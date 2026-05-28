#!/bin/bash
set -e

echo "📦 Finance Backend - starting up..."

# Run migration if DB is empty (first run)
if [ ! -f /app/data/finance.db ] || [ ! -s /app/data/finance.db ]; then
    echo "🗄️  Database empty or missing – running migration..."
    python -m app.migrate
    echo "✅ Migration complete."
else
    echo "✅ Database exists, skipping v1 migration."
fi

echo "🔧 Running v3 migration (accounts table, account_id)..."
python -m app.migrate_v3
echo "✅ v3 migration checks complete."

echo "🔧 Running v2 migration (categories, is_primary_income)..."
python -m app.migrate_v2
echo "✅ v2 migration checks complete."

echo "🚀 Starting FastAPI server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
