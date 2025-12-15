#!/bin/bash
# start.sh - Marty Application Entry Point

DB_FILE="/data/marty.db"

echo "--- AURA STARTUP SEQUENCE ---"

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
            
            # Optional: Seed data if it's a fresh DB? 
            # We can run the seeder if we want, but for Prod maybe empty is safer.
            # python seed_limits.py 
        else
            echo "🔥 Critical Failure: Could not migrate even after reset."
            exit 1
        fi
    else
        echo "🔥 Critical Failure: Migration failed but no DB file found?"
        exit 1
    fi
fi

echo "[2/2] Starting Application..."
# Launch the server
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
