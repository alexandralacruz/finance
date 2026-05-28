"""Finance summary routes – now querying SQLite instead of file extraction."""
import logging
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, extract, and_
from typing import Literal

from app.database import get_db
from app.models.orm import Transaction, Entity, Account
from app.api.routes.exchange import get_exchange_rate as fetch_rate

router = APIRouter(tags=["Finance"])
logger = logging.getLogger("finance")
logger.setLevel(logging.INFO)


def _get_usd_to_cop() -> float:
    """Helper: get USD→COP rate (COP per 1 USD)."""
    try:
        data = fetch_rate(target="USD")
        # exchangerate API from COP gives COP→USD, we need USD→COP
        rate = data.get("rate", 0.00025)
        return 1 / rate if rate > 0 else 4000
    except Exception:
        return 4000


def _convert_amount(amount: float, currency: str, target: str, rate: float) -> float:
    """Convert amount between COP and USD."""
    if currency == target:
        return amount
    if target == "COP":
        return amount * rate
    else:
        return amount / rate


@router.get("/years")
def get_available_years(db: Session = Depends(get_db)):
    """Return years that have transactions."""
    current_year = datetime.now().year
    years_in_db = (
        db.query(func.distinct(extract("year", Transaction.date)))
        .order_by(extract("year", Transaction.date).desc())
        .all()
    )
    years_in_db = [int(y[0]) for y in years_in_db if y[0]]

    # Always include current year
    if current_year not in years_in_db:
        years_in_db.append(current_year)

    return {"years": sorted(years_in_db, reverse=True)}


@router.get("/summary/{year}")
def get_summary(
    year: int,
    currency: Literal["COP", "USD"] = "COP",
    db: Session = Depends(get_db),
):
    """Financial summary for a given year."""
    try:
        usd_to_cop = _get_usd_to_cop()
    except Exception:
        usd_to_cop = 4000

    # Income
    income = (
        db.query(func.sum(Transaction.amount))
        .filter(
            extract("year", Transaction.date) == year,
            Transaction.amount > 0,
        )
        .scalar() or 0
    )

    # Expenses (stored as negative)
    expenses_raw = (
        db.query(func.sum(Transaction.amount))
        .filter(
            extract("year", Transaction.date) == year,
            Transaction.amount < 0,
        )
        .scalar() or 0
    )
    expenses = abs(expenses_raw)

    # Convert to target currency
    # For simplicity, all COP amounts stay COP, USD amounts are converted
    cop_income = (
        db.query(func.sum(Transaction.amount))
        .filter(
            extract("year", Transaction.date) == year,
            Transaction.amount > 0,
            Transaction.currency == "COP",
        )
        .scalar() or 0
    )
    usd_income = (
        db.query(func.sum(Transaction.amount))
        .filter(
            extract("year", Transaction.date) == year,
            Transaction.amount > 0,
            Transaction.currency == "USD",
        )
        .scalar() or 0
    )
    cop_expenses = (
        db.query(func.abs(func.sum(Transaction.amount)))
        .filter(
            extract("year", Transaction.date) == year,
            Transaction.amount < 0,
            Transaction.currency == "COP",
        )
        .scalar() or 0
    )
    usd_expenses = (
        db.query(func.abs(func.sum(Transaction.amount)))
        .filter(
            extract("year", Transaction.date) == year,
            Transaction.amount < 0,
            Transaction.currency == "USD",
        )
        .scalar() or 0
    )

    if currency == "COP":
        total_income = cop_income + (usd_income * usd_to_cop)
        total_expenses = cop_expenses + (usd_expenses * usd_to_cop)
    else:
        total_income = usd_income + (cop_income / usd_to_cop)
        total_expenses = usd_expenses + (cop_expenses / usd_to_cop)

    # Entity count (via accounts)
    entity_count = (
        db.query(func.count(func.distinct(Account.entity_id)))
        .join(Transaction, Transaction.account_id == Account.id)
        .filter(extract("year", Transaction.date) == year)
        .scalar() or 0
    )

    # Balance by entity (latest balance per entity, summed across accounts)
    entity_balances = _get_entity_balances(db, year, currency, usd_to_cop)
    total_balance = sum(e["BALANCE_FINAL"] for e in entity_balances)

    return {
        "totalBalance": round(total_balance, 2),
        "entities": entity_count,
        "income": round(total_income, 2),
        "expenses": round(total_expenses, 2),
        "currency": currency,
        "entityBalances": entity_balances,
    }


@router.get("/byEntity/{year}")
def get_data_by_entity(
    year: int,
    currency: Literal["COP", "USD"] = "USD",
    db: Session = Depends(get_db),
):
    """Balance breakdown by entity for a year."""
    try:
        usd_to_cop = _get_usd_to_cop()
    except Exception:
        usd_to_cop = 4000

    entities = _get_entity_balances(db, year, currency, usd_to_cop)
    return {"currency": currency, "entities": entities}


@router.get("/byMonth/{year}")
def get_data_by_month(
    year: int,
    currency: Literal["COP", "USD"] = "USD",
    db: Session = Depends(get_db),
):
    """Monthly balance evolution for a year."""
    try:
        usd_to_cop = _get_usd_to_cop()
    except Exception:
        usd_to_cop = 4000

    months_data = []

    for month in range(1, 13):
        # Per-currency aggregation for correct conversion
        cop_income = (
            db.query(func.sum(Transaction.amount))
            .filter(
                extract("year", Transaction.date) == year,
                extract("month", Transaction.date) == month,
                Transaction.amount > 0,
                Transaction.currency == "COP",
            )
            .scalar() or 0
        )
        usd_income = (
            db.query(func.sum(Transaction.amount))
            .filter(
                extract("year", Transaction.date) == year,
                extract("month", Transaction.date) == month,
                Transaction.amount > 0,
                Transaction.currency == "USD",
            )
            .scalar() or 0
        )
        cop_expenses_raw = (
            db.query(func.sum(Transaction.amount))
            .filter(
                extract("year", Transaction.date) == year,
                extract("month", Transaction.date) == month,
                Transaction.amount < 0,
                Transaction.currency == "COP",
            )
            .scalar() or 0
        )
        usd_expenses_raw = (
            db.query(func.sum(Transaction.amount))
            .filter(
                extract("year", Transaction.date) == year,
                extract("month", Transaction.date) == month,
                Transaction.amount < 0,
                Transaction.currency == "USD",
            )
            .scalar() or 0
        )

        if currency == "COP":
            month_income = cop_income + (usd_income * usd_to_cop)
            month_expenses = abs(cop_expenses_raw) + (abs(usd_expenses_raw) * usd_to_cop)
        else:
            month_income = usd_income + (cop_income / usd_to_cop)
            month_expenses = abs(usd_expenses_raw) + (abs(cop_expenses_raw) / usd_to_cop)

        # Get last balance for each account this month
        subq = (
            db.query(
                Transaction.account_id,
                func.max(Transaction.date).label("max_date")
            )
            .filter(
                extract("year", Transaction.date) == year,
                extract("month", Transaction.date) == month,
            )
            .group_by(Transaction.account_id)
            .subquery()
        )

        last_balances = (
            db.query(Transaction)
            .join(subq, (Transaction.account_id == subq.c.account_id) &
                         (Transaction.date == subq.c.max_date))
            .all()
        )

        total_balance = 0
        for tx in last_balances:
            if tx.balance is not None:
                b = tx.balance
                if tx.currency == "USD" and currency == "COP":
                    b *= usd_to_cop
                elif tx.currency == "COP" and currency == "USD":
                    b /= usd_to_cop
                total_balance += b

        months_data.append({
            "MES": f"{year}-{month:02d}",
            "total_balance": round(total_balance, 2),
            "income": round(month_income, 2),
            "expenses": round(month_expenses, 2),
        })

    return months_data


@router.get("/entity/{entity_name}/range")
def get_entity_range(
    entity_name: str,
    from_date: date = Query(..., alias="from"),
    to_date: date = Query(..., alias="to"),
    currency: Literal["COP", "USD"] = "USD",
    db: Session = Depends(get_db),
):
    """Transactions and summary for an entity within a date range."""
    entity = db.query(Entity).filter(Entity.name == entity_name).first()
    if not entity:
        raise HTTPException(status_code=404, detail=f"Entity '{entity_name}' not found")

    try:
        usd_to_cop = _get_usd_to_cop()
    except Exception:
        usd_to_cop = 4000

    # Get account IDs for this entity
    account_ids = [a.id for a in db.query(Account.id).filter(Account.entity_id == entity.id).all()]
    if not account_ids:
        raise HTTPException(status_code=404, detail=f"Entity '{entity_name}' has no accounts")

    # Balance at start of range: last transaction with balance on or before from_date
    balance_start_tx = (
        db.query(Transaction)
        .filter(
            Transaction.account_id.in_(account_ids),
            Transaction.date <= from_date,
            Transaction.balance.isnot(None),
        )
        .order_by(Transaction.date.desc(), Transaction.id.desc())
        .first()
    )
    balance_start = balance_start_tx.balance if balance_start_tx else 0

    # Balance at end of range
    balance_end_tx = (
        db.query(Transaction)
        .filter(
            Transaction.account_id.in_(account_ids),
            Transaction.date <= to_date,
            Transaction.balance.isnot(None),
        )
        .order_by(Transaction.date.desc(), Transaction.id.desc())
        .first()
    )
    balance_end = balance_end_tx.balance if balance_end_tx else 0

    # Transactions within the range
    txs = (
        db.query(Transaction)
        .filter(
            Transaction.account_id.in_(account_ids),
            Transaction.date >= from_date,
            Transaction.date <= to_date,
        )
        .order_by(Transaction.date.desc(), Transaction.id.desc())
        .all()
    )

    # Aggregate - use tx.currency (from transaction) for conversion
    income = 0
    expenses = 0
    tx_list = []

    for tx in txs:
        amt = tx.amount
        display_amt = amt
        display_balance = tx.balance
        tx_currency = tx.currency

        if tx_currency == "USD" and currency == "COP":
            amt *= usd_to_cop
            display_amt = amt
            display_balance = tx.balance * usd_to_cop if tx.balance is not None else None
        elif tx_currency == "COP" and currency == "USD":
            amt /= usd_to_cop
            display_amt = amt
            display_balance = tx.balance / usd_to_cop if tx.balance is not None else None

        if amt > 0:
            income += amt
        else:
            expenses += abs(amt)

        tx_list.append({
            "id": tx.id,
            "date": str(tx.date),
            "description": tx.description,
            "amount": round(display_amt, 2),
            "balance": round(display_balance, 2) if display_balance is not None else None,
            "type": tx.type.value if tx.type else None,
            "category": tx.category,
        })

    # Convert balance_start / balance_end to display currency (using first account's currency as reference)
    ref_account = db.query(Account).filter(Account.id == account_ids[0]).first()
    ref_currency = ref_account.currency if ref_account else "COP"
    if ref_currency == "USD" and currency == "COP":
        balance_start *= usd_to_cop
        balance_end *= usd_to_cop
    elif ref_currency == "COP" and currency == "USD":
        balance_start /= usd_to_cop
        balance_end /= usd_to_cop

    return {
        "entity": entity.name,
        "type": entity.type.value if entity.type else None,
        "native_currency": ref_currency,
        "display_currency": currency,
        "from": str(from_date),
        "to": str(to_date),
        "balance_start": round(balance_start, 2),
        "balance_end": round(balance_end, 2),
        "income": round(income, 2),
        "expenses": round(expenses, 2),
        "net": round(income - expenses, 2),
        "transaction_count": len(txs),
        "transactions": tx_list,
    }


@router.get("/entity/{entity_name}/{year}")
def get_entity_detail(
    entity_name: str,
    year: int,
    currency: Literal["COP", "USD"] = "USD",
    db: Session = Depends(get_db),
):
    """Detailed transactions and summary for a specific entity in a year."""
    entity = db.query(Entity).filter(Entity.name == entity_name).first()
    if not entity:
        raise HTTPException(status_code=404, detail=f"Entity '{entity_name}' not found")

    try:
        usd_to_cop = _get_usd_to_cop()
    except Exception:
        usd_to_cop = 4000

    # Get account IDs for this entity
    account_ids = [a.id for a in db.query(Account.id).filter(Account.entity_id == entity.id).all()]
    if not account_ids:
        raise HTTPException(status_code=404, detail=f"Entity '{entity_name}' has no accounts")

    txs = (
        db.query(Transaction)
        .filter(
            Transaction.account_id.in_(account_ids),
            extract("year", Transaction.date) == year,
        )
        .order_by(Transaction.date.desc())
        .all()
    )

    # Monthly aggregation
    monthly = {}
    for tx in txs:
        month_key = tx.date.strftime("%Y-%m")
        if month_key not in monthly:
            monthly[month_key] = {"income": 0, "expenses": 0, "count": 0}

        amt = tx.amount
        tx_currency = tx.currency
        if tx_currency == "USD" and currency == "COP":
            amt *= usd_to_cop
        elif tx_currency == "COP" and currency == "USD":
            amt /= usd_to_cop

        if amt > 0:
            monthly[month_key]["income"] += amt
        else:
            monthly[month_key]["expenses"] += abs(amt)
        monthly[month_key]["count"] += 1

    latest_balance = None
    if txs and txs[0].balance is not None:
        latest_balance = txs[0].balance
        tx_currency = txs[0].currency
        if tx_currency == "USD" and currency == "COP":
            latest_balance *= usd_to_cop
        elif tx_currency == "COP" and currency == "USD":
            latest_balance /= usd_to_cop

    return {
        "entity": entity.name,
        "type": entity.type.value if entity.type else None,
        "native_currency": tx_currency if txs else "COP",
        "currency": currency,
        "latest_balance": round(latest_balance, 2) if latest_balance else None,
        "transaction_count": len(txs),
        "monthly_summary": {
            k: {
                "income": round(v["income"], 2),
                "expenses": round(v["expenses"], 2),
                "net": round(v["income"] - v["expenses"], 2),
                "count": v["count"],
            }
            for k, v in monthly.items()
        },
    }


def _get_entity_balances(db: Session, year: int, currency: str, rate: float) -> list:
    """Calculate balance per entity for a given year, summing across all accounts."""
    entities = db.query(Entity).filter(Entity.active == True).all()
    result = []

    for entity in entities:
        account_ids = [a.id for a in entity.accounts if a.active]
        if not account_ids:
            result.append({"ENTIDAD": entity.name, "BALANCE_FINAL": 0})
            continue

        # Get last transaction per account for the year
        total_balance = 0
        for aid in account_ids:
            last_tx = (
                db.query(Transaction)
                .filter(
                    Transaction.account_id == aid,
                    extract("year", Transaction.date) == year,
                    Transaction.balance.isnot(None),
                )
                .order_by(Transaction.date.desc())
                .first()
            )
            if last_tx and last_tx.balance is not None:
                balance = last_tx.balance
                tx_currency = last_tx.currency
                if tx_currency == "USD" and currency == "COP":
                    balance *= rate
                elif tx_currency == "COP" and currency == "USD":
                    balance /= rate
                total_balance += balance

        result.append({
            "ENTIDAD": entity.name,
            "BALANCE_FINAL": round(total_balance, 2),
        })

    return result
