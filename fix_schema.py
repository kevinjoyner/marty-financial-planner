import sqlite3
import os

def fix_database():
    # check current directory
    db_path = "marty.db"
    
    if not os.path.exists(db_path):
        print(f"Database file '{db_path}' not found in current directory.")
        # check app subdirectory
        if os.path.exists("app/marty.db"):
            db_path = "app/marty.db"
            print(f"Found database at '{db_path}'")
        else:
            print("Could not find marty.db. Please ensure you are in the project root.")
            return

    print(f"Connecting to {db_path}...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check if table exists first
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='decumulation_strategies'")
        if not cursor.fetchone():
            print("Table 'decumulation_strategies' does not exist yet. It will be created by the app startup.")
            return

        # Check if column exists
        cursor.execute("PRAGMA table_info(decumulation_strategies)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if "enabled" not in columns:
            print("Adding missing column 'enabled' to decumulation_strategies...")
            cursor.execute("ALTER TABLE decumulation_strategies ADD COLUMN enabled BOOLEAN DEFAULT 1")
            conn.commit()
            print("Migration successful.")
        else:
            print("Column 'enabled' already exists. No action needed.")
            
    except Exception as e:
        print(f"An error occurred: {e}")
        
    finally:
        conn.close()

if __name__ == "__main__":
    fix_database()
