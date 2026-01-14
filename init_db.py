import sqlite3
from werkzeug.security import generate_password_hash
import os

DB_FILE = "devices.db"

def init_db():
    """Create database tables if they don't exist."""
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            serial_number TEXT UNIQUE,
            os TEXT,
            browser TEXT,
            ip TEXT,
            is_authorized INTEGER DEFAULT 0,
            registered_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)
        conn.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
        """)
        conn.commit()
    print("✅ Database tables initialized.")


def init_admin():
    """Add default admin or upgrade plaintext passwords."""
    with sqlite3.connect(DB_FILE) as conn:
        cur = conn.cursor()

        # Check if admin exists
        cur.execute("SELECT * FROM admins WHERE username = ?", ("admin",))
        admin = cur.fetchone()

        if not admin:
            hashed_password = generate_password_hash("1234")
            cur.execute(
                "INSERT INTO admins (username, password) VALUES (?, ?)",
                ("admin", hashed_password)
            )
            conn.commit()
            print("✅ Default admin created (username='admin', password='1234')")
        else:
            # Migrate plaintext passwords to hashed
            cur.execute("SELECT id, password FROM admins")
            for row in cur.fetchall():
                if '$' not in row[1]:
                    hashed = generate_password_hash(row[1])
                    cur.execute(
                        "UPDATE admins SET password=? WHERE id=?",
                        (hashed, row[0])
                    )
                    print(f"🔒 Migrated admin ID {row[0]} password to hash.")
            conn.commit()


if __name__ == "__main__":
    print("=" * 60)
    print("🗄️ Initializing Device Registration Database")
    print("=" * 60)
    init_db()
    init_admin()
    print("✅ Database setup complete. File:", os.path.abspath(DB_FILE))
    print("=" * 60)
