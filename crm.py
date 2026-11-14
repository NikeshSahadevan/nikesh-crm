# crm.py
from storage import (
    init_users_table,
    authenticate_user,
    fetch_all_users,
    create_user_db,
    update_user_permissions_db,
    change_own_password_db,
    admin_reset_password_db,
    delete_user_db,
    insert_lead,
    fetch_all_leads,
    search_leads_db,
    update_lead_db,
    delete_lead_db
)

def setup_database():
    init_users_table()

def login_user(username, password):
    return authenticate_user(username, password)

def get_users():
    return fetch_all_users()

def add_user(username, password, role, can_add, can_edit, can_delete, can_export, can_analytics):
    create_user_db(username, password, role, can_add, can_edit, can_delete, can_export, can_analytics)

def update_user_access(user_id, role, can_add, can_edit, can_delete, can_export, can_analytics):
    update_user_permissions_db(user_id, role, can_add, can_edit, can_delete, can_export, can_analytics)

def change_own_password(user_id, current_password, new_password):
    return change_own_password_db(user_id, current_password, new_password)

def reset_user_password_by_admin(user_id, new_password):
    admin_reset_password_db(user_id, new_password)

def remove_user(user_id):
    delete_user_db(user_id)

def get_leads():
    return fetch_all_leads()

def add_lead(name, number, status="Lead", follow_up_date=None, notes=""):
    insert_lead(name, number, status, follow_up_date, notes)

def search_lead(keyword):
    return search_leads_db(keyword)

def update_lead(lead_id, old_lead, new_name, new_number, new_status, new_date, new_notes):
    final_name = new_name.strip() if new_name.strip() else old_lead["name"]
    final_number = new_number.strip() if new_number.strip() else old_lead["number"]
    update_lead_db(lead_id, final_name, final_number, new_status, new_date, new_notes.strip())

def delete_lead(lead_id):
    delete_lead_db(lead_id)