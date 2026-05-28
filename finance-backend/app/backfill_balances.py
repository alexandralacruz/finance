"""Backfill & recompute balances for all entities.

- Finds the earliest bank-statement (non-manual) transaction with a balance as anchor
- Recomputes ALL subsequent transactions from that anchor forward
- Bank-statement balances are trusted; manual balances are recomputed
- Run with --dry-run to preview changes only
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import SessionLocal
from app.models.orm import Transaction, Entity

DRY_RUN = "--dry-run" in sys.argv

db = SessionLocal()
try:
    entities = db.query(Entity).filter(Entity.active == True).all()
    total_fixed = 0

    for entity in entities:
        print(f"\n━━━ {entity.name} ({entity.currency}) ━━━")

        # Find anchor: earliest non-manual transaction with a balance
        anchor = (
            db.query(Transaction)
            .filter(
                Transaction.entity_id == entity.id,
                Transaction.balance.isnot(None),
                Transaction.source_file != "manual",
            )
            .order_by(Transaction.date.asc(), Transaction.id.asc())
            .first()
        )

        if not anchor:
            print("  ⚠️  No bank-statement anchor found — skipping")
            continue

        # Get ALL transactions from anchor date forward
        txs = (
            db.query(Transaction)
            .filter(
                Transaction.entity_id == entity.id,
                Transaction.date >= anchor.date,
            )
            .order_by(Transaction.date.asc(), Transaction.id.asc())
            .all()
        )

        running = anchor.balance
        fixed = 0

        for tx in txs:
            if tx.id == anchor.id:
                continue  # anchor stays as-is

            # Trust non-manual balances that are >= running (forward progress)
            if tx.source_file != "manual" and tx.balance is not None and tx.balance >= running:
                running = tx.balance
                continue

            # Compute from running
            new_balance = round(running + tx.amount, 2)
            tag = "[manual]" if tx.source_file == "manual" else "[bank]"

            if tx.balance != new_balance:
                if DRY_RUN:
                    print(f"  {tag} [DRY-RUN] Would fix #{tx.id} ({tx.date}): "
                          f"{tx.amount:+.2f} → {tx.balance} → {new_balance}")
                else:
                    tx.balance = new_balance
                    print(f"  {tag} Fixed #{tx.id} ({tx.date}): "
                          f"{tx.amount:+.2f} → balance = {new_balance}")
                fixed += 1

            running = new_balance

        if not DRY_RUN:
            db.commit()

        status = "would fix" if DRY_RUN else "fixed"
        print(f"  ✅ {fixed} tx {status}, final balance = {running}")

    if DRY_RUN:
        print("\n🔍 DRY RUN — no changes made. Remove --dry-run to apply.")
    else:
        print(f"\n✅ Backfill complete.")

except Exception as e:
    if not DRY_RUN:
        db.rollback()
    print(f"❌ Error: {e}")
    raise
finally:
    db.close()
