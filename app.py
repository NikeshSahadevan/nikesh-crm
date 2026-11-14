import datetime
import streamlit as st
import pandas as pd
from storage import init_db, verify_user, create_user, get_all_users
from crm import (
    VALID_STATUSES,
    create_lead,
    fetch_leads,
    modify_lead,
    remove_lead,
    get_pipeline_metrics,
    is_due_or_overdue
)

st.set_page_config(page_title="Nikesh CRM", page_icon="🚀", layout="wide")

# Initialize database tables & default admin on startup
init_db()

# Custom CSS for Eye-Catching Mobile & Desktop UI + Colored Clickable KPI Buttons
st.markdown("""
<style>
    /* Clean Gradient Header Banner */
    .crm-banner {
        background: linear-gradient(135deg, #0F172A 0%, #1E3A8A 60%, #2563EB 100%);
        padding: 1.2rem 1.5rem;
        border-radius: 14px;
        color: #FFFFFF;
        margin-bottom: 1.2rem;
        box-shadow: 0 6px 18px rgba(37, 99, 235, 0.22);
    }
    .crm-banner h1 {
        margin: 0;
        font-size: 1.65rem;
        font-weight: 800;
        color: #FFFFFF;
        letter-spacing: 0.3px;
    }
    .crm-banner p {
        margin: 4px 0 0 0;
        font-size: 0.92rem;
        color: #DBEAFE;
    }

    /* Style the 4 KPI Buttons inside the KPI row */
    div[data-testid="stHorizontalBlock"]:has(.kpi-marker) > div:nth-child(1) button {
        background: linear-gradient(135deg, #1D4ED8 0%, #3B82F6 100%) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 14px !important;
        padding: 1.1rem 0.8rem !important;
        min-height: 92px !important;
        box-shadow: 0 6px 15px rgba(29, 78, 216, 0.28) !important;
        transition: transform 0.15s ease, box-shadow 0.15s ease !important;
    }
    div[data-testid="stHorizontalBlock"]:has(.kpi-marker) > div:nth-child(2) button {
        background: linear-gradient(135deg, #0F766E 0%, #14B8A6 100%) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 14px !important;
        padding: 1.1rem 0.8rem !important;
        min-height: 92px !important;
        box-shadow: 0 6px 15px rgba(15, 118, 110, 0.28) !important;
        transition: transform 0.15s ease, box-shadow 0.15s ease !important;
    }
    div[data-testid="stHorizontalBlock"]:has(.kpi-marker) > div:nth-child(3) button {
        background: linear-gradient(135deg, #15803D 0%, #22C55E 100%) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 14px !important;
        padding: 1.1rem 0.8rem !important;
        min-height: 92px !important;
        box-shadow: 0 6px 15px rgba(21, 128, 61, 0.28) !important;
        transition: transform 0.15s ease, box-shadow 0.15s ease !important;
    }
    div[data-testid="stHorizontalBlock"]:has(.kpi-marker) > div:nth-child(4) button {
        background: linear-gradient(135deg, #B91C1C 0%, #EF4444 100%) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 14px !important;
        padding: 1.1rem 0.8rem !important;
        min-height: 92px !important;
        box-shadow: 0 6px 15px rgba(185, 28, 28, 0.32) !important;
        transition: transform 0.15s ease, box-shadow 0.15s ease !important;
    }

    /* Bold White Text inside KPI Buttons for Mobile & Desktop Visibility */
    div[data-testid="stHorizontalBlock"]:has(.kpi-marker) button p {
        color: #FFFFFF !important;
        font-size: 1.05rem !important;
        font-weight: 700 !important;
        line-height: 1.4 !important;
        white-space: pre-line !important;
    }
    div[data-testid="stHorizontalBlock"]:has(.kpi-marker) button:hover {
        transform: translateY(-3px) !important;
        filter: brightness(1.07) !important;
    }

    /* Active Filter Pill */
    .filter-badge {
        background-color: #EFF6FF;
        border-left: 4px solid #2563EB;
        color: #1E3A8A;
        padding: 0.55rem 0.9rem;
        border-radius: 8px;
        font-weight: 600;
        font-size: 0.92rem;
        margin: 0.4rem 0 0.8rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Session states
if "user" not in st.session_state:
    st.session_state.user = None
if "kpi_filter" not in st.session_state:
    st.session_state.kpi_filter = "Total Pipeline"

# ---------------- LOGIN SCREEN ----------------
if st.session_state.user is None:
    st.markdown("""
    <div class="crm-banner">
        <h1>🚀 Nikesh CRM</h1>
        <p>Sales Pipeline & Customer Relationship Management System</p>
    </div>
    """, unsafe_allow_html=True)

    col_l, col_m, col_r = st.columns([1, 2, 1])
    with col_m:
        with st.form("login_form"):
            st.subheader("🔐 Sign In to Workspace")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Sign In", use_container_width=True, type="primary")
            if submitted:
                user = verify_user(username.strip(), password)
                if user:
                    st.session_state.user = user
                    st.rerun()
                else:
                    st.error("Invalid username or password.")
    st.stop()

# ---------------- MAIN DASHBOARD ----------------
current_user = st.session_state.user
with st.sidebar:
    st.markdown(f"### 👤 {current_user['username'].capitalize()}")
    st.caption(f"Access Level: **{current_user['role']}**")
    st.divider()
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.user = None
        st.session_state.kpi_filter = "Total Pipeline"
        st.rerun()

st.markdown("""
<div class="crm-banner">
    <h1>📊 Nikesh CRM Dashboard</h1>
    <p>Tap any colored card below to filter your leads instantly</p>
</div>
""", unsafe_allow_html=True)

# 4 Eye-Catching Clickable KPI Cards
metrics = get_pipeline_metrics()
c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown('<span class="kpi-marker"></span>', unsafe_allow_html=True)
    if st.button(f"📦 TOTAL PIPELINE\n{metrics['total']} Leads", key="btn_total", use_container_width=True):
        st.session_state.kpi_filter = "Total Pipeline"

with c2:
    if st.button(f"⚡ ACTIVE LEADS\n{metrics['active']} Active", key="btn_active", use_container_width=True):
        st.session_state.kpi_filter = "Active Leads"

with c3:
    if st.button(f"🏆 WON DEALS\n{metrics['won']} Closed", key="btn_won", use_container_width=True):
        st.session_state.kpi_filter = "Won Deals"

with c4:
    if st.button(f"⏰ DUE / OVERDUE\n{metrics['due_overdue']} Pending", key="btn_due", use_container_width=True):
        st.session_state.kpi_filter = "Due / Overdue"

# Navigation Tabs
tabs = ["📋 Leads Pipeline", "➕ Add New Lead"]
if current_user["role"] == "Admin":
    tabs.append("🔐 User Management")

tab_objs = st.tabs(tabs)

# TAB 1: VIEW, SEARCH, UPDATE & DELETE LEADS
with tab_objs[0]:
    active_kpi = st.session_state.kpi_filter
    col_badge, col_reset = st.columns([4, 1])
    with col_badge:
        icon_map = {
            "Total Pipeline": "📦",
            "Active Leads": "⚡",
            "Won Deals": "🏆",
            "Due / Overdue": "⏰"
        }
        st.markdown(
            f'<div class="filter-badge">{icon_map.get(active_kpi, "📌")} Showing: <b>{active_kpi}</b></div>',
            unsafe_allow_html=True
        )
    with col_reset:
        if active_kpi != "Total Pipeline":
            if st.button("🔄 Show All", use_container_width=True):
                st.session_state.kpi_filter = "Total Pipeline"
                st.rerun()

    col_s, col_f = st.columns([2, 1])
    search_q = col_s.text_input("🔍 Search by Name, Phone, or Notes")
    status_f = col_f.selectbox("📌 Stage Filter", ["All"] + VALID_STATUSES)

    leads = fetch_leads(search_q, status_f, active_kpi)
    if leads:
        df = pd.DataFrame(leads)
        # Add visual urgency indicator for Due/Overdue rows
        df["alert"] = df.apply(lambda r: "🔴 Due/Overdue" if is_due_or_overdue(r) else "🟢 On Track", axis=1)
        display_cols = ["id", "alert", "name", "number", "status", "follow_up_date", "notes"]
        st.dataframe(df[display_cols], use_container_width=True, hide_index=True)

        st.divider()
        st.subheader("✏️ Update or Delete a Lead")
        lead_map = {f"#{l['id']} - {l['name']} ({l['status']})": l for l in leads}
        selected_label = st.selectbox("Select Lead to Modify", list(lead_map.keys()))
        sel = lead_map[selected_label]

        with st.form("edit_lead_form"):
            new_status = st.selectbox("Status", VALID_STATUSES, index=VALID_STATUSES.index(sel["status"]))
            default_date = sel["follow_up_date"] if sel["follow_up_date"] else datetime.date.today()
            new_date = st.date_input("Follow-up Date", value=default_date)
            new_notes = st.text_area("Notes", value=sel["notes"] or "")
            col_u, col_d = st.columns(2)
            update_btn = col_u.form_submit_button("💾 Save Changes", use_container_width=True, type="primary")
            delete_btn = col_d.form_submit_button("🗑️ Delete Lead", use_container_width=True)

            if update_btn:
                modify_lead(sel["id"], new_status, new_date, new_notes)
                st.success("Lead updated successfully!")
                st.rerun()
            if delete_btn:
                remove_lead(sel["id"])
                st.warning("Lead deleted.")
                st.rerun()
    else:
        st.info(f"No leads found under '{active_kpi}'. Click 'Show All' or switch to '➕ Add New Lead'.")

# TAB 2: ADD NEW LEAD
with tab_objs[1]:
    st.subheader("➕ Add New Customer Lead")
    with st.form("add_lead_form", clear_on_submit=True):
        name = st.text_input("Customer Name *")
        number = st.text_input("Phone Number *")
        status = st.selectbox("Initial Status", VALID_STATUSES)
        follow_up = st.date_input("Follow-up Date", value=datetime.date.today())
        notes = st.text_area("Notes")
        if st.form_submit_button("✅ Add Lead", use_container_width=True, type="primary"):
            try:
                create_lead(name, number, status, follow_up, notes)
                st.success(f"Added lead: {name}")
                st.rerun()
            except ValueError as e:
                st.error(str(e))

# TAB 3: ADMIN USER MANAGEMENT
if current_user["role"] == "Admin":
    with tab_objs[2]:
        st.subheader("👥 Create Staff / Demo User Account")
        with st.form("create_user_form", clear_on_submit=True):
            u_name = st.text_input("New Username")
            u_pass = st.text_input("New Password", type="password")
            u_role = st.selectbox("Role", ["Staff", "Admin"])
            if st.form_submit_button("➕ Create User", use_container_width=True, type="primary"):
                if u_name.strip() and u_pass:
                    try:
                        create_user(u_name.strip(), u_pass, u_role)
                        st.success(f"User '{u_name}' created as {u_role}!")
                        st.rerun()
                    except Exception as ex:
                        st.error(f"Could not create user: {ex}")
                else:
                    st.error("Username and password are required.")

        st.subheader("Existing Users")
        st.dataframe(pd.DataFrame(get_all_users())[["id", "username", "role", "created_at"]], use_container_width=True, hide_index=True)