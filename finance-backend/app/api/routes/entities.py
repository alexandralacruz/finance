"""Entities CRUD routes."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.models.orm import Entity, EntityType

router = APIRouter(tags=["Entities"])


class EntityCreate(BaseModel):
    name: str
    type: EntityType = EntityType.bank


class EntityUpdate(BaseModel):
    name: str | None = None
    type: EntityType | None = None
    active: bool | None = None


@router.get("/entities")
def list_entities(db: Session = Depends(get_db)):
    """List all entities."""
    entities = db.query(Entity).order_by(Entity.name).all()
    # Include accounts summary for each entity
    result = []
    for e in entities:
        accounts = [
            {
                "id": a.id,
                "account_type": a.account_type.value if a.account_type else None,
                "currency": a.currency,
            }
            for a in e.accounts
        ]
        result.append({
            "id": e.id,
            "name": e.name,
            "type": e.type.value if e.type else None,
            "active": e.active,
            "accounts": accounts,
        })
    return result


@router.post("/entities")
def create_entity(data: EntityCreate, db: Session = Depends(get_db)):
    """Create a new financial entity."""
    existing = db.query(Entity).filter(Entity.name == data.name).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Entity '{data.name}' already exists")

    entity = Entity(name=data.name, type=data.type)
    db.add(entity)
    db.commit()
    db.refresh(entity)
    return {
        "id": entity.id,
        "name": entity.name,
        "type": entity.type.value if entity.type else None,
    }


@router.put("/entities/{entity_id}")
def update_entity(entity_id: int, data: EntityUpdate, db: Session = Depends(get_db)):
    """Update an entity."""
    entity = db.query(Entity).filter(Entity.id == entity_id).first()
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")

    if data.name is not None:
        entity.name = data.name
    if data.type is not None:
        entity.type = data.type
    if data.active is not None:
        entity.active = data.active

    db.commit()
    return {"ok": True}


@router.put("/entities/{entity_id}/set-primary-income")
def set_primary_income(entity_id: int, db: Session = Depends(get_db)):
    """Set this entity as the primary income account. Unsets others."""
    entity = db.query(Entity).filter(Entity.id == entity_id).first()
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")

    # Unset all others
    db.query(Entity).filter(Entity.id != entity_id).update(
        {Entity.is_primary_income: False}
    )
    entity.is_primary_income = True
    db.commit()
    return {"ok": True, "primary_entity": entity.name}


@router.delete("/entities/{entity_id}")
def delete_entity(entity_id: int, db: Session = Depends(get_db)):
    """Soft-delete an entity (set active=False)."""
    entity = db.query(Entity).filter(Entity.id == entity_id).first()
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    entity.active = False
    db.commit()
    return {"ok": True}
