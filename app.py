# app.py
import io
from datetime import date
import psycopg2
import streamlit as st
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from crm import (
    setup_database,
    login_user,
    get_users,
    add_user,
    update_user_access,
    change_own_password,
    reset_user_password_by_admin,
    remove_user,
    get_leads,
    add_lead,
    search_lead,
    update_lead,
    delete_lead
)

st.set_page_config(page_title="Nikesh CRM", page_icon="🚀", layout="wide")

setup_database()

# --- Authentication Logic ---
def login_screen():
    if "current_user" not in st.session_state:
        st.session_state["current_user"] = None

    if st.session_state["current_user"] is not None:
        return True

    _, center_col, _ = st.columns([1, 1.3, 1])
    with center_col:
        st.write("")
        st.write("")
        st.markdown("""
            <div style="background: linear-gradient(90deg, #1E3A8A 0%, #2563EB 100%);
                        padding: 1.5rem; border-radius: 12px; color: white; text-align: center; margin-bottom: 1rem;">
                <h2 style="margin:0; color:white;">🔐 Nikesh CRM</h2>
                <p style="margin:0.3rem 0 0 0; opacity:0.9; font-size:0.9rem;">Sign in with your Admin or User account</p>
            </div>
        """, unsafe_allow_html=True)

        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter username")
            password = st.text_input("Password", type="password", placeholder="Enter password")
            login_btn = st.form_submit_button("🔓 Login", use_container_width=True)

            if login_btn:
                user_record = login_user(username, password)
                if user_record:
                    st.session_state["current_user"] = user_record
                    st.rerun()
                else:
                    st.error("❌ Invalid username or password!")

    return False

if not login_screen():
    st.stop()

# ================= LOGGED IN USER & PERMISSIONS =================
user = st.session_state["current_user"]
is_admin = user["role"] == "admin"

can_add = is_admin or user["can_add"]
can_edit = is_admin or user["can_edit"]
can_delete = is_admin or user["can_delete"]
can_export = is_admin or user["can_export"]
can_analytics = is_admin or user["can_analytics"]

if "edit_reset_key" not in st.session_state:
    st.session_state["edit_reset_key"] = 0
if "edit_flash_msg" not in st.session_state:
    st.session_state["edit_flash_msg"] = ""

st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(90deg, #1E3A8A 0%, #2563EB 100%);
        padding: 1.5rem 2rem;
        border-radius: 12px;
        color: white;
        margin-bottom: 1.5rem;
    }
    .main-header h1 { margin: 0; font-size: 2rem; color: white; }
    .main-header p { margin: 0.3rem 0 0 0; opacity: 0.9; font-size: 0.95rem; }
    div[data-testid="stMetric"] {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    </style>
""", unsafe_allow_html=True)

role_badge = "👑 Admin" if is_admin else "👤 Staff User"
st.markdown(f"""
    <div class="main-header">
        <h1>🚀 Nikesh CRM</h1>
        <p>Logged in as: <b>{user['username']}</b> ({role_badge}) • Powered by PostgreSQL</p>
    </div>
""", unsafe_allow_html=True)

PIPELINE_STAGES = ["New", "Lead", "Contacted", "Qualified", "Won", "Lost"]
STATUS_BADGES = {
    "New": "🆕 New",
    "Lead": "🔵 Lead",
    "Contacted": "📞 Contacted",
    "Qualified": "⭐ Qualified",
    "Won": "🏆 Won",
    "Lost": "❌ Lost"
}

leads = get_leads()
today = date.today()

# --- Top KPI Metrics ---
total_leads = len(leads)
active_leads = sum(1 for l in leads if l["status"] in ["New", "Lead", "Contacted", "Qualified"])
won_deals = sum(1 for l in leads if l["status"] == "Won")
due_today = sum(
    1 for l in leads
    if l.get("follow_up_date") and l["follow_up_date"] <= today and l["status"] not in ["Won", "Lost"]
)

col1, col2, col3, col4 = st.columns(4)
col1.metric("📊 Total Pipeline", total_leads)
col2.metric("🔥 Active Leads", active_leads)
col3.metric("🏆 Won Deals", won_deals)
col4.metric("⏰ Due / Overdue Follow-ups", due_today)

st.write("")

# --- Sidebar: Add Lead, Change Own Password & Logout ---
st.sidebar.markdown(f"### 👤 {user['username']} ({role_badge})")
st.sidebar.divider()

if can_add:
    st.sidebar.markdown("## ➕ Add New Lead")
    with st.sidebar.form("add_lead_form", clear_on_submit=True):
        name = st.text_input("Full Name", placeholder="e.g. Rahul Menon")
        number = st.text_input("Mobile Number", placeholder="e.g. 9876543210")
        status = st.selectbox("Pipeline Stage", PIPELINE_STAGES, index=1)
        follow_up = st.date_input("Next Follow-up Date", value=today)
        notes = st.text_area("Call / Meeting Notes", placeholder="Requirements, budget, next steps...")
        submitted = st.form_submit_button("Save to Pipeline", use_container_width=True)

        if submitted:
            if name.strip() and number.strip():
                add_lead(name.strip(), number.strip(), status, follow_up, notes.strip())
                st.sidebar.success(f"✅ {name} saved!")
                st.rerun()
            else:
                st.sidebar.error("⚠️ Name and Mobile Number are required!")
else:
    st.sidebar.info("🔒 Add Lead access is restricted by Admin.")

st.sidebar.divider()

# Self-Service Change Password (Available to both Admin & Users)
with st.sidebar.expander("🔐 Change My Password"):
    with st.form("change_own_pass_form", clear_on_submit=True):
        curr_pw = st.text_input("Current Password", type="password")
        new_pw = st.text_input("New Password", type="password")
        conf_pw = st.text_input("Confirm New Password", type="password")
        if st.form_submit_button("Update My Password", use_container_width=True):
            if not curr_pw or not new_pw:
                st.error("⚠️ Fill all password fields.")
            elif new_pw != conf_pw:
                st.error("❌ New passwords do not match.")
            elif len(new_pw) < 4:
                st.error("⚠️ Password must be at least 4 characters.")
            else:
                if change_own_password(user["id"], curr_pw, new_pw):
                    st.success("✅ Password updated!")
                else:
                    st.error("❌ Current password is incorrect.")

if st.sidebar.button("🚪 Logout", use_container_width=True):
    st.session_state["current_user"] = None
    st.rerun()

# --- Excel (.xlsx) Export Builder ---
def convert_to_excel(data):
    wb = Workbook()
    ws = wb.active
    ws.title = "Leads Pipeline"

    headers = ["ID", "Lead Name", "Mobile Number", "Stage", "Follow-up Date", "Notes"]
    ws.append(headers)

    header_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
    header_font = Font(color="FFFFFF", bold=True)
    for cell in ws[1]:
        cell.fill = header_fill
        cell.font = header_font

    for l in data:
        f_date = l["follow_up_date"].strftime("%Y-%m-%d") if l.get("follow_up_date") else ""
        ws.append([
            l["id"],
            l["name"],
            str(l["number"]),
            l["status"],
            f_date,
            l.get("notes") or ""
        ])
        # Force Mobile Number & Date cells as Text so Excel never converts to E+09
        ws.cell(row=ws.max_row, column=3).number_format = "@"
        ws.cell(row=ws.max_row, column=5).number_format = "@"

    # Auto-fit Column Widths so '########' never appears
    column_widths = {"A": 8, "B": 22, "C": 18, "D": 15, "E": 16, "F": 40}
    for col_letter, width in column_widths.items():
        ws.column_dimensions[col_letter].width = width

    output = io.BytesIO()
    wb.save(output)
    return output.getvalue()

# --- Dynamic Tabs Based on Permissions ---
tab_names = ["📋 Pipeline Overview"]
if can_analytics:
    tab_names.append("📊 Stage Analytics")
if can_edit:
    tab_names.append("✏️ Edit & Follow-up")
if can_delete:
    tab_names.append("🗑️ Remove Lead")
if is_admin:
    tab_names.append("👑 User & Access Control")

tabs = st.tabs(tab_names)
tab_idx = 0

# 1. Pipeline Overview
with tabs[tab_idx]:
    tab_idx += 1
    f_col1, f_col2, f_col3 = st.columns([2, 1.5, 1])
    with f_col1:
        search_query = st.text_input("🔍 Search Name or Notes", placeholder="Search lead or keyword...")
    with f_col2:
        status_filter = st.selectbox("Filter by Stage", ["All Stages"] + PIPELINE_STAGES)
    with f_col3:
        st.write("")
        st.write("")
        if leads and can_export:
            st.download_button(
                label="📥 Export Excel",
                data=convert_to_excel(leads),
                file_name="nikesh_crm_leads.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

    filtered_leads = search_lead(search_query) if search_query else leads
    if status_filter != "All Stages":
        filtered_leads = [l for l in filtered_leads if l["status"] == status_filter]

    if not filtered_leads:
        st.info("No leads match your current filter.")
    else:
        formatted_rows = [
            {
                "ID": l["id"],
                "Lead Name": l["name"],
                "Mobile": l["number"],
                "Stage": STATUS_BADGES.get(l["status"], l["status"]),
                "Follow-up Date": str(l["follow_up_date"]) if l.get("follow_up_date") else "—",
                "Notes": l.get("notes") or "—"
            }
            for l in filtered_leads
        ]
        st.dataframe(formatted_rows, width="stretch", hide_index=True)

# 2. Stage Analytics
if can_analytics:
    with tabs[tab_idx]:
        tab_idx += 1
        st.subheader("📈 Leads Distribution by Pipeline Stage")
        if not leads:
            st.info("Add some leads to view pipeline analytics.")
        else:
            stage_counts = {stage: sum(1 for l in leads if l["status"] == stage) for stage in PIPELINE_STAGES}
            st.bar_chart(stage_counts)

            won_count = stage_counts["Won"]
            conv_rate = round((won_count / len(leads)) * 100, 1)
            st.caption(f"Overall Win Rate: **{conv_rate}%** ({won_count} won out of {len(leads)} total leads)")

# 3. Edit & Follow-up
if can_edit:
    with tabs[tab_idx]:
        tab_idx += 1

        if st.session_state["edit_flash_msg"]:
            st.success(st.session_state["edit_flash_msg"])
            st.session_state["edit_flash_msg"] = ""

        if not leads:
            st.info("No leads available to update.")
        else:
            lead_options = {"-- Select a Lead --": None}
            for l in leads:
                label = f"#{l['id']} — {l['name']} ({STATUS_BADGES.get(l['status'], l['status'])})"
                lead_options[label] = l

            selected_label = st.selectbox(
                "Select Lead to Update",
                list(lead_options.keys()),
                key=f"edit_lead_selector_{st.session_state['edit_reset_key']}"
            )
            selected_lead = lead_options[selected_label]

            if selected_lead is None:
                st.info("👆 Select a lead from the dropdown above to edit details or log follow-up notes.")
                u_col1, u_col2 = st.columns(2)
                with u_col1:
                    st.text_input("Lead Name", value="", disabled=True, key="blank_name")
                    st.text_input("Mobile Number", value="", disabled=True, key="blank_num")
                with u_col2:
                    st.selectbox("Move to Stage", PIPELINE_STAGES, disabled=True, key="blank_stage")
                    st.date_input("Follow-up Date", value=today, disabled=True, key="blank_date")
                st.text_area("Follow-up Notes", value="", disabled=True, key="blank_notes")
            else:
                u_col1, u_col2 = st.columns(2)
                with u_col1:
                    new_name = st.text_input("Lead Name", value=selected_lead["name"], key=f"name_{selected_lead['id']}")
                    new_number = st.text_input("Mobile Number", value=selected_lead["number"], key=f"num_{selected_lead['id']}")
                with u_col2:
                    current_idx = PIPELINE_STAGES.index(selected_lead["status"]) if selected_lead["status"] in PIPELINE_STAGES else 0
                    new_status = st.selectbox("Move to Stage", PIPELINE_STAGES, index=current_idx, key=f"status_{selected_lead['id']}")
                    default_date = selected_lead.get("follow_up_date") or today
                    new_date = st.date_input("Follow-up Date", value=default_date, key=f"date_{selected_lead['id']}")

                new_notes = st.text_area(
                    "Follow-up Notes",
                    value=selected_lead.get("notes") or "",
                    key=f"notes_{selected_lead['id']}"
                )

                if st.button("💾 Save Changes", type="primary"):
                    update_lead(selected_lead["id"], selected_lead, new_name, new_number, new_status, new_date, new_notes)
                    st.session_state["edit_flash_msg"] = f"✅ Saved changes for {new_name} (#{selected_lead['id']})!"
                    st.session_state["edit_reset_key"] += 1
                    st.rerun()

# 4. Remove Lead
if can_delete:
    with tabs[tab_idx]:
        tab_idx += 1
        if not leads:
            st.info("No leads available to delete.")
        else:
            del_options = {
                f"#{l['id']} — {l['name']} ({l['number']}) [{l['status']}]": l["id"]
                for l in leads
            }
            del_label = st.selectbox("Select Lead to Remove", list(del_options.keys()), key="del_box")

            if st.button("🗑️ Permanently Delete", type="primary"):
                delete_lead(del_options[del_label])
                st.warning("Lead removed from database.")
                st.rerun()

# 5. Admin Panel: User & Access Control + Admin Password Reset
if is_admin:
    with tabs[tab_idx]:
        st.subheader("👑 Create New User Account & Set Permissions")
        with st.form("create_user_form", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            with c1:
                u_name = st.text_input("New Username", placeholder="e.g. rahul")
            with c2:
                u_pass = st.text_input("Password", type="password", placeholder="Set user password")
            with c3:
                u_role = st.selectbox("Account Role", ["user", "admin"])

            st.markdown("**Assign Permissions (for Staff Users):**")
            p1, p2, p3, p4, p5 = st.columns(5)
            p_add = p1.checkbox("➕ Add Leads", value=True)
            p_edit = p2.checkbox("✏️ Edit / Follow-up", value=True)
            p_del = p3.checkbox("🗑️ Delete Leads", value=False)
            p_exp = p4.checkbox("📥 Export Excel", value=False)
            p_ana = p5.checkbox("📊 View Analytics", value=True)

            if st.form_submit_button("✅ Create User Account", use_container_width=True):
                if u_name.strip() and u_pass.strip():
                    try:
                        add_user(u_name.strip(), u_pass, u_role, p_add, p_edit, p_del, p_exp, p_ana)
                        st.success(f"User '{u_name}' created successfully!")
                        st.rerun()
                    except psycopg2.IntegrityError:
                        st.error("❌ Username already exists! Choose a different username.")
                else:
                    st.error("⚠️ Username and Password are required!")

        st.divider()
        st.subheader("🔑 Manage Existing Users, Permissions & Password Reset")
        all_users = get_users()
        for u in all_users:
            with st.expander(f"👤 {u['username']} — Role: {u['role'].upper()}"):
                if u["id"] == user["id"]:
                    st.info("You are currently logged in as this Admin account. Use '🔐 Change My Password' in the sidebar to update your password.")
                else:
                    st.markdown("**1. Role & Feature Permissions:**")
                    uc1, uc2, uc3, uc4, uc5, uc6 = st.columns([1.2, 1, 1, 1, 1, 1])
                    edit_role = uc1.selectbox(
                        "Role", ["user", "admin"],
                        index=0 if u["role"] == "user" else 1,
                        key=f"role_{u['id']}"
                    )
                    e_add = uc2.checkbox("Add", value=u["can_add"], key=f"add_{u['id']}")
                    e_edit = uc3.checkbox("Edit", value=u["can_edit"], key=f"edit_{u['id']}")
                    e_del = uc4.checkbox("Delete", value=u["can_delete"], key=f"del_{u['id']}")
                    e_exp = uc5.checkbox("Export", value=u["can_export"], key=f"exp_{u['id']}")
                    e_ana = uc6.checkbox("Analytics", value=u["can_analytics"], key=f"ana_{u['id']}")

                    if st.button("💾 Save Permissions", key=f"upd_{u['id']}"):
                        update_user_access(u["id"], edit_role, e_add, e_edit, e_del, e_exp, e_ana)
                        st.success(f"Updated permissions for {u['username']}!")
                        st.rerun()

                    st.markdown("---")
                    st.markdown(f"**2. Admin Override — Reset Password for `{u['username']}`:**")
                    rp1, rp2 = st.columns([2, 1])
                    with rp1:
                        admin_new_pw = st.text_input(
                            "Enter New Password",
                            type="password",
                            placeholder=f"New password for {u['username']}",
                            key=f"reset_pw_input_{u['id']}"
                        )
                    with rp2:
                        st.write("")
                        st.write("")
                        if st.button("🔄 Reset Password", key=f"reset_pw_btn_{u['id']}", use_container_width=True):
                            if len(admin_new_pw) >= 4:
                                reset_user_password_by_admin(u["id"], admin_new_pw)
                                st.success(f"✅ Password reset for '{u['username']}'!")
                            else:
                                st.error("⚠️ Password must be at least 4 characters.")

                    st.markdown("---")
                    if st.button(f"🗑️ Delete User '{u['username']}'", type="primary", key=f"delu_{u['id']}"):
                        remove_user(u["id"])
                        st.warning(f"Deleted user {u['username']}.")
                        st.rerun()