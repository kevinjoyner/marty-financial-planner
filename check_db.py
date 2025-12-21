import sqlite3
import os

DB_FILE = "marty.db"

if not os.path.exists(DB_FILE):
    print(f"ERROR: {DB_FILE} does not exist!")
else:
    print(f"Connecting to {DB_FILE}...")
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    try:
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='scenarios'")
        if not cursor.fetchone():
            print("ERROR: Table 'scenarios' does not exist. The DB seems uninitialized.")
        else:
            # List Scenarios
            cursor.execute("SELECT id, name, start_date FROM scenarios")
            rows = cursor.fetchall()
            
            if not rows:
                print("Database is valid but EMPTY (0 scenarios found).")
            else:
                print(f"Found {len(rows)} scenarios:")
                for r in rows:
                    print(f"  [ID: {r[0]}] {r[1]} (Start: {r[2]})")
                    
    except Exception as e:
        print(f"Error querying database: {e}")
    finally:
        conn.close()
