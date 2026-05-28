"""Retirement plan routes: projections and savings tracking."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from pydantic import BaseModel
from datetime import date, datetime

from app.database import get_db
from app.models.orm import RetirementPlan, Transaction, Entity, Account

router = APIRouter(tags=["Retirement"])


class RetirementPlanCreate(BaseModel):
    name: str = "Plan de retiro"
    target_amount_cop: float | None = None
    target_amount_usd: float | None = None
    target_years: int = 20
    annual_return_pct: float = 5.0
    current_savings_cop: float = 0.0
    current_savings_usd: float = 0.0


@router.get("/retirement/plan")
def get_retirement_plan(db: Session = Depends(get_db)):
    """Get the active retirement plan."""
    plan = db.query(RetirementPlan).order_by(RetirementPlan.id.desc()).first()
    if not plan:
        # Create default
        plan = RetirementPlan()
        db.add(plan)
        db.commit()
        db.refresh(plan)

    # Calculate real monthly savings capacity from last 12 months
    twelve_months_ago = date.today().replace(day=1)
    for _ in range(12):
        if twelve_months_ago.month == 1:
            twelve_months_ago = twelve_months_ago.replace(year=twelve_months_ago.year - 1, month=12)
        else:
            twelve_months_ago = twelve_months_ago.replace(month=twelve_months_ago.month - 1)

    # Per-entity savings breakdown
    entities = db.query(Entity).filter(Entity.active == True).all()
    entity_savings = []
    grand_total_income = 0
    grand_total_expenses = 0

    for entity in entities:
        account_ids = [a.id for a in entity.accounts if a.active]
        if not account_ids:
            continue

        entity_income = (
            db.query(func.sum(Transaction.amount))
            .filter(
                Transaction.account_id.in_(account_ids),
                Transaction.date >= twelve_months_ago,
                Transaction.amount > 0,
            )
            .scalar() or 0
        )
        entity_expenses = (
            db.query(func.abs(func.sum(Transaction.amount)))
            .filter(
                Transaction.account_id.in_(account_ids),
                Transaction.date >= twelve_months_ago,
                Transaction.amount < 0,
            )
            .scalar() or 0
        )

        grand_total_income += entity_income
        grand_total_expenses += entity_expenses

        # Get the currency from first account
        currency = entity.accounts[0].currency if entity.accounts else "COP"
        entity_savings.append({
            "entity_name": entity.name,
            "currency": currency,
            "monthly_income": round(entity_income / 12, 2),
            "monthly_expenses": round(entity_expenses / 12, 2),
            "monthly_savings": round((entity_income - entity_expenses) / 12, 2),
        })

    total_savings = grand_total_income - grand_total_expenses
    monthly_savings = total_savings / 12 if total_savings > 0 else 0

    return {
        "id": plan.id,
        "name": plan.name,
        "target_amount_cop": plan.target_amount_cop,
        "target_amount_usd": plan.target_amount_usd,
        "target_years": plan.target_years,
        "annual_return_pct": plan.annual_return_pct,
        "current_savings_cop": plan.current_savings_cop,
        "current_savings_usd": plan.current_savings_usd,
        "monthly_savings_capacity": round(monthly_savings, 2),
        "entity_savings": entity_savings,
        "projection": _calculate_projection(plan, monthly_savings),
    }


@router.put("/retirement/plan")
def update_retirement_plan(data: RetirementPlanCreate, db: Session = Depends(get_db)):
    """Create or update the retirement plan."""
    plan = db.query(RetirementPlan).order_by(RetirementPlan.id.desc()).first()
    if plan:
        plan.name = data.name
        plan.target_amount_cop = data.target_amount_cop
        plan.target_amount_usd = data.target_amount_usd
        plan.target_years = data.target_years
        plan.annual_return_pct = data.annual_return_pct
        plan.current_savings_cop = data.current_savings_cop
        plan.current_savings_usd = data.current_savings_usd
        plan.updated_at = datetime.utcnow()
    else:
        plan = RetirementPlan(**data.model_dump())
        db.add(plan)

    db.commit()
    db.refresh(plan)
    return {"ok": True, "id": plan.id}


def _calculate_projection(plan: RetirementPlan, monthly_savings: float) -> dict:
    """Calculate retirement projection."""
    monthly_rate = (1 + plan.annual_return_pct / 100) ** (1 / 12) - 1
    months = plan.target_years * 12
    monthly_contribution = plan.monthly_savings_capacity or monthly_savings or 0
    initial = plan.current_savings_cop or 0

    future_value = initial
    yearly_projection = []

    for m in range(1, months + 1):
        future_value = future_value * (1 + monthly_rate) + monthly_contribution
        if m % 12 == 0:
            yearly_projection.append({
                "year": m // 12,
                "projected_savings": round(future_value, 2),
            })

    on_track = future_value >= (plan.target_amount_cop or 0) if plan.target_amount_cop else None
    monthly_needed = 0
    if plan.target_amount_cop and monthly_rate > 0:
        monthly_needed = (plan.target_amount_cop - initial * (1 + monthly_rate) ** months) * monthly_rate / ((1 + monthly_rate) ** months - 1)

    return {
        "final_projection": round(future_value, 2),
        "target": plan.target_amount_cop,
        "on_track": on_track,
        "monthly_needed_to_reach_target": round(max(0, monthly_needed), 2),
        "monthly_gap": round(max(0, monthly_needed - monthly_contribution), 2),
        "yearly": yearly_projection,
    }
