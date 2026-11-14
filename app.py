import io
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

# Helper function to convert DataFrame to Excel (.xlsx) bytes
def to_excel_bytes(df: pd.DataFrame) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Leads_Data")
    return output.getvalue()

# Custom CSS for Centered Login, Gradient KPI Cards & Mobile Visibility
st.markdown("""
<style>
    /* Login Banner - Centered */
    .login-banner {
        background: linear-gradient(135deg, #0F172A 0%, #1E3A8A 60%, #2563EB 100%);
        padding: 1.6rem 1.5rem;
        border-radius: 16px;
        color: #FFFFFF;
        text-align: center;
        margin-bottom: 1.5rem;
        box-shadow: 0 8px 22px rgba(37, 99, 235, 0.25);
    }
    .login-banner h1 {
        margin: 0;
        font-size: 2rem;
        font-weight: 800;
        color: #FFFFFF;
        text-align: center;
    }
    .login-banner p {
        margin: 6px 0 0 0;
        font-size: 0.95rem;
        color: #DBEAFE;
        text-align: center;
    }

    /* Dashboard Header Banner */
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
    }
    .crm-banner p {
        margin: 4px 0 0 0;
        font-size: 0.92rem;
        color: #DBEAFE;
    }

    /* 4 Eye-Catching Gradient KPI Buttons */
    div[data-testid="stHorizontalBlock"]:has(.kpi-marker) > div:nth-child(1) button {
        background: linear-gradient(135deg, #1D4ED8 0%, #3B82F6 100%) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 14px !important;
        padding: 1.1rem 0.8rem !important;
        min-height: 92px !important;
        box-shadow: 0 6px 15px rgba(29, 78, 216, 0.28) !important;
    }
    div[data-testid="stHorizontalBlock"]:has(.kpi-marker) > div:nth-child(2) button {
        background: linear-gradient(135deg, #0F766E 0%, #14B8A6 100%) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 14px !important;
        padding: 1.1rem 0.8rem !important;
        min-height: 92px !important;
        box-shadow: 0 6px 15px rgba(15, 118, 110, 0.28) !important;
    }
    div[data-testid="stHorizontalBlock"]:has(.kpi-marker) > div:nth-child(3) button {
        background: linear-gradient(135deg, #15803D 0%, #22C55E 100%) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 14px !important;
        padding: 1.1rem 0.8rem !important;
        min-height: 92px !important;
        box-shadow: 0 6px 15px rgba(21, 128, 61, 0.28) !important;
    }
    div[data-testid="stHorizontalBlock"]:has(.kpi-marker) > div:nth-child(4) button {
        background: linear-gradient(135deg, #B91C1C 0%, #EF4444 100%) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 14px !important;
        padding: 1.1rem 0.8rem !important;
        min-height: 92px !important;
        box-shadow: 0 6px 15px rgba(185, 28, 28, 0.32) !important;
    }

    /* Crisp Bold White Text inside KPI Cards */
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
if "upd_select" not in st.session_state:
    st.session_state.upd_select = "-- Select a Lead --"
if "del_select" not in st.session_state:
    st.session_state.del_select = "-- Select a Lead --"
if "del_confirm_chk" not in st.session_state:
    st.session_state.del_confirm_chk = False
if "reset_upd" not in st.session_state:
    st.session_state.reset_upd = False
if "reset_del" not in st.session_state:
    st.session_state.reset_del = False
if "upd_flash" not in st.session_state:
    st.session_state.upd_flash = None
if "del_flash" not in st.session_state:
    st.session_state.del_flash = None

# Reset widget states BEFORE widgets are instantiated
if st.session_state.reset_upd:
    st.session_state.upd_select = "-- Select a Lead --"
    st.session_state.reset_upd = False

if st.session_state.reset_del:
    st.session_state.del_select = "-- Select a Lead --"
    st.session_state.del_confirm_chk = False
    st.session_state.reset_del = False

# ---------------- LOGIN SCREEN (CENTERED) ----------------
if st.session_state.user is None:
    col_l, col_m, col_r = st.columns([1, 1.8, 1])
    with col_m:
        st.markdown("""
        <div class="login-banner">
            <h1>🚀 Nikesh CRM</h1>
            <p>Sales Pipeline & Customer Relationship Management System</p>
        </div>
        """, unsafe_allow_html=True)

        with st.form("login_form"):
            st.markdown("<h3 style='text-align: center;'>🔐 Sign In to Workspace</h3>", unsafe_allow_html=True)
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
        st.session_state.reset_upd = True
        st.session_state.reset_del = True
        st.rerun()

st.markdown("""
<div class="crm-banner">
    <h1>📊 Nikesh CRM Dashboard</h1>
    <p>Tap any colored KPI card below to filter leads, analyze charts, or export to Excel</p>
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

# Separate Navigation Tabs for Clean Operations
tabs = [
    "📋 Leads & Export",
    "📈 Pipeline Analytics",
    "➕ Add Lead",
    "✏️ Update Lead",
    "🗑️ Delete Lead"
]
if current_user["role"] == "Admin":
    tabs.append("🔐 Users")

tab_objs = st.tabs(tabs)

# =========================================================
# TAB 1: VIEW LEADS, SEARCH, FILTER & EXCEL EXPORT
# =========================================================
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
            f'<div class="filter-badge">{icon_map.get(active_kpi, "📌")} Active View: <b>{active_kpi}</b></div>',
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
        df["Follow-Up Alert"] = df.apply(
            lambda r: "🔴 Due / Overdue" if is_due_or_overdue(r) else "🟢 On Track", axis=1
        )
        display_cols = ["id", "Follow-Up Alert", "name", "number", "status", "follow_up_date", "notes"]
        clean_df = df[display_cols].rename(columns={
            "id": "ID",
            "name": "Customer Name",
            "number": "Phone Number",
            "status": "Stage",
            "follow_up_date": "Follow-Up Date",
            "notes": "Notes"
        })

        st.dataframe(clean_df, use_container_width=True, hide_index=True)

        # Excel (.xlsx) Export Button
        excel_data = to_excel_bytes(clean_df)
        today_str = datetime.date.today().strftime("%Y-%m-%d")
        st.download_button(
            label="📥 Export Filtered Leads to Excel (.xlsx)",
            data=excel_data,
            file_name=f"Nikesh_CRM_{active_kpi.replace(' ', '_').replace('/', '-')}_{today_str}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary"
        )
    else:
        st.info(f"No leads found under '{active_kpi}'. Click 'Show All' or add a new lead.")

# =========================================================
# TAB 2: PIPELINE CHARTS & VISUAL ANALYTICS
# =========================================================
with tab_objs[1]:
    st.subheader("📈 Sales Pipeline Visual Analytics")
    all_leads = fetch_leads("", "All", "Total Pipeline")
    if all_leads:
        df_all = pd.DataFrame(all_leads)
        chart_c1, chart_c2 = st.columns(2)

        with chart_c1:
            st.markdown("**Leads Count by Sales Stage**")
            stage_counts = (
                df_all["status"]
                .value_counts()
                .reindex(VALID_STATUSES, fill_value=0)
            )
            st.bar_chart(stage_counts, color="#2563EB")

        with chart_c2:
            st.markdown("**Follow-Up Urgency Breakdown**")
            df_all["Urgency"] = df_all.apply(
                lambda r: "Due / Overdue" if is_due_or_overdue(r) else (
                    "Closed" if r["status"] in ("Closed Won", "Closed Lost") else "Upcoming / On Track"
                ),
                axis=1
            )
            urgency_counts = df_all["Urgency"].value_counts()
            st.bar_chart(urgency_counts, color="#0F766E")

        st.divider()
        st.markdown("**Stage Distribution Summary Table**")
        summary_df = stage_counts.reset_index()
        summary_df.columns = ["Pipeline Stage", "Lead Count"]
        summary_df["Share (%)"] = ((summary_df["Lead Count"] / len(df_all)) * 100).round(1)
        st.dataframe(summary_df, use_container_width=True, hide_index=True)
    else:
        st.info("Add some leads first to generate pipeline charts and analytics.")

# =========================================================
# TAB 3: ADD NEW LEAD
# =========================================================
with tab_objs[2]:
    st.subheader("➕ Add New Customer Lead")
    with st.form("add_lead_form", clear_on_submit=True):
        name = st.text_input("Customer Name *")
        number = st.text_input("Phone Number *")
        status = st.selectbox("Initial Status", VALID_STATUSES)
        follow_up = st.date_input("Follow-up Date", value=datetime.date.today())
        notes = st.text_area("Notes")
        if st.form_submit_button("✅ Save New Lead", use_container_width=True, type="primary"):
            try:
                create_lead(name, number, status, follow_up, notes)
                st.success(f"Added lead: {name}")
                st.rerun()
            except ValueError as e:
                st.error(str(e))

# =========================================================
# TAB 4: SEPARATE UPDATE LEAD TAB (AUTO-RESET AFTER SAVE)
# =========================================================
with tab_objs[3]:
    st.subheader("✏️ Update Existing Lead")

    if st.session_state.upd_flash:
        st.success(st.session_state.upd_flash)
        st.session_state.upd_flash = None

    all_leads_upd = fetch_leads("", "All", "Total Pipeline")
    if all_leads_upd:
        lead_map_upd = {f"#{l['id']} — {l['name']} ({l['number']}) [{l['status']}]": l for l in all_leads_upd}
        upd_options = ["-- Select a Lead --"] + list(lead_map_upd.keys())

        if st.session_state.upd_select not in upd_options:
            st.session_state.upd_select = "-- Select a Lead --"

        selected_upd_label = st.selectbox("Choose Lead to Update", upd_options, key="upd_select")

        if selected_upd_label != "-- Select a Lead --":
            sel_u = lead_map_upd[selected_upd_label]
            current_status = sel_u.get("status") or VALID_STATUSES[0]
            status_options = VALID_STATUSES if current_status in VALID_STATUSES else [current_status] + VALID_STATUSES

            with st.form(f"separate_update_form_{sel_u['id']}"):
                new_status = st.selectbox("Update Stage", status_options, index=status_options.index(current_status))
                default_date = sel_u["follow_up_date"] if sel_u["follow_up_date"] else datetime.date.today()
                new_date = st.date_input("Update Follow-up Date", value=default_date)
                new_notes = st.text_area("Update Notes", value=sel_u["notes"] or "")
                if st.form_submit_button("💾 Save Lead Changes", use_container_width=True, type="primary"):
                    modify_lead(sel_u["id"], new_status, new_date, new_notes)
                    st.session_state.upd_flash = f"✅ Lead #{sel_u['id']} ({sel_u['name']}) updated to '{new_status}'! Form reset for next update."
                    st.session_state.reset_upd = True
                    st.rerun()
        else:
            st.info("👆 Select a lead from the dropdown above to edit its stage, follow-up date, or notes.")
    else:
        st.info("No leads available to update.")

# =========================================================
# TAB 5: SEPARATE DELETE LEAD TAB (AUTO-RESET AFTER DELETE)
# =========================================================
with tab_objs[4]:
    st.subheader("🗑️ Delete a Lead")

    if st.session_state.del_flash:
        st.success(st.session_state.del_flash)
        st.session_state.del_flash = None

    all_leads_del = fetch_leads("", "All", "Total Pipeline")
    if all_leads_del:
        lead_map_del = {f"#{l['id']} — {l['name']} ({l['number']}) [{l['status']}]": l for l in all_leads_del}
        del_options = ["-- Select a Lead --"] + list(lead_map_del.keys())

        if st.session_state.del_select not in del_options:
            st.session_state.del_select = "-- Select a Lead --"

        selected_del_label = st.selectbox("Choose Lead to Delete", del_options, key="del_select")

        if selected_del_label != "-- Select a Lead --":
            sel_d = lead_map_del[selected_del_label]
            st.warning(f"⚠️ You are about to permanently delete **#{sel_d['id']} - {sel_d['name']}** ({sel_d['status']}). This action cannot be undone.")
            confirm_del = st.checkbox("Yes, I confirm I want to delete this lead permanently", key="del_confirm_chk")
            if st.button("🗑️ Confirm & Delete Lead", type="primary", disabled=not confirm_del):
                remove_lead(sel_d["id"])
                st.session_state.del_flash = f"🗑️ Lead #{sel_d['id']} ({sel_d['name']}) deleted permanently!"
                st.session_state.reset_del = True
                st.rerun()
        else:
            st.info("👆 Select a lead from the dropdown above if you want to remove it.")
    else:
        st.info("No leads available to delete.")

# =========================================================
# TAB 6: ADMIN USER MANAGEMENT
# =========================================================
if current_user["role"] == "Admin":
    with tab_objs[5]:
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