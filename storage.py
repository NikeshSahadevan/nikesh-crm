import os
import json
import hashlib
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

ALL_PERMISSIONS = [
    "export_excel",
    "view_analytics",
    "add_lead",
    "update_lead",
    "delete_lead"
]

DEFAULT_STAFF_PERMISSIONS = [
    "export_excel",
    "view_analytics",
    "add_lead",
    "update_lead"
]

def get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        port=os.getenv("DB_PORT", "5432"),
        sslmode=os.getenv("DB_SSLMODE", "prefer")
    )

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            role VARCHAR(20) DEFAULT 'Staff',
            permissions TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    # Safely add missing columns if upgrading from an older users table
    cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS permissions TEXT;")
    cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;")

    cur.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            number VARCHAR(20) NOT NULL,
            status VARCHAR(50) DEFAULT 'Lead',
            follow_up_date DATE,
            notes TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    admin_user = os.getenv("CRM_USERNAME", "nikesh")
    admin_pass = os.getenv("CRM_PASSWORD", "nikesh123")
    cur.execute("SELECT id FROM users WHERE username = %s;", (admin_user,))
    if not cur.fetchone():
        cur.execute(
            "INSERT INTO users (username, password_hash, role, permissions) VALUES (%s, %s, %s, %s);",
            (admin_user, hash_password(admin_pass), "Admin", json.dumps(ALL_PERMISSIONS))
        )
    else:
        cur.execute(
            "UPDATE users SET role = 'Admin', permissions = %s WHERE username = %s;",
            (json.dumps(ALL_PERMISSIONS), admin_user)
        )

    conn.commit()
    cur.close()
    conn.close()

def parse_permissions(role: str, perm_str: str) -> list:
    if role == "Admin":
        return ALL_PERMISSIONS
    if not perm_str:
        return DEFAULT_STAFF_PERMISSIONS
    try:
        return json.loads(perm_str)
    except Exception:
        return DEFAULT_STAFF_PERMISSIONS

def verify_user(username: str, password: str):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute(
        "SELECT id, username, role, permissions FROM users WHERE username = %s AND password_hash = %s;",
        (username, hash_password(password))
    )
    user = cur.fetchone()
    cur.close()
    conn.close()
    if user:
        user = dict(user)
        user["permissions_list"] = parse_permissions(user["role"], user.get("permissions"))
    return user

def create_user(username: str, password: str, role: str = "Staff", permissions: list = None):
    if permissions is None:
        permissions = ALL_PERMISSIONS if role == "Admin" else DEFAULT_STAFF_PERMISSIONS
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO users (username, password_hash, role, permissions) VALUES (%s, %s, %s, %s);",
        (username, hash_password(password), role, json.dumps(permissions))
    )
    conn.commit()
    cur.close()
    conn.close()

def update_user_access(user_id: int, role: str, permissions: list, new_password: str = ""):
    if role == "Admin":
        permissions = ALL_PERMISSIONS
    conn = get_connection()
    cur = conn.cursor()
    if new_password.strip():
        cur.execute(
            "UPDATE users SET role = %s, permissions = %s, password_hash = %s WHERE id = %s;",
            (role, json.dumps(permissions), hash_password(new_password.strip()), user_id)
        )
    else:
        cur.execute(
            "UPDATE users SET role = %s, permissions = %s WHERE id = %s;",
            (role, json.dumps(permissions), user_id)
        )
    conn.commit()
    cur.close()
    conn.close()

def delete_user_db(user_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE id = %s;", (user_id,))
    conn.commit()
    cur.close()
    conn.close()

def get_all_users():
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT id, username, role, permissions, created_at FROM users ORDER BY id ASC;")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    result = []
    for r in rows:
        item = dict(r)
        item["permissions_list"] = parse_permissions(item["role"], item.get("permissions"))
        result.append(item)
    return result

def add_lead_db(name: str, number: str, status: str, follow_up_date, notes: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO leads (name, number, status, follow_up_date, notes)
           VALUES (%s, %s, %s, %s, %s);""",
        (name, number, status, follow_up_date, notes)
    )
    conn.commit()
    cur.close()
    conn.close()

def get_all_leads_db():
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM leads ORDER BY id DESC;")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def update_lead_db(lead_id: int, status: str, follow_up_date, notes: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """UPDATE leads SET status = %s, follow_up_date = %s, notes = %s
           WHERE id = %s;""",
        (status, follow_up_date, notes, lead_id)
    )
    conn.commit()
    cur.close()
    conn.close()

def delete_lead_db(lead_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM leads WHERE id = %s;", (lead_id,))
    conn.commit()
    cur.close()
    conn.close()