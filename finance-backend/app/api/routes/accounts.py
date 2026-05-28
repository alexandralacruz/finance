"""Accounts CRUD routes – manage sub-accounts within entities."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.models.orm import Account, Entity, AccountType

router = APIRouter(tags=["Accounts"])


class AccountCreate(BaseModel):
    entity_id: int
    account_type: AccountType = AccountType.checking
    currency: str = "COP"


class AccountUpdate(BaseModel):
    account_type: AccountType | None = None
    currency: str | None = None
    active: bool | None = None


@router.get("/entities/{entity_id}/accounts")
def list_accounts(entity_id: int, db: Session = Depends(get_db)):
    """List all accounts for a given entity."""
    entity = db.query(Entity).filter(Entity.id == entity_id).first()
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")

    accounts = (
        db.query(Account)
        .filter(Account.entity_id == entity_id)
        .order_by(Account.account_type, Account.id)
        .all()
    )
    return [
        {
            "id": a.id,
            "entity_id": a.entity_id,
            "entity_name": entity.name,
            "account_type": a.account_type.value if a.account_type else None,
            "currency": a.currency,
            "active": a.active,
        }
        for a in accounts
    ]


@router.post("/accounts")
def create_account(data: AccountCreate, db: Session = Depends(get_db)):
    """Create a new account under an entity."""
    entity = db.query(Entity).filter(Entity.id == data.entity_id).first()
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")

    # Check for duplicate: same entity + same account_type + same currency
    existing = (
        db.query(Account)
        .filter(
            Account.entity_id == data.entity_id,
            Account.account_type == data.account_type,
            Account.currency == data.currency,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Account '{data.account_type.value}' with currency '{data.currency}' already exists for this entity",
        )

    account = Account(
        entity_id=data.entity_id,
        account_type=data.account_type,
        currency=data.currency,
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return {
        "id": account.id,
        "entity_id": account.entity_id,
        "entity_name": entity.name,
        "account_type": account.account_type.value if account.account_type else None,
        "currency": account.currency,
    }


@router.put("/accounts/{account_id}")
def update_account(account_id: int, data: AccountUpdate, db: Session = Depends(get_db)):
    """Update an account's type, currency, or active status."""
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    if data.account_type is not None:
        account.account_type = data.account_type
    if data.currency is not None:
        account.currency = data.currency
    if data.active is not None:
        account.active = data.active

    db.commit()
    return {"ok": True}


@router.delete("/accounts/{account_id}")
def delete_account(account_id: int, db: Session = Depends(get_db)):
    """Soft-delete an account (set active=False)."""
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    account.active = False
    db.commit()
    return {"ok": True}
