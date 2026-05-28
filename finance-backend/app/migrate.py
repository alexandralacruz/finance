"""CLI migration script: process existing dataset files into SQLite."""
import sys
from pathlib import Path

# Ensure the app package is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import logging
from datetime import datetime

from app.database import SessionLocal, init_db
from app.models.orm import Entity, Account, Transaction, EntityType, AccountType, TransactionType
from app import extract, config
from app import extract as extract_module

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("migrate")


def get_or_create_entity(db, name: str, entity_type: EntityType, currency: str) -> tuple[Entity, Account]:
    """Get or create entity and its default account."""
    entity = db.query(Entity).filter(Entity.name == name).first()
    if not entity:
        entity = Entity(name=name, type=entity_type)
        db.add(entity)
        db.flush()
        logger.info(f"  + Created entity: {name} ({entity_type.value})")

    # Ensure default account exists
    account = db.query(Account).filter(Account.entity_id == entity.id).first()
    if not account:
        # Map entity type to default account type
        type_map = {
            EntityType.bank: AccountType.checking,
            EntityType.investment: AccountType.investment_fund,
            EntityType.crypto: AccountType.spot,
            EntityType.payment_processor: AccountType.checking,
            EntityType.pension_fund: AccountType.pension,
            EntityType.other: AccountType.other,
        }
        atype = type_map.get(entity_type, AccountType.checking)
        account = Account(entity_id=entity.id, account_type=atype, currency=currency)
        db.add(account)
        db.flush()
        logger.info(f"  + Created account: {name} ({atype.value}, {currency})")

    return entity, account


def detect_type(amount: float, description: str) -> TransactionType:
    """Heuristic to classify a transaction type."""
    desc_lower = description.lower() if description else ""

    if amount > 0:
        if any(kw in desc_lower for kw in ["freelance", "pago proyecto", "servicio"]):
            return TransactionType.freelance
        if any(kw in desc_lower for kw in ["deposit", "depósito", "consignación", "transferencia recibida"]):
            return TransactionType.deposit
        if any(kw in desc_lower for kw in ["rendimiento", "dividendo", "interest", "interés"]):
            return TransactionType.return_
        if any(kw in desc_lower for kw in ["transfer", "traspaso"]):
            return TransactionType.transfer_in
        return TransactionType.income
    else:
        if any(kw in desc_lower for kw in ["comisión", "fee", "comision", "cuota de manejo"]):
            return TransactionType.fee
        if any(kw in desc_lower for kw in ["transfer", "traspaso", "envío"]):
            return TransactionType.transfer_out
        if any(kw in desc_lower for kw in ["inversión", "compra acción", "buy", "trade"]):
            return TransactionType.investment
        return TransactionType.expense


def detect_category(description: str) -> str | None:
    """Match description against known categories."""
    if not description:
        return None

    try:
        categories = extract.read_categories_class()
    except Exception:
        return None

    from app.processing import clasificar_transaccion
    cat = clasificar_transaccion(description, categories)
    return cat if cat != "otros" else None


def migrate_entity(db, entity: Entity, account: Account, base_folder: str, year: int, extract_fn, **kwargs):
    """Extract and insert transactions for one entity in one year."""
    try:
        df = extract_fn(base_folder, year, **kwargs)
    except FileNotFoundError:
        logger.warning(f"  No data found for {entity.name} in {year}")
        return 0, 0, 0
    except Exception as e:
        logger.error(f"  Error extracting {entity.name} {year}: {e}")
        return 0, 0, 1

    if df is None or df.empty:
        return 0, 0, 0

    new_count = 0
    dup_count = 0
    err_count = 0

    for _, row in df.iterrows():
        try:
            date_val = row.get("FECHA")
            if hasattr(date_val, "to_pydatetime"):
                date_val = date_val.to_pydatetime().date()
            elif hasattr(date_val, "date"):
                date_val = date_val.date()
            elif isinstance(date_val, str):
                date_val = datetime.strptime(date_val[:10], "%Y-%m-%d").date()

            amount = float(row.get("CREDIT/DEBIT", 0) or 0)
            description = str(row.get("DESCRIPCION", ""))
            balance = row.get("SALDO")
            balance = float(balance) if balance is not None and str(balance).lower() != "nan" else None

            # Check duplicate
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

            tx_type = detect_type(amount, description)
            category = detect_category(description)

            tx = Transaction(
                account_id=account.id,
                date=date_val,
                description=description,
                amount=amount,
                balance=balance,
                currency=account.currency,
                type=tx_type,
                category=category,
                source_file=f"migrate:{year}",
            )
            db.add(tx)
            new_count += 1

        except Exception as e:
            logger.debug(f"  Row error: {e}")
            err_count += 1

    db.flush()
    logger.info(f"  {entity.name} {year}: {new_count} new, {dup_count} dup, {err_count} err")
    return new_count, dup_count, err_count


def migrate_all():
    """Main migration entry point."""
    db = SessionLocal()
    try:
        init_db()

        base_folder = config.DATASET_ROOT_PATH
        logger.info(f"Dataset root: {base_folder}")

        # ── Pre-seed entities ──
        entities_config = [
            ("BC", EntityType.bank, "COP"),
            ("AMERANT", EntityType.bank, "USD"),
            ("PAYONEER", EntityType.payment_processor, "USD"),
        ]

        entities = {}
        accounts = {}
        for name, etype, currency in entities_config:
            entity, account = get_or_create_entity(db, name, etype, currency)
            entities[name] = entity
            accounts[name] = account

        db.commit()

        # ── Available years ──
        current_year = datetime.now().year
        years = [current_year, current_year - 1, current_year - 2, current_year - 3]

        totals = {"new": 0, "dup": 0, "err": 0}

        for year in years:
            base_year = Path(base_folder) / str(year)
            if not base_year.exists():
                logger.info(f"Skipping year {year} (no folder)")
                continue

            logger.info(f"--- Year {year} ---")
            subfolders = [f.name for f in base_year.iterdir() if f.is_dir()]

            # BC
            if "BC" in subfolders:
                n, d, e = migrate_entity(
                    db, entities["BC"], accounts["BC"], base_folder, year,
                    extract_module.extractExtractosFromFolderYearBC,
                )
                for k, v in zip(["new", "dup", "err"], [n, d, e]):
                    totals[k] += v

            # Amerant
            if "Amerant" in subfolders:
                n, d, e = migrate_entity(
                    db, entities["AMERANT"], accounts["AMERANT"], base_folder, year,
                    extract_module.extract_amerant,
                )
                for k, v in zip(["new", "dup", "err"], [n, d, e]):
                    totals[k] += v

            # Payoneer
            if "Payoneer" in subfolders:
                n, d, e = migrate_entity(
                    db, entities["PAYONEER"], accounts["PAYONEER"], base_folder, year,
                    extract_module.extract_payoneer,
                )
                for k, v in zip(["new", "dup", "err"], [n, d, e]):
                    totals[k] += v

        db.commit()
        logger.info("=" * 50)
        logger.info(f"Migration complete: {totals['new']} new, {totals['dup']} dup, {totals['err']} errors")

        # Show summary
        total_tx = db.query(Transaction).count()
        total_entities = db.query(Entity).count()
        logger.info(f"Database now has {total_tx} transactions across {total_entities} entities")

    except Exception as e:
        db.rollback()
        logger.exception(f"Migration failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    migrate_all()
