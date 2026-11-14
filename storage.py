# storage.py
import hashlib
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        port=os.getenv("DB_PORT")
    )

def hash_password(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

# --- USERS & RBAC SETUP ---
def init_users_table():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            role VARCHAR(20) DEFAULT 'user',
            can_add BOOLEAN DEFAULT TRUE,
            can_edit BOOLEAN DEFAULT TRUE,
            can_delete BOOLEAN DEFAULT FALSE,
            can_export BOOLEAN DEFAULT FALSE,
            can_analytics BOOLEAN DEFAULT TRUE
        );
    """)

    admin_user = os.getenv("CRM_USERNAME", "nikesh")
    admin_pass = os.getenv("CRM_PASSWORD", "nikesh123")
    cur.execute("SELECT id FROM users WHERE username = %s;", (admin_user,))
    if not cur.fetchone():
        cur.execute(
            """
            INSERT INTO users (username, password_hash, role, can_add, can_edit, can_delete, can_export, can_analytics)
            VALUES (%s, %s, 'admin', TRUE, TRUE, TRUE, TRUE, TRUE);
            """,
            (admin_user, hash_password(admin_pass))
        )
    conn.commit()
    cur.close()
    conn.close()

def authenticate_user(username, password):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute(
        "SELECT * FROM users WHERE username = %s AND password_hash = %s;",
        (username.strip(), hash_password(password))
    )
    user = cur.fetchone()
    cur.close()
    conn.close()
    return dict(user) if user else None

def fetch_all_users():
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute(
        "SELECT id, username, role, can_add, can_edit, can_delete, can_export, can_analytics FROM users ORDER BY id ASC;"
    )
    users = [dict(row) for row in cur.fetchall()]
    cur.close()
    conn.close()
    return users

def create_user_db(username, password, role, can_add, can_edit, can_delete, can_export, can_analytics):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO users (username, password_hash, role, can_add, can_edit, can_delete, can_export, can_analytics)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
        """,
        (username.strip(), hash_password(password), role, can_add, can_edit, can_delete, can_export, can_analytics)
    )
    conn.commit()
    cur.close()
    conn.close()

def update_user_permissions_db(user_id, role, can_add, can_edit, can_delete, can_export, can_analytics):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE users
        SET role = %s, can_add = %s, can_edit = %s, can_delete = %s, can_export = %s, can_analytics = %s
        WHERE id = %s;
        """,
        (role, can_add, can_edit, can_delete, can_export, can_analytics, user_id)
    )
    conn.commit()
    cur.close()
    conn.close()

# Self-service password change (Current password verify cheythittu update cheyyunnu)
def change_own_password_db(user_id, current_password, new_password):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT id FROM users WHERE id = %s AND password_hash = %s;",
        (user_id, hash_password(current_password))
    )
    if not cur.fetchone():
        cur.close()
        conn.close()
        return False

    cur.execute(
        "UPDATE users SET password_hash = %s WHERE id = %s;",
        (hash_password(new_password), user_id)
    )
    conn.commit()
    cur.close()
    conn.close()
    return True

# Admin direct password reset (Pazhaya password vendaathe Admin-inu reset cheyyaam)
def admin_reset_password_db(user_id, new_password):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE users SET password_hash = %s WHERE id = %s;",
        (hash_password(new_password), user_id)
    )
    conn.commit()
    cur.close()
    conn.close()

def delete_user_db(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE id = %s;", (user_id,))
    conn.commit()
    cur.close()
    conn.close()

# --- LEADS CRUD ---
def insert_lead(name, number, status="Lead", follow_up_date=None, notes=""):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO leads (name, number, status, follow_up_date, notes)
        VALUES (%s, %s, %s, %s, %s);
        """,
        (name, number, status, follow_up_date, notes)
    )
    conn.commit()
    cur.close()
    conn.close()

def fetch_all_leads():
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute(
        "SELECT id, name, number, status, follow_up_date, notes FROM leads ORDER BY id ASC;"
    )
    leads = [dict(row) for row in cur.fetchall()]
    cur.close()
    conn.close()
    return leads

def search_leads_db(keyword):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute(
        """
        SELECT id, name, number, status, follow_up_date, notes
        FROM leads
        WHERE name ILIKE %s OR notes ILIKE %s
        ORDER BY id ASC;
        """,
        (f"%{keyword}%", f"%{keyword}%")
    )
    leads = [dict(row) for row in cur.fetchall()]
    cur.close()
    conn.close()
    return leads

def update_lead_db(lead_id, new_name, new_number, new_status, new_date, new_notes):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE leads
        SET name = %s, number = %s, status = %s, follow_up_date = %s, notes = %s
        WHERE id = %s;
        """,
        (new_name, new_number, new_status, new_date, new_notes, lead_id)
    )
    conn.commit()
    cur.close()
    conn.close()

def delete_lead_db(lead_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM leads WHERE id = %s;", (lead_id,))
    conn.commit()
    cur.close()
    conn.close()