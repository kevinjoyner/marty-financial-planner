#!/bin/bash
# start.sh - Marty Application Entry Point

echo "--- MARTY STARTUP SEQUENCE ---"

# Dynamically determine DB path
if [[ "$DATABASE_URL" == sqlite:///* ]]; then
    DB_FILE="${DATABASE_URL#sqlite://}"
    if [[ "$DB_FILE" != /* ]]; then
         DB_FILE="/app/data/marty.db"
    fi
else
    DB_FILE="/app/data/marty.db"
fi

# Ensure directory exists
mkdir -p "$(dirname "$DB_FILE")"

# --- STEP 0: HEAL DATA ---
# Fix any corrupted Enums from bad imports before the app tries to read them
python3 heal_db.py

# --- STEP 1: MIGRATE ---
echo "[1/2] Running Database Migrations..."
if alembic upgrade head; then
    echo "✅ Migrations applied."
else
    echo "❌ Migration Failed."
    # If migration fails, we don't exit immediately in case it's a transient lock, 
    # but for a schema mismatch, the app will likely crash later.
fi

# --- STEP 2: SEED ---
echo "[2/2] Checking Seed Data..."
python3 seed_frontend_data.py

echo "✅ Starting Application..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
