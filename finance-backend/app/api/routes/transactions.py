"""Manual transaction entry routes."""
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.models.orm import Transaction, Account, TransactionType

router = APIRouter(tags=["Transactions"])


class TransactionCreate(BaseModel):
    account_id: int
    date: date
    description: str
    amount: float | None = None       # required for non-balance types
    balance: float | None = None       # required for balance type (new saldo)
    type: TransactionType = TransactionType.freelance
    category: str | None = None
    related_entity: str | None = None


class TransactionUpdate(BaseModel):
    description: str | None = None
    category: str | None = None
    type: TransactionType | None = None


@router.post("/transactions")
def create_transaction(data: TransactionCreate, db: Session = Depends(get_db)):
    """Manually add a transaction or balance snapshot."""
    account = db.query(Account).filter(Account.id == data.account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail=f"Account {data.account_id} not found")

    # ── Balance type: user provides the new total balance ──
    if data.type == TransactionType.balance:
        if data.balance is None:
            raise HTTPException(status_code=400, detail="balance field is required for type='balance'")

        # Get previous balance for this account
        last_tx = (
            db.query(Transaction)
            .filter(
                Transaction.account_id == account.id,
                Transaction.balance.isnot(None),
            )
            .order_by(Transaction.date.desc(), Transaction.id.desc())
            .first()
        )
        prev_balance = last_tx.balance if last_tx else 0
        computed_amount = round(data.balance - prev_balance, 2)

        tx = Transaction(
            account_id=account.id,
            date=data.date,
            description=data.description,
            amount=computed_amount,
            balance=data.balance,
            currency=account.currency,
            type=data.type,
            category=data.category,
            related_entity=data.related_entity,
            source_file="manual",
        )
    else:
        # ── Regular transaction (deposit, withdrawal, freelance, etc.) ──
        if data.amount is None:
            raise HTTPException(
                status_code=400,
                detail="amount field is required for non-balance transaction types",
            )

        # Auto-compute running balance if not provided
        balance = data.balance
        if balance is None:
            last_tx = (
                db.query(Transaction)
                .filter(
                    Transaction.account_id == account.id,
                    Transaction.balance.isnot(None),
                )
                .order_by(Transaction.date.desc(), Transaction.id.desc())
                .first()
            )
            prev_balance = last_tx.balance if last_tx else 0
            balance = round(prev_balance + data.amount, 2)

        tx = Transaction(
            account_id=account.id,
            date=data.date,
            description=data.description,
            amount=data.amount,
            balance=balance,
            currency=account.currency,
            type=data.type,
            category=data.category,
            related_entity=data.related_entity,
            source_file="manual",
        )

    db.add(tx)
    db.commit()
    db.refresh(tx)
    return {
        "id": tx.id,
        "account_id": tx.account_id,
        "entity_name": account.entity.name if account.entity else None,
        "date": str(tx.date),
        "description": tx.description,
        "amount": tx.amount,
        "balance": tx.balance,
        "type": tx.type.value if tx.type else None,
    }


@router.put("/transactions/{tx_id}")
def update_transaction(tx_id: int, data: TransactionUpdate, db: Session = Depends(get_db)):
    """Update a transaction's metadata (category, type, description)."""
    tx = db.query(Transaction).filter(Transaction.id == tx_id).first()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")

    if data.description is not None:
        tx.description = data.description
    if data.category is not None:
        tx.category = data.category
    if data.type is not None:
        tx.type = data.type

    db.commit()
    return {"ok": True}
