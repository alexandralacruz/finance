"""Upload routes: process bank/investment statements and insert into DB."""
import shutil
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.orm import Entity, Account, Transaction, TransactionType
from app import extract as extract_module
from app import config

import pandas as pd

router = APIRouter(tags=["Upload"])


# Per-file parsers for known entity formats
def _parse_amerant_file(file_path: str) -> pd.DataFrame | None:
    """Parse a single Amerant XLS file."""
    try:
        df = pd.read_excel(file_path, skiprows=1)
        df = df.drop(df.index[-1])
        df = df.sort_values(by='Date').reset_index(drop=True)
        df['CREDIT/DEBIT'] = df.apply(
            lambda row: -row['Debit Amount'] if pd.notnull(row['Debit Amount']) else row['Credit Amount'],
            axis=1
        )
        df = df.drop(columns=['Debit Amount', 'Credit Amount'])
        df = df.rename(columns={'Description': 'DESCRIPCION', 'Date': 'FECHA', 'Running Balance': 'SALDO'})
        if 'Check Number' in df.columns:
            df = df.drop(columns=['Check Number'])
        df['FECHA'] = pd.to_datetime(df['FECHA'], errors='coerce')
        return df
    except Exception:
        return None


def _parse_payoneer_file(file_path: str) -> pd.DataFrame | None:
    """Parse a single Payoneer CSV file."""
    try:
        df = pd.read_csv(file_path)
        df['FECHA'] = pd.to_datetime(
            df['Transaction Date'] + ' ' + df['Transaction Time']
        )
        df['CREDIT/DEBIT'] = (
            df['Credit Amount'].fillna(0) - df['Debit Amount'].fillna(0)
        )
        df = df.rename(columns={
            'Description': 'DESCRIPCION',
            'Running Balance': 'SALDO',
            'Currency': 'MONEDA'
        })
        df = df[['FECHA', 'DESCRIPCION', 'CREDIT/DEBIT', 'SALDO', 'MONEDA']]
        return df
    except Exception:
        return None


def _parse_bc_file(file_path: str) -> pd.DataFrame | None:
    """Parse a single BC (Bancolombia) file."""
    try:
        ext = Path(file_path).suffix.lower()
        if ext == '.csv':
            df = pd.read_csv(file_path, sep='\t', encoding='ISO-8859-1', header=None)
        else:
            df = pd.read_excel(file_path, header=None)

        # Try the extracto format (multi-block with 'FECHA' headers)
        col0 = df[0].astype(str)
        if col0.str.contains("FECHA", na=False).any():
            # Try to extract year from file path (saved as dataset/{year}/BC/)
            year = None
            try:
                parts = Path(file_path).parts
                for p in parts:
                    if p.isdigit() and len(p) == 4:
                        year = int(p)
                        break
            except Exception:
                pass
            return extract_module.extract_from_extrato_file(file_path, year)
        # Try the periodo format
        elif col0.str.contains("Fecha", na=False).any():
            return extract_module.extract_from_period_xls(file_path)
        else:
            return pd.read_excel(file_path, header=None)
    except Exception:
        return None


def _save_and_parse(file: UploadFile, entity_name: str) -> pd.DataFrame | None:
    """Save file to dataset folder and parse it."""
    year = str(datetime.now().year)
    dest_dir = Path(config.DATASET_ROOT_PATH) / year / entity_name
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / file.filename

    with open(dest_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # Choose parser
    df = None
    if entity_name == "AMERANT":
        df = _parse_amerant_file(str(dest_path))
    elif entity_name == "PAYONEER":
        df = _parse_payoneer_file(str(dest_path))
    elif entity_name == "BC":
        df = _parse_bc_file(str(dest_path))

    # Fallback: try generic parser if entity-specific parser failed
    if df is None:
        df = _parse_generic_file(str(dest_path))

    return df


def _parse_generic_file(file_path: str) -> pd.DataFrame | None:
    """Generic CSV/Excel parser with auto-detection of columns."""
    try:
        ext = Path(file_path).suffix.lower()
        if ext == '.csv':
            df = pd.read_csv(file_path)
        elif ext in ('.xls', '.xlsx'):
            df = pd.read_excel(file_path)
        else:
            return None

        col_map = {}
        for col in df.columns:
            cl = str(col).lower()
            if 'fecha' in cl or 'date' in cl:
                col_map['FECHA'] = col
            elif any(k in cl for k in ['descrip', 'concepto', 'description', 'narrativa']):
                col_map['DESCRIPCION'] = col
            elif any(k in cl for k in ['valor', 'monto', 'amount', 'credito', 'crédito', 'debit']):
                col_map['CREDIT/DEBIT'] = col
            elif any(k in cl for k in ['saldo', 'balance']):
                col_map['SALDO'] = col

        if 'FECHA' not in col_map or 'CREDIT/DEBIT' not in col_map:
            return None

        df = df.rename(columns={v: k for k, v in col_map.items()})
        df['FECHA'] = pd.to_datetime(df['FECHA'], errors='coerce')
        df['CREDIT/DEBIT'] = pd.to_numeric(df['CREDIT/DEBIT'], errors='coerce')

        needed = ['FECHA', 'DESCRIPCION', 'CREDIT/DEBIT']
        if 'SALDO' in df.columns:
            needed.append('SALDO')
        return df[[c for c in needed if c in df.columns]].dropna(subset=['FECHA', 'CREDIT/DEBIT'])
    except Exception:
        return None


def _get_or_create_default_account(db: Session, entity: Entity) -> Account | None:
    """Get the first active account for an entity, or create a default checking one."""
    account = db.query(Account).filter(Account.entity_id == entity.id, Account.active == True).first()
    if account:
        return account
    # Create a default checking account using the entity's legacy currency if present
    currency = getattr(entity, 'currency', 'COP')
    from app.models.orm import AccountType
    account = Account(entity_id=entity.id, account_type=AccountType.checking, currency=currency)
    db.add(account)
    db.flush()
    return account


def _insert_transactions(
    db: Session,
    entity: Entity,
    df: pd.DataFrame,
    source_file: str,
) -> dict:
    """Insert rows from DataFrame into transactions table with dedup."""
    new_count = 0
    dup_count = 0
    err_count = 0

    if df is None or df.empty:
        return {"new": 0, "duplicates": 0, "errors": 0}

    df = df.sort_values('FECHA') if 'FECHA' in df.columns else df

    account = _get_or_create_default_account(db, entity)
    if not account:
        return {"new": 0, "duplicates": 0, "errors": 1}

    # Preload last known balance so we can compute running balance if SALDO is missing
    last_known = (
        db.query(Transaction)
        .filter(
            Transaction.account_id == account.id,
            Transaction.balance.isnot(None),
        )
        .order_by(Transaction.date.desc(), Transaction.id.desc())
        .first()
    )
    running_balance = last_known.balance if last_known else 0

    for _, row in df.iterrows():
        try:
            date_val = row.get('FECHA')
            if pd.isna(date_val):
                err_count += 1
                continue
            if hasattr(date_val, 'date'):
                date_val = date_val.date()
            elif isinstance(date_val, str):
                date_val = datetime.strptime(date_val[:10], '%Y-%m-%d').date()

            amount = float(row.get('CREDIT/DEBIT', 0) or 0)
            description = str(row.get('DESCRIPCION', ''))
            balance = row.get('SALDO')
            balance = float(balance) if pd.notna(balance) else None

            # Auto-compute running balance if not provided in file
            if balance is None:
                running_balance = round(running_balance + amount, 2)
                balance = running_balance
            else:
                running_balance = balance

            # Dedup
            existing = (
                db.query(Transaction)
                .filter(
                    Transaction.account_id == account.id,
                    Transaction.date == date_val,
                    Transaction.description == description,
                    Transaction.amount == amount,
                )
                .first()
            )
            if existing:
                dup_count += 1
                continue

            tx = Transaction(
                account_id=account.id,
                date=date_val,
                description=description,
                amount=amount,
                balance=balance,
                currency=account.currency,
                type=TransactionType.income if amount > 0 else TransactionType.expense,
                source_file=source_file,
            )
            db.add(tx)
            new_count += 1

        except Exception:
            err_count += 1

    db.commit()
    return {"new": new_count, "duplicates": dup_count, "errors": err_count}


@router.post("/upload/{entity_name}")
def upload_statement(
    entity_name: str,
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
):
    """Upload bank/investment statements for an entity."""
    entity = db.query(Entity).filter(Entity.name == entity_name).first()
    if not entity:
        raise HTTPException(status_code=404, detail=f"Entity '{entity_name}' not found")

    total = {"new": 0, "duplicates": 0, "errors": 0}
    file_results = []

    for file in files:
        try:
            df = _save_and_parse(file, entity_name)

            if df is None or df.empty:
                file_results.append({
                    "file": file.filename,
                    "error": "Could not parse file – unknown format",
                })
                total["errors"] += 1
                continue

            res = _insert_transactions(db, entity, df, f"upload:{file.filename}")
            file_results.append({"file": file.filename, **res})
            for k in ["new", "duplicates", "errors"]:
                total[k] += res[k]

        except Exception as e:
            file_results.append({"file": file.filename, "error": str(e)})
            total["errors"] += 1

    return {"entity": entity_name, "total": total, "files": file_results}
