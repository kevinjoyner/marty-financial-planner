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

DB_DIR="$(dirname "$DB_FILE")"

# --- CRITICAL FIX FOR RAILWAY VOLUMES ---
# Railway mounts volumes as root. We must chown them to appuser.
# Since we are running as root (via Dockerfile), we can do this.
if [ -d "$DB_DIR" ]; then
    echo "🔧 Fixing permissions for $DB_DIR..."
    chown -R appuser:appuser "$DB_DIR"
    chmod 755 "$DB_DIR"
fi

# Switch to appuser for all subsequent commands using gosu
# This ensures the app runs securely, not as root.
EXEC_CMD="gosu appuser"

# --- STEP 0: HEAL DATA ---
$EXEC_CMD python3 heal_db.py

# --- STEP 1: MIGRATE ---
echo "[1/2] Running Database Migrations..."
if $EXEC_CMD alembic upgrade head; then
    echo "✅ Migrations applied."
else
    echo "❌ Migration Failed."
fi

# --- STEP 2: SEED ---
echo "[2/2] Checking Seed Data..."
$EXEC_CMD python3 seed_frontend_data.py

echo "✅ Starting Application..."
# Execute the final process as appuser (replacing PID 1)
python seed_frontend_data.py
exec gosu appuser uvicorn app.main:app --host 0.0.0.0 --port 8000
