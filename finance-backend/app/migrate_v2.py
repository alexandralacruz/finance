"""Migration v2: add categories table, is_primary_income to entities, category_id FKs."""
from app.database import init_db, engine, SessionLocal
from app.models.orm import Base, Category, Entity
from sqlalchemy import text


def migrate():
    """Create new tables/columns and seed default categories."""
    
    # 1. Add new columns to existing tables (SQLite safe via ALTER TABLE)
    with engine.connect() as conn:
        migrations = [
            ("entities", "is_primary_income", "BOOLEAN NOT NULL DEFAULT 0"),
            ("transactions", "category_id", "INTEGER REFERENCES categories(id)"),
            ("budgets", "category_id", "INTEGER REFERENCES categories(id)"),
            ("categories", "sort_order", "INTEGER NOT NULL DEFAULT 0"),
        ]
        for table, col, col_def in migrations:
            try:
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} {col_def}"))
                conn.commit()
                print(f"[OK] Added {col} to {table}")
            except Exception as e:
                if "duplicate column" in str(e).lower():
                    print(f"--> {table}.{col} already exists")
                else:
                    print(f"[WARN] {table}.{col}: {e}")

    # 2. Create tables for any new models (Category)
    init_db()

    # 3. Seed default categories
    db = SessionLocal()

    default_expense_categories = [
        "Comida",
        "Regalos",
        "Salud/medicos",
        "Vivienda",
        "Transporte",
        "Gastos personales",
        "Mascotas",
        "Suministros (luz, agua, gas, etc.)",
        "Viajes",
        "Deuda",
        "Otros",
        "Categoria personalizada 1",
        "Categoria personalizada 2",
        "Categoria personalizada 3",
    ]

    default_income_categories = [
        "Sueldo",
        "Bonificaciones",
        "Intereses",
        "Otros",
        "Categoria personalizada",
    ]

    for name in default_expense_categories:
        existing = db.query(Category).filter(Category.name == name, Category.type == "expense").first()
        if not existing:
            db.add(Category(name=name, type="expense"))
            print(f"  + expense: {name}")

    for name in default_income_categories:
        existing = db.query(Category).filter(Category.name == name, Category.type == "income").first()
        if not existing:
            db.add(Category(name=name, type="income"))
            print(f"  + income: {name}")

    db.commit()

    # 4. Smart mapping: NOMI -> Sueldo, INTERESES -> Intereses
    from app.models.orm import Transaction, Budget
    
    sueldo_cat = db.query(Category).filter(Category.name == "Sueldo", Category.type == "income").first()
    intereses_cat = db.query(Category).filter(Category.name == "Intereses", Category.type == "income").first()
    
    if sueldo_cat:
        nomi_updated = db.query(Transaction).filter(
            Transaction.category_id == None,
            Transaction.description.ilike("%nomi%"),
            Transaction.amount > 0,
        ).update({"category_id": sueldo_cat.id, "category": "Sueldo"}, synchronize_session=False)
        print(f"[OK] Mapped {nomi_updated} NOMI transactions -> Sueldo")
    
    if intereses_cat:
        int_updated = db.query(Transaction).filter(
            Transaction.category_id == None,
            Transaction.description.ilike("%intereses%"),
            Transaction.amount > 0,
        ).update({"category_id": intereses_cat.id, "category": "Intereses"}, synchronize_session=False)
        print(f"[OK] Mapped {int_updated} INTERESES transactions -> Intereses")

    # 5. Link remaining transactions to categories by name match
    categories = db.query(Category).all()
    cat_map = {c.name.lower().replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u"): c.id for c in categories}
    
    def normalize(s):
        return (s or "").lower().replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")

    txns = db.query(Transaction).filter(Transaction.category_id == None, Transaction.category != None).all()
    updated_txn = 0
    for t in txns:
        cid = cat_map.get(normalize(t.category))
        if cid:
            t.category_id = cid
            updated_txn += 1
    
    budgets = db.query(Budget).filter(Budget.category_id == None, Budget.category != None).all()
    updated_bud = 0
    for b in budgets:
        cid = cat_map.get(normalize(b.category))
        if cid:
            b.category_id = cid
            updated_bud += 1

    db.commit()
    print(f"[OK] Linked {updated_txn} transactions and {updated_bud} budgets to categories by name")

    # 6. Set sort_order on categories
    expense_order = [
        ("Comida", 1), ("Regalos", 2), ("Salud/medicos", 3), ("Vivienda", 4),
        ("Transporte", 5), ("Gastos personales", 6), ("Mascotas", 7),
        ("Suministros (luz, agua, gas, etc.)", 8), ("Viajes", 9), ("Deuda", 10),
        ("Otros", 11), ("Categoria personalizada 1", 12),
        ("Categoria personalizada 2", 13), ("Categoria personalizada 3", 14),
    ]
    income_order = [
        ("Sueldo", 1), ("Bonificaciones", 2), ("Intereses", 3),
        ("Otros", 4), ("Categoria personalizada", 5),
    ]
    for name, order in expense_order + income_order:
        c = db.query(Category).filter(Category.name == name).first()
        if c:
            c.sort_order = order
    db.commit()
    print("[OK] Updated category sort_order")

    # 7. Set BC as primary income account if not set
    bc = db.query(Entity).filter(Entity.name == "BC").first()
    if bc and not bc.is_primary_income:
        primary_exists = db.query(Entity).filter(Entity.is_primary_income == True).first()
        if not primary_exists:
            bc.is_primary_income = True
            db.commit()
            print("[OK] Set BC as primary income account")

    db.close()
    print("\n[OK] Migration v2 complete")


if __name__ == "__main__":
    migrate()
