from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
import secrets
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
# Generate a secure secret key if not set in environment
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))

# Security settings
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('FLASK_ENV') == 'production'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour session timeout

DB_FILE = "devices.db"

# --------------------- Database setup ---------------------
def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            serial_number TEXT UNIQUE,
            os TEXT,
            browser TEXT,
            ip TEXT,
            is_authorized INTEGER DEFAULT 0,
            registered_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )""")
        
        # Migration: Check if serial_number and is_authorized columns exist
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(devices)")
        columns = [column[1] for column in cur.fetchall()]
        
        if 'serial_number' not in columns:
            try:
                # SQLite doesn't support UNIQUE constraint in ALTER TABLE ADD COLUMN
                conn.execute("ALTER TABLE devices ADD COLUMN serial_number TEXT")
                conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_devices_serial_number ON devices(serial_number)")
                logger.info("Added serial_number column and unique index to devices table")
            except sqlite3.OperationalError as e:
                logger.error(f"Error adding serial_number column: {e}")
                pass
        
        if 'is_authorized' not in columns:
            try:
                conn.execute("ALTER TABLE devices ADD COLUMN is_authorized INTEGER DEFAULT 0")
                logger.info("Added is_authorized column to devices table")
            except sqlite3.OperationalError:
                pass
        
        conn.execute("""CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )""")
        conn.commit()

# Initialize DB and add default admin
def init_admin():
    with sqlite3.connect(DB_FILE) as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM admins WHERE username=?", ("admin",))
        admin = cur.fetchone()
        if not admin:
            # Hash the default password
            hashed_password = generate_password_hash("1234")
            cur.execute("INSERT INTO admins (username, password) VALUES (?, ?)", ("admin", hashed_password))
            conn.commit()
        else:
            # Migrate existing plaintext passwords to hashed passwords
            existing_password = admin[2]
            if existing_password and '$' not in existing_password:
                hashed_password = generate_password_hash(existing_password)
                cur.execute("UPDATE admins SET password = ? WHERE username = ?", (hashed_password, "admin"))
                conn.commit()
        
        # Migrate all other admin accounts with plaintext passwords
        cur.execute("SELECT id, username, password FROM admins")
        all_admins = cur.fetchall()
        for admin_row in all_admins:
            admin_password = admin_row[2]
            if admin_password and '$' not in admin_password:
                hashed_password = generate_password_hash(admin_password)
                cur.execute("UPDATE admins SET password = ? WHERE id = ?", (hashed_password, admin_row[0]))
                conn.commit()

# --------------------- Routes ---------------------
@app.route("/")
def index():
    return render_template("device-registration.html")

@app.route("/register", methods=["POST"])
def register_device():
    # Validate Content-Type
    if not request.is_json:
        return jsonify({"status": "error", "message": "Content-Type must be application/json"}), 400
    
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "Invalid JSON data"}), 400
    
    name = data.get("name", "").strip()
    serial_number = data.get("serial_number", "").strip()
    os_name = data.get("os", "").strip()
    browser = data.get("browser", "").strip()
    
    # Input validation
    if not name:
        return jsonify({"status": "error", "message": "Device name is required"}), 400
    
    if not serial_number:
        return jsonify({"status": "error", "message": "Serial number is required"}), 400
    
    # Sanitize input - limit lengths
    if len(name) > 100:
        return jsonify({"status": "error", "message": "Device name is too long"}), 400
    if len(serial_number) > 100:
        return jsonify({"status": "error", "message": "Serial number is too long"}), 400
    if len(os_name) > 50:
        return jsonify({"status": "error", "message": "OS name is too long"}), 400
    if len(browser) > 50:
        return jsonify({"status": "error", "message": "Browser name is too long"}), 400
    
    # Get IP address (handle proxy headers)
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    if ip:
        ip = ip.split(',')[0].strip()

    try:
        with sqlite3.connect(DB_FILE) as conn:
            # Check if serial number already exists
            cur = conn.cursor()
            cur.execute("SELECT id FROM devices WHERE serial_number = ?", (serial_number,))
            if cur.fetchone():
                return jsonify({"status": "error", "message": f"Serial number {serial_number} is already registered"}), 400

            conn.execute("INSERT INTO devices (name, serial_number, os, browser, ip, is_authorized) VALUES (?, ?, ?, ?, ?, 0)",
                         (name, serial_number, os_name, browser, ip))
            conn.commit()
            
        logger.info(f"Device registered: {name} (SN: {serial_number}, {os_name}, {browser})")
        return jsonify({"status": "success", "message": "Device registered successfully and is awaiting authorization"})
        
    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")
        return jsonify({"status": "error", "message": "Database error occurred"}), 500

# --------------------- Admin area ---------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        
        # Input validation
        if not username or not password:
            return render_template("admin-login.html", error="Username and password are required")
        
        if len(username) > 50:
            return render_template("admin-login.html", error="Invalid credentials")
        
        with sqlite3.connect(DB_FILE) as conn:
            cur = conn.cursor()
            cur.execute("SELECT id, username, password FROM admins WHERE username=?", (username,))
            admin = cur.fetchone()
        
        if admin:
            stored_password_hash = admin[2]
            
            if '$' in stored_password_hash:
                if check_password_hash(stored_password_hash, password):
                    session["admin"] = username
                    session["admin_id"] = admin[0]
                    session.permanent = True
                    logger.info(f"Admin logged in: {username}")
                    return redirect(url_for("admin_dashboard"))
            else:
                if stored_password_hash == password:
                    hashed_password = generate_password_hash(password)
                    with sqlite3.connect(DB_FILE) as conn:
                        cur = conn.cursor()
                        cur.execute("UPDATE admins SET password = ? WHERE username = ?", (hashed_password, username))
                        conn.commit()
                    session["admin"] = username
                    session["admin_id"] = admin[0]
                    session.permanent = True
                    logger.info(f"Admin logged in (migrated): {username}")
                    return redirect(url_for("admin_dashboard"))
        
        logger.warning(f"Failed login attempt for user: {username}")
        return render_template("admin-login.html", error="Invalid username or password")
    
    return render_template("admin-login.html")

@app.route("/logout")
def logout():
    username = session.get("admin")
    session.clear()
    logger.info(f"Admin logged out: {username}")
    return redirect(url_for("login"))

@app.route("/admin")
def admin_dashboard():
    if "admin" not in session or "admin_id" not in session:
        return redirect(url_for("login"))
    
    with sqlite3.connect(DB_FILE) as conn:
        cur = conn.cursor()
        cur.execute("SELECT id FROM admins WHERE id=? AND username=?", (session.get("admin_id"), session.get("admin")))
        if not cur.fetchone():
            session.clear()
            return redirect(url_for("login"))
        
        cur.execute("SELECT id, name, serial_number, os, browser, ip, is_authorized, registered_at FROM devices ORDER BY id DESC")
        devices = [
            {
                "id": row[0],
                "name": row[1],
                "serial_number": row[2],
                "os": row[3],
                "browser": row[4],
                "ip": row[5],
                "is_authorized": row[6],
                "registered_at": row[7]
            }
            for row in cur.fetchall()
        ]
    
    return render_template("admin-dashboard.html", devices=devices)

# --------------------- API for external access ---------------------
@app.route("/api/devices")
def api_devices():
    """Get all registered devices"""
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cur = conn.cursor()
            cur.execute("SELECT id, name, serial_number, os, browser, ip, is_authorized, registered_at FROM devices ORDER BY id DESC")
            devices = [
                {
                    "id": row[0],
                    "name": row[1],
                    "serial_number": row[2],
                    "os": row[3],
                    "browser": row[4],
                    "ip": row[5],
                    "is_authorized": row[6],
                    "registered_at": row[7]
                }
                for row in cur.fetchall()
            ]
        return jsonify({
            "status": "success",
            "count": len(devices),
            "devices": devices
        })
    except Exception as e:
        logger.error(f"API error in /api/devices: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/devices/<int:device_id>")
def api_get_device(device_id):
    """Get a specific device by ID"""
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cur = conn.cursor()
            cur.execute("SELECT id, name, serial_number, os, browser, ip, is_authorized, registered_at FROM devices WHERE id=?", (device_id,))
            row = cur.fetchone()
            
            if row:
                device = {
                    "id": row[0],
                    "name": row[1],
                    "serial_number": row[2],
                    "os": row[3],
                    "browser": row[4],
                    "ip": row[5],
                    "is_authorized": row[6],
                    "registered_at": row[7]
                }
                return jsonify({
                    "status": "success",
                    "device": device
                })
            else:
                return jsonify({
                    "status": "error",
                    "message": "Device not found"
                }), 404
    except Exception as e:
        logger.error(f"API error in /api/devices/{device_id}: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/devices/check")
def api_check_device():
    """Check if a device exists by name"""
    device_name = request.args.get('name', '').strip()
    
    if not device_name:
        return jsonify({
            "status": "error",
            "message": "Device name parameter is required"
        }), 400
    
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cur = conn.cursor()
            cur.execute("SELECT id, name, serial_number, os, browser, ip, is_authorized, registered_at FROM devices WHERE name=? ORDER BY id DESC LIMIT 1", (device_name,))
            row = cur.fetchone()
            
            if row:
                device = {
                    "id": row[0],
                    "name": row[1],
                    "serial_number": row[2],
                    "os": row[3],
                    "browser": row[4],
                    "ip": row[5],
                    "is_authorized": row[6],
                    "registered_at": row[7]
                }
                return jsonify({
                    "status": "success",
                    "exists": True,
                    "device": device
                })
            else:
                return jsonify({
                    "status": "success",
                    "exists": False,
                    "message": "Device not found"
                })
    except Exception as e:
        logger.error(f"API error in /api/devices/check: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/devices/search")
def api_search_devices():
    """Search devices by name, OS, or browser"""
    query = request.args.get('q', '').strip()
    
    if not query:
        return jsonify({
            "status": "error",
            "message": "Search query parameter 'q' is required"
        }), 400
    
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cur = conn.cursor()
            search_pattern = f"%{query}%"
            cur.execute("""
                SELECT id, name, serial_number, os, browser, ip, is_authorized, registered_at 
                FROM devices 
                WHERE name LIKE ? OR serial_number LIKE ? OR os LIKE ? OR browser LIKE ? 
                ORDER BY id DESC
            """, (search_pattern, search_pattern, search_pattern, search_pattern))
            
            devices = [
                {
                    "id": row[0],
                    "name": row[1],
                    "serial_number": row[2],
                    "os": row[3],
                    "browser": row[4],
                    "ip": row[5],
                    "is_authorized": row[6],
                    "registered_at": row[7]
                }
                for row in cur.fetchall()
            ]
            
            return jsonify({
                "status": "success",
                "query": query,
                "count": len(devices),
                "devices": devices
            })
    except Exception as e:
        logger.error(f"API error in /api/devices/search: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/devices/stats")
def api_device_stats():
    """Get device statistics"""
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cur = conn.cursor()
            
            # Total devices
            cur.execute("SELECT COUNT(*) FROM devices")
            total = cur.fetchone()[0]
            
            # Devices by OS
            cur.execute("SELECT os, COUNT(*) as count FROM devices GROUP BY os ORDER BY count DESC")
            os_stats = {row[0]: row[1] for row in cur.fetchall()}
            
            # Devices by browser
            cur.execute("SELECT browser, COUNT(*) as count FROM devices GROUP BY browser ORDER BY count DESC")
            browser_stats = {row[0]: row[1] for row in cur.fetchall()}
            
            # Recent registrations (last 24 hours)
            cur.execute("""
                SELECT COUNT(*) 
                FROM devices 
                WHERE datetime(registered_at) > datetime('now', '-1 day')
            """)
            recent_24h = cur.fetchone()[0]
            
            # Recent registrations (last 7 days)
            cur.execute("""
                SELECT COUNT(*) 
                FROM devices 
                WHERE datetime(registered_at) > datetime('now', '-7 days')
            """)
            recent_7d = cur.fetchone()[0]
            
            return jsonify({
                "status": "success",
                "stats": {
                    "total": total,
                    "recent_24h": recent_24h,
                    "recent_7d": recent_7d,
                    "by_os": os_stats,
                    "by_browser": browser_stats
                }
            })
    except Exception as e:
        logger.error(f"API error in /api/device/stats: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# --------------------- Admin Device Authorization ---------------------
@app.route("/api/devices/<int:device_id>/authorize", methods=["POST"])
def api_authorize_device(device_id):
    """Authorize or deauthorize a device (admin only)"""
    if "admin" not in session or "admin_id" not in session:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
    
    if not request.is_json:
        return jsonify({"status": "error", "message": "Content-Type must be application/json"}), 400
    
    data = request.get_json()
    authorize = data.get("authorize", True)
    
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cur = conn.cursor()
            # Check if device exists
            cur.execute("SELECT id FROM devices WHERE id=?", (device_id,))
            if not cur.fetchone():
                return jsonify({"status": "error", "message": "Device not found"}), 404
            
            # Update authorization status
            status = 1 if authorize else 0
            cur.execute("UPDATE devices SET is_authorized=? WHERE id=?", (status, device_id))
            conn.commit()
            
            action = "authorized" if authorize else "deauthorized"
            logger.info(f"Device {device_id} {action} by admin: {session.get('admin')}")
            return jsonify({"status": "success", "message": f"Device {action} successfully"})
            
    except sqlite3.Error as e:
        logger.error(f"Database error authorizing device: {e}")
        return jsonify({"status": "error", "message": "Database error occurred"}), 500

@app.route("/api/devices/authorize-serial", methods=["POST"])
def api_authorize_serial():
    """Authorize a device by its serial number (admin only)"""
    if "admin" not in session or "admin_id" not in session:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
    
    if not request.is_json:
        return jsonify({"status": "error", "message": "Content-Type must be application/json"}), 400
    
    data = request.get_json()
    serial_number = data.get("serial_number", "").strip()
    authorize = data.get("authorize", True)
    
    if not serial_number:
        return jsonify({"status": "error", "message": "Serial number is required"}), 400
    
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cur = conn.cursor()
            # Check if device exists
            cur.execute("SELECT id FROM devices WHERE serial_number=?", (serial_number,))
            device = cur.fetchone()
            if not device:
                return jsonify({"status": "error", "message": f"Device with SN {serial_number} not found"}), 404
            
            # Update authorization status
            status = 1 if authorize else 0
            cur.execute("UPDATE devices SET is_authorized=? WHERE serial_number=?", (status, serial_number))
            conn.commit()
            
            action = "authorized" if authorize else "deauthorized"
            logger.info(f"Device SN {serial_number} {action} by admin: {session.get('admin')}")
            return jsonify({"status": "success", "message": f"Device with serial number {serial_number} {action} successfully"})
            
    except sqlite3.Error as e:
        logger.error(f"Database error authorizing device by SN: {e}")
        return jsonify({"status": "error", "message": "Database error occurred"}), 500

# --------------------- Admin Device Management ---------------------
@app.route("/api/devices/<int:device_id>", methods=["PUT"])
def api_update_device(device_id):
    """Update a device (admin only)"""
    if "admin" not in session or "admin_id" not in session:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
    
    if not request.is_json:
        return jsonify({"status": "error", "message": "Content-Type must be application/json"}), 400
    
    data = request.get_json()
    name = data.get("name", "").strip()
    os_name = data.get("os", "").strip()
    browser = data.get("browser", "").strip()
    
    # Input validation
    if not name:
        return jsonify({"status": "error", "message": "Device name is required"}), 400
    
    if len(name) > 100:
        return jsonify({"status": "error", "message": "Device name is too long"}), 400
    if len(os_name) > 50:
        return jsonify({"status": "error", "message": "OS name is too long"}), 400
    if len(browser) > 50:
        return jsonify({"status": "error", "message": "Browser name is too long"}), 400
    
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cur = conn.cursor()
            # Check if device exists
            cur.execute("SELECT id FROM devices WHERE id=?", (device_id,))
            if not cur.fetchone():
                return jsonify({"status": "error", "message": "Device not found"}), 404
            
            # Update device
            cur.execute("""
                UPDATE devices 
                SET name=?, os=?, browser=? 
                WHERE id=?
            """, (name, os_name, browser, device_id))
            conn.commit()
            
            logger.info(f"Device {device_id} updated by admin: {session.get('admin')}")
            return jsonify({"status": "success", "message": "Device updated successfully"})
            
    except sqlite3.Error as e:
        logger.error(f"Database error updating device: {e}")
        return jsonify({"status": "error", "message": "Database error occurred"}), 500

@app.route("/api/devices/<int:device_id>", methods=["DELETE"])
def api_delete_device(device_id):
    """Delete a device (admin only)"""
    if "admin" not in session or "admin_id" not in session:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
    
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cur = conn.cursor()
            # Check if device exists
            cur.execute("SELECT id FROM devices WHERE id=?", (device_id,))
            if not cur.fetchone():
                return jsonify({"status": "error", "message": "Device not found"}), 404
            
            # Delete device
            cur.execute("DELETE FROM devices WHERE id=?", (device_id,))
            conn.commit()
            
            logger.info(f"Device {device_id} deleted by admin: {session.get('admin')}")
            return jsonify({"status": "success", "message": "Device deleted successfully"})
            
    except sqlite3.Error as e:
        logger.error(f"Database error deleting device: {e}")
        return jsonify({"status": "error", "message": "Database error occurred"}), 500

# --------------------- Health Check ---------------------
@app.route("/health")
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "device-registration-portal"
    })

# --------------------- Main ---------------------
if __name__ == "__main__":
    init_db()
    init_admin()
    
    print("=" * 60)
    print("🚀 Device Registration Portal")
    print("=" * 60)
    print(f"📍 Web Portal: http://localhost:8080")
    print(f"🔐 Admin Login: http://localhost:8080/login")
    print(f"❤️  Health Check: http://localhost:8080/health")
    print("\n📚 API Endpoints:")
    print(f"  GET  /api/devices - Get all devices")
    print(f"  GET  /api/devices/<id> - Get device by ID")
    print(f"  GET  /api/devices/check?name=<name> - Check if device exists")
    print(f"  GET  /api/devices/search?q=<query> - Search devices")
    print(f"  GET  /api/devices/stats - Get device statistics")
    print("\n💡 Note: Telegram bot runs separately on port 8081")
    print("=" * 60)
    
    app.run(host="0.0.0.0", port=8080, debug=True)