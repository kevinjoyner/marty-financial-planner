import sqlite3
import os

# Determine DB path dynamically to match start.sh logic
# Priority 1: DATABASE_URL env var
db_url = os.getenv("DATABASE_URL")
if db_url and db_url.startswith("sqlite:///"):
    # Strip prefix
    DB_PATH = db_url.replace("sqlite:///", "")
    # Handle absolute path triple slash
    if DB_PATH.startswith("/"):
        pass # It's absolute, e.g. /data/marty.db
    else:
        # relative, assume /app/
        pass
else:
    # Priority 2: Default Hardcoded paths
    DB_PATH = "/app/data/marty.db"
    
# Fallback for local dev if not running inside Docker structure
if not os.path.exists("/app/data") and not db_url:
    if os.path.exists("marty.db"):
        DB_PATH = "marty.db"
    elif os.path.exists("data/marty.db"):
        DB_PATH = "data/marty.db"

def heal():
    if not os.path.exists(DB_PATH):
        print(f"🏥 Healer: DB not found at {DB_PATH}. Skipping.")
        return

    print(f"🏥 Healer: Checking {DB_PATH} for data corruption...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # 1. Fix Invalid 'expense' Enum in financial_events
        cursor.execute("UPDATE financial_events SET event_type = 'income_expense' WHERE event_type = 'expense'")
        if cursor.rowcount > 0:
            print(f"   ✅ Fixed {cursor.rowcount} invalid 'expense' event types.")
        
        # 2. Fix Invalid 'income' Enum (just in case)
        cursor.execute("UPDATE financial_events SET event_type = 'income_expense' WHERE event_type = 'income'")
        if cursor.rowcount > 0:
            print(f"   ✅ Fixed {cursor.rowcount} invalid 'income' event types.")

        conn.commit()
        print("🏥 Healer: Database clean.")
        
    except Exception as e:
        print(f"⚠️  Healer Warning: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    heal()
