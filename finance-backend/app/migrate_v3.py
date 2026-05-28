"""Migration v3: accounts table, entity_id -> account_id in transactions, remove currency from entities."""
from app.database import engine, SessionLocal
from app.models.orm import Base, Entity, Transaction, Account, AccountType
from sqlalchemy import text


def migrate():
    """Create accounts table, migrate transactions, clean up old columns."""

    with engine.connect() as conn:
        # Quick check: does entities table have 'currency' column?
        # If not, the DB was created from the new ORM and migration is already done.
        cols = conn.execute(text("PRAGMA table_info(entities)")).fetchall()
        col_names = [c[1] for c in cols]

        if 'currency' not in col_names:
            print("[OK] Database already has v3 schema (no currency on entities).")
            # Still ensure accounts table exists (idempotent)
            try:
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS accounts (
                        id INTEGER NOT NULL,
                        entity_id INTEGER NOT NULL,
                        account_type VARCHAR(20) NOT NULL DEFAULT 'checking',
                        currency VARCHAR(10) NOT NULL DEFAULT 'COP',
                        active BOOLEAN NOT NULL DEFAULT 1,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY (id),
                        FOREIGN KEY(entity_id) REFERENCES entities (id)
                    )
                """))
                conn.commit()
                print("[OK] Accounts table ensured.")
            except Exception as e:
                print(f"[WARN] accounts ensure: {e}")
            return

        # ── Legacy path: migrate from old schema ──
        # ── 1. Create accounts table ──
        try:
            conn.execute(text("""
                CREATE TABLE accounts (
                    id INTEGER NOT NULL,
                    entity_id INTEGER NOT NULL,
                    account_type VARCHAR(20) NOT NULL DEFAULT 'checking',
                    currency VARCHAR(10) NOT NULL DEFAULT 'COP',
                    active BOOLEAN NOT NULL DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (id),
                    FOREIGN KEY(entity_id) REFERENCES entities (id)
                )
            """))
            conn.commit()
            print("[OK] Created accounts table")
        except Exception as e:
            print(f"[WARN] accounts table: {e}")

        # ── 2. Add account_id to transactions (nullable first) ──
        try:
            conn.execute(text(
                "ALTER TABLE transactions ADD COLUMN account_id INTEGER REFERENCES accounts(id)"
            ))
            conn.commit()
            print("[OK] Added account_id to transactions")
        except Exception as e:
            if "duplicate column" in str(e).lower():
                print("--> account_id already exists in transactions")
            else:
                print(f"[WARN] account_id: {e}")

    # ── 3. Create default accounts for each entity ──
    db = SessionLocal()

    # Mapping: entity type → default account type
    type_map = {
        "bank": AccountType.checking,
        "investment": AccountType.investment_fund,
        "crypto": AccountType.spot,
        "payment_processor": AccountType.checking,
        "pension_fund": AccountType.pension,
        "trading": AccountType.investment_fund,
        "other": AccountType.other,
    }

    # Read legacy currency values from DB before ORM removes access
    with engine.connect() as conn:
        currency_rows = conn.execute(text("SELECT id, currency FROM entities")).fetchall()
        entity_currency = {row[0]: row[1] for row in currency_rows}

    entities = db.query(Entity).all()
    entity_account = {}  # entity_id -> account_id

    for e in entities:
        existing = db.query(Account).filter(Account.entity_id == e.id).first()
        if existing:
            entity_account[e.id] = existing.id
            print(f"  Account already exists for {e.name} (id={existing.id})")
            continue

        atype = type_map.get(e.type.value if hasattr(e.type, 'value') else str(e.type), AccountType.other)
        currency = entity_currency.get(e.id, 'COP')
        acct = Account(entity_id=e.id, account_type=atype, currency=currency)
        db.add(acct)
        db.flush()
        entity_account[e.id] = acct.id
        print(f"  + Account {acct.id}: {e.name} -> {atype.value} ({currency})")

    db.commit()

    # ── 4. Assign account_id to existing transactions using raw SQL ──
    with engine.connect() as conn:
        # Check if entity_id column still exists (it may have been dropped in a previous run)
        cols = conn.execute(text("PRAGMA table_info(transactions)")).fetchall()
        col_names = [c[1] for c in cols]

        if 'entity_id' not in col_names:
            print("  entity_id already removed from transactions – skipping account_id assignment")
        else:
            unassigned_count = conn.execute(
                text("SELECT COUNT(*) FROM transactions WHERE account_id IS NULL")
            ).scalar()
            print(f"  Found {unassigned_count} transactions without account_id")

            updated = 0
            for eid, aid in entity_account.items():
                result = conn.execute(
                    text("UPDATE transactions SET account_id = :aid WHERE entity_id = :eid AND account_id IS NULL"),
                    {"aid": aid, "eid": eid},
                )
                updated += result.rowcount
            conn.commit()
            print(f"[OK] Assigned account_id to {updated} transactions")

    # ── 5. Rebuild entities table to drop currency column ──
    with engine.connect() as conn:
        cols = conn.execute(text("PRAGMA table_info(entities)")).fetchall()
        col_names = [c[1] for c in cols]
        if 'currency' in col_names:
            print("  Rebuilding entities table to drop currency...")
            # Clean up any leftover from failed attempts
            conn.execute(text("DROP TABLE IF EXISTS entities_new"))
            # Get current entities data
            rows = conn.execute(text("SELECT id, name, type, active, is_primary_income, created_at FROM entities")).fetchall()
            conn.execute(text("""
                CREATE TABLE entities_new (
                    id INTEGER NOT NULL,
                    name VARCHAR(64) NOT NULL,
                    type VARCHAR(17) NOT NULL,
                    active BOOLEAN NOT NULL DEFAULT 1,
                    is_primary_income BOOLEAN NOT NULL DEFAULT 0,
                    created_at DATETIME,
                    PRIMARY KEY (id),
                    UNIQUE (name)
                )
            """))
            for row in rows:
                conn.execute(text(
                    "INSERT INTO entities_new (id, name, type, active, is_primary_income, created_at) VALUES (?, ?, ?, ?, ?, ?)"
                ), row)
            conn.execute(text("DROP TABLE entities"))
            conn.execute(text("ALTER TABLE entities_new RENAME TO entities"))
            conn.commit()
            print("  [OK] Rebuilt entities table without currency")

    # ── 6. Rebuild transactions table to drop entity_id ──
    with engine.connect() as conn:
        # Check if entity_id still exists on transactions
        cols = conn.execute(text("PRAGMA table_info(transactions)")).fetchall()
        col_names = [c[1] for c in cols]
        if 'entity_id' in col_names:
            print("  Rebuilding transactions table to drop entity_id...")
            conn.execute(text("""
                CREATE TABLE transactions_new (
                    id INTEGER NOT NULL,
                    account_id INTEGER NOT NULL,
                    date DATE NOT NULL,
                    description VARCHAR(512) NOT NULL,
                    amount FLOAT NOT NULL,
                    balance FLOAT,
                    currency VARCHAR(10) NOT NULL,
                    type VARCHAR(12) NOT NULL,
                    category VARCHAR(64),
                    category_id INTEGER REFERENCES categories(id),
                    related_entity VARCHAR(64),
                    source_file VARCHAR(512),
                    created_at DATETIME,
                    PRIMARY KEY (id),
                    FOREIGN KEY(account_id) REFERENCES accounts(id)
                )
            """))
            conn.execute(text("""
                INSERT INTO transactions_new SELECT
                    id, account_id, date, description, amount, balance,
                    currency, type, category, category_id, related_entity,
                    source_file, created_at
                FROM transactions
            """))
            conn.execute(text("DROP TABLE transactions"))
            conn.execute(text("ALTER TABLE transactions_new RENAME TO transactions"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_transactions_date ON transactions (date)"))
            conn.commit()
            print("  [OK] Rebuilt transactions table without entity_id")

    db.close()
    print("\n[OK] Migration v3 complete.")


if __name__ == "__main__":
    migrate()
