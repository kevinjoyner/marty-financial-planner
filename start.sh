#!/bin/bash
# start.sh - Marty Application Entry Point

echo "--- MARTY STARTUP SEQUENCE ---"

# Dynamically determine DB path from the Env Var to ensure mkdir works
# Removes protocol 'sqlite://' or 'sqlite:///'
if [[ "$DATABASE_URL" == sqlite:///* ]]; then
    DB_FILE="${DATABASE_URL#sqlite://}"
    # Remove extra leading slash if needed (handling sqlite://// vs sqlite:///)
    # Simplest safe approach: just use the path we know we configured in Docker/Railway
    if [[ "$DB_FILE" == /* ]]; then
         : # It is an absolute path, good.
    else
         DB_FILE="/app/data/marty.db"
    fi
else
    DB_FILE="/app/data/marty.db"
fi

# Ensure the directory exists (Critical for Railway permissions)
mkdir -p "$(dirname "$DB_FILE")"

echo "Using Database File: $DB_FILE"

# Function to run migrations
run_migrations() {
    echo "[1/2] Running Database Migrations..."
    if alembic upgrade head; then
        echo "✅ Migrations applied successfully."
        return 0
    else
        echo "❌ Migration Failed."
        return 1
    fi
}

# Attempt 1: Normal Startup
if ! run_migrations; then
    echo "⚠️  Database schema mismatch detected."
    
    if [ -f "$DB_FILE" ]; then
        echo "♻️  Resetting Database to resolve conflict..."
        # Backup just in case
        mv "$DB_FILE" "$DB_FILE.bak.$(date +%s)"
        echo "   (Old database backed up to $DB_FILE.bak...)"
        
        # Retry Migrations on fresh DB
        echo "🔄 Retrying Migrations..."
        if run_migrations; then
            echo "✅ Database reset and migrated successfully."
        else
            echo "🔥 Critical Failure: Could not migrate even after reset."
            exit 1
        fi
    else
        # If no file exists, the previous failure was odd, but we try again essentially as a fresh start
        echo "⚠️  No DB file found, retrying migration from scratch..."
        if ! run_migrations; then
             echo "🔥 Critical Failure: Migration failed on fresh install."
             exit 1
        fi
    fi
fi

# Attempt 2: Seeding
# We run this on every startup. The seed script is idempotent (checks if data exists).
echo "[2/2] Checking Seed Data..."
python3 seed_frontend_data.py

echo "✅ Starting Application..."
# Launch the server
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
