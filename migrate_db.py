import sqlite3
import logging

DB_FILE = "devices.db"
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate():
    with sqlite3.connect(DB_FILE) as conn:
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(devices)")
        columns = [column[1] for column in cur.fetchall()]
        
        if 'serial_number' not in columns:
            try:
                print("Adding serial_number column...")
                conn.execute("ALTER TABLE devices ADD COLUMN serial_number TEXT")
                conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_devices_serial_number ON devices(serial_number)")
                print("✅ Added serial_number column and unique index.")
            except Exception as e:
                print(f"❌ Error adding serial_number: {e}")
        else:
            print("ℹ️ serial_number column already exists.")

        if 'is_authorized' not in columns:
            try:
                print("Adding is_authorized column...")
                conn.execute("ALTER TABLE devices ADD COLUMN is_authorized INTEGER DEFAULT 0")
                print("✅ Added is_authorized column.")
            except Exception as e:
                print(f"❌ Error adding is_authorized: {e}")
        else:
            print("ℹ️ is_authorized column already exists.")
        
        conn.commit()

if __name__ == "__main__":
    migrate()
