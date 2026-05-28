"""Budget routes: monthly spending limits per category + full budget view."""
from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, extract, case
from pydantic import BaseModel

from app.database import get_db
from app.models.orm import Budget, Transaction, Category, Entity, Account

router = APIRouter(tags=["Budgets"])


class BudgetCreate(BaseModel):
    year: int
    month: int
    category_id: int | None = None
    category: str | None = None
    limit_amount: float
    currency: str = "COP"


# ── Category CRUD ──────────────────────────────────────────────────

@router.get("/categories")
def list_categories(type: str | None = None, db: Session = Depends(get_db)):
    """List all active categories, optionally filtered by type (expense/income)."""
    q = db.query(Category).filter(Category.active == True)
    if type:
        q = q.filter(Category.type == type)
    categories = q.order_by(Category.name).all()
    return [
        {"id": c.id, "name": c.name, "type": c.type}
        for c in categories
    ]


class CategoryCreate(BaseModel):
    name: str
    type: str = "expense"  # expense | income


@router.post("/categories")
def create_category(data: CategoryCreate, db: Session = Depends(get_db)):
    """Create a new category."""
    existing = db.query(Category).filter(
        Category.name == data.name,
        Category.type == data.type,
    ).first()
    if existing:
        if not existing.active:
            existing.active = True
            db.commit()
            return {"ok": True, "reactivated": True, "id": existing.id}
        raise HTTPException(400, "Category already exists")

    cat = Category(name=data.name, type=data.type)
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return {"ok": True, "id": cat.id, "name": cat.name, "type": cat.type}


@router.delete("/categories/{category_id}")
def delete_category(category_id: int, db: Session = Depends(get_db)):
    """Soft-delete a category (sets active=false)."""
    cat = db.query(Category).filter(Category.id == category_id).first()
    if not cat:
        raise HTTPException(404, "Category not found")
    cat.active = False
    db.commit()
    return {"ok": True}


# ── Budget CRUD ────────────────────────────────────────────────────

@router.get("/budgets/{year}/{month}")
def get_budgets(year: int, month: int, db: Session = Depends(get_db)):
    """Get all budget entries for a given month."""
    budgets = (
        db.query(Budget)
        .filter(Budget.year == year, Budget.month == month)
        .all()
    )
    return [
        {
            "id": b.id,
            "year": b.year,
            "month": b.month,
            "category": b.category,
            "category_id": b.category_id,
            "limit_amount": b.limit_amount,
            "currency": b.currency,
        }
        for b in budgets
    ]


@router.post("/budgets")
def create_budget(data: BudgetCreate, db: Session = Depends(get_db)):
    """Create or update a budget entry by category_id."""
    existing = (
        db.query(Budget)
        .filter(
            Budget.year == data.year,
            Budget.month == data.month,
            Budget.category_id == data.category_id,
        )
        .first()
    )
    if existing:
        existing.limit_amount = data.limit_amount
        existing.currency = data.currency
        db.commit()
        return {"ok": True, "updated": True, "id": existing.id}

    budget = Budget(
        year=data.year,
        month=data.month,
        category=data.category,
        category_id=data.category_id,
        limit_amount=data.limit_amount,
        currency=data.currency,
    )
    db.add(budget)
    db.commit()
    db.refresh(budget)
    return {"ok": True, "updated": False, "id": budget.id}


@router.delete("/budgets/{budget_id}")
def delete_budget(budget_id: int, db: Session = Depends(get_db)):
    """Delete a budget entry (reset limit to 0)."""
    b = db.query(Budget).filter(Budget.id == budget_id).first()
    if not b:
        raise HTTPException(404, "Budget not found")
    db.delete(b)
    db.commit()
    return {"ok": True}


# ── Full budget view ───────────────────────────────────────────────

def _get_primary_entity(db: Session) -> Entity | None:
    """Get the entity marked as primary income source."""
    return db.query(Entity).filter(Entity.is_primary_income == True).first()


def _get_balance_at_date(db: Session, entity_id: int, before_date: date) -> float:
    """Get the running balance right before a given date for an entity (summed across all accounts)."""
    account_ids = [a.id for a in db.query(Account.id).filter(Account.entity_id == entity_id).all()]
    if not account_ids:
        return 0.0

    total_balance = 0.0
    for aid in account_ids:
        last_txn = (
            db.query(Transaction)
            .filter(
                Transaction.account_id == aid,
                Transaction.date < before_date,
                Transaction.balance != None,
            )
            .order_by(Transaction.date.desc(), Transaction.id.desc())
            .first()
        )
        if last_txn and last_txn.balance:
            total_balance += last_txn.balance
        else:
            total = (
                db.query(func.coalesce(func.sum(Transaction.amount), 0.0))
                .filter(
                    Transaction.account_id == aid,
                    Transaction.date < before_date,
                )
                .scalar()
            )
            total_balance += (total or 0.0)

    return total_balance


def _get_last_nomina(db: Session, entity_id: int, before_month: int, before_year: int) -> float:
    """Get total amount of 'NOMI' transactions in the most recent month that has them."""
    account_ids = [a.id for a in db.query(Account.id).filter(Account.entity_id == entity_id).all()]
    if not account_ids:
        return 0.0

    # Find the most recent month with nomina transactions
    last_nomina = (
        db.query(Transaction)
        .filter(
            Transaction.account_id.in_(account_ids),
            Transaction.description.ilike("%nomi%"),
            Transaction.amount > 0,
        )
        .order_by(Transaction.date.desc())
        .first()
    )
    if not last_nomina:
        return 0.0

    # Sum all nomina payments in that month
    nomina_month = last_nomina.date.month
    nomina_year = last_nomina.date.year
    total = (
        db.query(func.coalesce(func.sum(Transaction.amount), 0.0))
        .filter(
            Transaction.account_id.in_(account_ids),
            Transaction.description.ilike("%nomi%"),
            Transaction.amount > 0,
            extract("year", Transaction.date) == nomina_year,
            extract("month", Transaction.date) == nomina_month,
        )
        .scalar()
    )
    return total or 0.0


def _get_monthly_summary(db: Session, entity_id: int, year: int, month: int, amount_sign: str):
    """Get total income (positive) or expenses (negative) grouped by category for a month."""
    account_ids = [a.id for a in db.query(Account.id).filter(Account.entity_id == entity_id).all()]
    if not account_ids:
        return []

    sign_filter = Transaction.amount > 0 if amount_sign == "positive" else Transaction.amount < 0
    rows = (
        db.query(
            Transaction.category_id,
            Category.name,
            func.sum(func.abs(Transaction.amount)).label("total"),
        )
        .outerjoin(Category, Transaction.category_id == Category.id)
        .filter(
            Transaction.account_id.in_(account_ids),
            extract("year", Transaction.date) == year,
            extract("month", Transaction.date) == month,
            sign_filter,
        )
        .group_by(Transaction.category_id, Category.name)
        .all()
    )
    return rows  # list of (category_id, category_name, total)


@router.get("/budgets/{year}/{month}/full")
def budget_full(year: int, month: int, db: Session = Depends(get_db)):
    """
    Full budget view for a month.
    Returns saldo inicial, saldo final, ahorro, 80/20 split,
    ganancias and gastos with previsto/real/diferencia per category,
    and notifications.
    """
    primary = _get_primary_entity(db)
    if not primary:
        return {
            "error": "No primary income entity configured.",
            "hint": "Set is_primary_income=true on one entity.",
        }

    entity_id = primary.id
    entity_name = primary.name

    # -- Saldo inicial: balance just before month starts --
    month_start = date(year, month, 1)
    saldo_inicial = _get_balance_at_date(db, entity_id, month_start)

    # -- Ganancias Previsto: last nomina total --
    ganancias_previsto_total = _get_last_nomina(db, entity_id, month, year)

    # -- Ganancias Real: actual income this month --
    income_rows = _get_monthly_summary(db, entity_id, year, month, "positive")
    ganancias_real_total = sum(r[2] for r in income_rows)

    # -- Gastos Real: actual expenses this month --
    expense_rows = _get_monthly_summary(db, entity_id, year, month, "negative")
    gastos_real_total = sum(r[2] for r in expense_rows)

    # -- Gastos Previsto: from Budget table --
    budgets = (
        db.query(Budget)
        .filter(Budget.year == year, Budget.month == month)
        .all()
    )
    budget_by_cat = {}
    for b in budgets:
        cid = b.category_id or 0
        budget_by_cat[cid] = b.limit_amount
    gastos_previsto_total = sum(budget_by_cat.values())

    # -- Saldo Final --
    saldo_final = saldo_inicial + ganancias_real_total - gastos_real_total

    # -- Ahorro del mes --
    ahorro_mes = ganancias_real_total - gastos_real_total

    # -- Ahorro acumulado = current balance of primary entity (summed across all accounts) --
    account_ids = [a.id for a in db.query(Account.id).filter(Account.entity_id == entity_id).all()]
    ahorro_acumulado = 0.0
    for aid in account_ids:
        last_balance = (
            db.query(Transaction.balance)
            .filter(
                Transaction.account_id == aid,
                Transaction.balance != None,
            )
            .order_by(Transaction.date.desc(), Transaction.id.desc())
            .first()
        )
        ahorro_acumulado += (last_balance[0] if last_balance else 0.0)

    # 80/20 split
    bloqueado_80 = ahorro_acumulado * 0.80
    colchon_20 = ahorro_acumulado * 0.20

    # -- Ahorro mes anterior (for +50% comparison) --
    prev_month = month - 1
    prev_year = year
    if prev_month == 0:
        prev_month = 12
        prev_year = year - 1

    prev_income = sum(
        r[2] for r in _get_monthly_summary(db, entity_id, prev_year, prev_month, "positive")
    )
    prev_expenses = sum(
        r[2] for r in _get_monthly_summary(db, entity_id, prev_year, prev_month, "negative")
    )
    ahorro_mes_anterior = prev_income - prev_expenses

    # Variación %
    if ahorro_mes_anterior != 0:
        ahorro_variacion_pct = round(
            (ahorro_mes - ahorro_mes_anterior) / abs(ahorro_mes_anterior) * 100, 1
        )
    else:
        ahorro_variacion_pct = None  # "—" in UI

    # % ahorrado sobre ingresos
    if ganancias_real_total > 0:
        ahorro_pct_ingresos = round(ahorro_mes / ganancias_real_total * 100, 1)
    else:
        ahorro_pct_ingresos = 0.0

    # -- Notificaciones --
    notificacion, notificacion_tipo = _compute_notification(
        ahorro_mes, ahorro_acumulado, bloqueado_80, ahorro_pct_ingresos
    )

    # -- Build income categories table --
    all_income_cats = (
        db.query(Category)
        .filter(Category.active == True, Category.type == "income")
        .order_by(Category.sort_order, Category.name)
        .all()
    )
    income_by_cat = {r[0]: {"name": r[1], "real": r[2]} for r in income_rows}

    ganancias_categorias = []
    for cat in all_income_cats:
        real = income_by_cat.get(cat.id, {}).get("real", 0.0)
        # Only "Sueldo" gets the previsto (100% of nomina)
        previsto = ganancias_previsto_total if cat.name == "Sueldo" else 0.0
        ganancias_categorias.append({
            "category_id": cat.id,
            "nombre": cat.name,
            "previsto": round(previsto, 2),
            "real": round(real, 2),
            "diferencia": round(real - previsto, 2),
        })

    # Also include any income category not in the categories table
    for cid, cname, ctotal in income_rows:
        if cid is None and ctotal > 0:
            ganancias_categorias.append({
                "category_id": None,
                "nombre": cname or "Sin categoria",
                "previsto": 0.0,
                "real": round(ctotal, 2),
                "diferencia": round(ctotal, 2),
            })

    # -- Build expense categories table --
    all_expense_cats = (
        db.query(Category)
        .filter(Category.active == True, Category.type == "expense")
        .order_by(Category.sort_order, Category.name)
        .all()
    )
    expense_by_cat = {r[0]: {"name": r[1], "real": r[2]} for r in expense_rows}

    gastos_categorias = []
    for cat in all_expense_cats:
        real = expense_by_cat.get(cat.id, {}).get("real", 0.0)
        previsto = budget_by_cat.get(cat.id, 0.0)
        gastos_categorias.append({
            "category_id": cat.id,
            "nombre": cat.name,
            "previsto": round(previsto, 2),
            "real": round(real, 2),
            "diferencia": round(previsto - real, 2),  # positive = underspent
            "editable": True,
        })

    # Also include uncategorized expenses
    for cid, cname, ctotal in expense_rows:
        if cid is None and ctotal > 0:
            gastos_categorias.append({
                "category_id": None,
                "nombre": cname or "Sin categoria",
                "previsto": 0.0,
                "real": round(ctotal, 2),
                "diferencia": round(-ctotal, 2),
                "editable": False,
            })

    return {
        "year": year,
        "month": month,
        "primary_entity": entity_name,
        "saldo_inicial": round(saldo_inicial, 2),
        "saldo_final": round(saldo_final, 2),
        "ahorro_mes": round(ahorro_mes, 2),
        "ahorro_acumulado": round(ahorro_acumulado, 2),
        "ahorro_acumulado_80": round(bloqueado_80, 2),
        "ahorro_acumulado_20": round(colchon_20, 2),
        "ahorro_mes_anterior": round(ahorro_mes_anterior, 2),
        "ahorro_variacion_pct": ahorro_variacion_pct,
        "ahorro_pct_ingresos": ahorro_pct_ingresos,
        "notificacion": notificacion,
        "notificacion_tipo": notificacion_tipo,
        "ganancias": {
            "previsto_total": round(ganancias_previsto_total, 2),
            "real_total": round(ganancias_real_total, 2),
            "diferencia_total": round(ganancias_real_total - ganancias_previsto_total, 2),
            "categorias": ganancias_categorias,
        },
        "gastos": {
            "previsto_total": round(gastos_previsto_total, 2),
            "real_total": round(gastos_real_total, 2),
            "diferencia_total": round(gastos_previsto_total - gastos_real_total, 2),
            "categorias": gastos_categorias,
        },
    }


def _compute_notification(ahorro_mes, ahorro_acumulado, bloqueado_80, ahorro_pct_ingresos):
    """Determine budget notification state."""
    if ahorro_pct_ingresos >= 20 and ahorro_mes > 0:
        return "Felicitacion! Ahorraste al menos el 20% de tus ingresos este mes", "felicitacion"
    elif ahorro_mes > 0:
        return "Vas bien! Ahorro positivo este mes", "bien"
    elif ahorro_mes == 0:
        return "Vas bien! Sin cambios este mes", "bien"
    elif ahorro_mes < 0:
        # Déficit: check against 80% bloqueado
        nuevo_acumulado = ahorro_acumulado + ahorro_mes
        if nuevo_acumulado < bloqueado_80:
            return "ALARMA: El deficit esta consumiendo el ahorro bloqueado (80%)", "alarma"
        else:
            return "Advertencia: Deficit este mes, pero dentro del colchon del 20%", "advertencia"
    return "Sin datos", "neutro"


# ── Legacy status endpoint (kept for backwards compat) ─────────────

@router.get("/budgets/{year}/{month}/status")
def budget_status(year: int, month: int, db: Session = Depends(get_db)):
    """Compare actual spending vs budget for a month."""
    budgets = (
        db.query(Budget)
        .filter(Budget.year == year, Budget.month == month)
        .all()
    )

    expenses = (
        db.query(
            Transaction.category,
            func.sum(Transaction.amount).label("total")
        )
        .filter(
            extract("year", Transaction.date) == year,
            extract("month", Transaction.date) == month,
            Transaction.amount < 0,
        )
        .group_by(Transaction.category)
        .all()
    )

    categories = {}
    for cat, spent in expenses:
        categories[cat or "sin_categoria"] = abs(spent)

    result = []
    for b in budgets:
        spent = categories.get(b.category or "sin_categoria", 0)
        result.append({
            "category": b.category,
            "limit": b.limit_amount,
            "spent": round(spent, 2),
            "remaining": round(b.limit_amount - spent, 2),
            "pct_used": round((spent / b.limit_amount * 100) if b.limit_amount else 0, 1),
            "currency": b.currency,
        })

    all_budgeted = {b.category for b in budgets}
    for cat, spent in categories.items():
        if cat not in all_budgeted:
            result.append({
                "category": cat,
                "limit": 0,
                "spent": round(spent, 2),
                "remaining": round(-spent, 2),
                "pct_used": 100,
                "currency": "COP",
            })

    total_budget = sum(b.limit_amount for b in budgets if b.category is None)
    total_spent = sum(categories.values())

    return {
        "year": year,
        "month": month,
        "total_budget": total_budget,
        "total_spent": round(total_spent, 2),
        "remaining": round(total_budget - total_spent, 2),
        "details": result,
    }
