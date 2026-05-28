"""Balances route – reads from SQLite via accounts."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.orm import Account, Transaction

router = APIRouter(tags=["Balances"])


@router.get("/balances")
def get_balances(db: Session = Depends(get_db)):
    """Get current balance for each active account, grouped by entity."""
    accounts = (
        db.query(Account)
        .filter(Account.active == True)
        .order_by(Account.entity_id, Account.account_type)
        .all()
    )

    result = []
    for account in accounts:
        # Get most recent transaction with a balance for this account
        last_tx = (
            db.query(Transaction)
            .filter(
                Transaction.account_id == account.id,
                Transaction.balance.isnot(None),
            )
            .order_by(Transaction.date.desc())
            .first()
        )

        balance = last_tx.balance if last_tx else 0
        entity_name = account.entity.name if account.entity else "Unknown"

        result.append({
            "account_id": account.id,
            "entity": entity_name,
            "account_type": account.account_type.value if account.account_type else "checking",
            "currency": account.currency,
            "balance": round(balance, 2),
            "active": account.active,
        })

    return result
