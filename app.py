import io
import re
import urllib.parse
import datetime
import streamlit as st
import pandas as pd
from storage import (
    init_db,
    verify_user,
    create_user,
    update_user_access,
    delete_user_db,
    get_all_users,
    ALL_PERMISSIONS
)
from crm import (
    VALID_STATUSES,
    create_lead,
    fetch_leads,
    modify_lead,
    remove_lead,
    get_pipeline_metrics,
    is_due_or_overdue,
    make_whatsapp_link
)

st.set_page_config(page_title="Nikesh CRM", page_icon="🚀", layout="wide")

# Initialize database tables & default admin on startup
init_db()

PERMISSION_LABELS = {
    "export_excel": "📥 Export Excel (.xlsx)",
    "view_analytics": "📈 Pipeline Analytics & Charts",
    "add_lead": "➕ Add New Lead",
    "update_lead": "✏️ Update Existing Lead",
    "delete_lead": "🗑️ Delete Lead"
}


def to_excel_bytes(df: pd.DataFrame) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Leads_Data")
    return output.getvalue()

# Custom CSS for Centered Login, Gradient KPI Cards & Mobile Visibility
st.markdown("""
<style>
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

# ---------------- LOGIN SCREEN ----------------
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
is_admin = current_user.get("role") == "Admin"
user_perms = ALL_PERMISSIONS if is_admin else current_user.get("permissions_list", [])

with st.sidebar:
    st.markdown(f"### 👤 {current_user['username'].capitalize()}")
    if is_admin:
        st.success("👑 Role: **Admin (Full Access)**")
    else:
        st.info(f"🛡️ Role: **{current_user['role']}**")
        st.caption("**Enabled Permissions:**")
        for p in user_perms:
            st.caption(f"• {PERMISSION_LABELS.get(p, p)}")
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
    <p>Tap any colored KPI card below to filter leads, analyze charts, or manage your pipeline</p>
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

# Build Tabs Dynamically Based on User Permissions
dynamic_tabs = [("📋 Leads Pipeline", "view_leads")]
if "view_analytics" in user_perms:
    dynamic_tabs.append(("📈 Pipeline Analytics", "view_analytics"))
if "add_lead" in user_perms:
    dynamic_tabs.append(("➕ Add Lead", "add_lead"))
if "update_lead" in user_perms:
    dynamic_tabs.append(("✏️ Update Lead", "update_lead"))
if "delete_lead" in user_perms:
    dynamic_tabs.append(("🗑️ Delete Lead", "delete_lead"))
if is_admin:
    dynamic_tabs.append(("👑 Admin Panel", "admin_panel"))

tab_labels = [t[0] for t in dynamic_tabs]
tab_keys = [t[1] for t in dynamic_tabs]
tab_objs = st.tabs(tab_labels)
tab_map = dict(zip(tab_keys, tab_objs))

# =========================================================
# TAB: VIEW LEADS, SEARCH, FILTER & EXCEL EXPORT
# =========================================================
with tab_map["view_leads"]:
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
        df["WhatsApp"] = df.apply(lambda r: make_whatsapp_link(r["name"], r["number"]), axis=1)
        display_cols = ["id", "Follow-Up Alert", "name", "number", "WhatsApp", "status", "follow_up_date", "notes"]
        clean_df = df[display_cols].rename(columns={
            "id": "ID",
            "name": "Customer Name",
            "number": "Phone Number",
            "status": "Stage",
            "follow_up_date": "Follow-Up Date",
            "notes": "Notes"
        })

        st.dataframe(
            clean_df,
            use_container_width=True,
            hide_index=True,
            column_config={"WhatsApp": st.column_config.LinkColumn("WhatsApp", display_text="💬 Chat")}
        )

        if "export_excel" in user_perms:
            excel_data = to_excel_bytes(clean_df.drop(columns=["WhatsApp"]))
            today_str = datetime.date.today().strftime("%Y-%m-%d")
            st.download_button(
                label="📥 Export Filtered Leads to Excel (.xlsx)",
                data=excel_data,
                file_name=f"Nikesh_CRM_{active_kpi.replace(' ', '_').replace('/', '-')}_{today_str}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary"
            )
    else:
        st.info(f"No leads found under '{active_kpi}'.")

# =========================================================
# TAB: PIPELINE CHARTS & VISUAL ANALYTICS
# =========================================================
if "view_analytics" in tab_map:
    with tab_map["view_analytics"]:
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
# TAB: ADD NEW LEAD
# =========================================================
if "add_lead" in tab_map:
    with tab_map["add_lead"]:
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
# TAB: UPDATE LEAD
# =========================================================
if "update_lead" in tab_map:
    with tab_map["update_lead"]:
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
                        st.session_state.upd_flash = f"✅ Lead #{sel_u['id']} ({sel_u['name']}) updated to '{new_status}'! Form reset."
                        st.session_state.reset_upd = True
                        st.rerun()
            else:
                st.info("👆 Select a lead from the dropdown above to edit its stage, follow-up date, or notes.")
        else:
            st.info("No leads available to update.")

# =========================================================
# TAB: DELETE LEAD
# =========================================================
if "delete_lead" in tab_map:
    with tab_map["delete_lead"]:
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
# TAB: ADMIN PANEL (FULL USER & ACCESS CONTROL)
# =========================================================
if is_admin and "admin_panel" in tab_map:
    with tab_map["admin_panel"]:
        st.subheader("👑 Admin Control Center — User & Access Management")
        st.caption("Create users, set passwords, and control exact feature permissions for each team member.")

        col_create, col_edit = st.columns(2)

        # 1. CREATE NEW USER WITH CUSTOM PERMISSIONS
        with col_create:
            st.markdown("### ➕ Create New User")
            with st.form("create_user_form", clear_on_submit=True):
                u_name = st.text_input("Username *")
                u_pass = st.text_input("Password *", type="password")
                u_role = st.selectbox("Role", ["Staff", "Admin"])
                st.markdown("**Select Allowed Features (for Staff):**")
                p_export = st.checkbox(PERMISSION_LABELS["export_excel"], value=True)
                p_charts = st.checkbox(PERMISSION_LABELS["view_analytics"], value=True)
                p_add = st.checkbox(PERMISSION_LABELS["add_lead"], value=True)
                p_upd = st.checkbox(PERMISSION_LABELS["update_lead"], value=True)
                p_del = st.checkbox(PERMISSION_LABELS["delete_lead"], value=False)

                if st.form_submit_button("✅ Create User Account", use_container_width=True, type="primary"):
                    if u_name.strip() and u_pass.strip():
                        selected_perms = []
                        if p_export: selected_perms.append("export_excel")
                        if p_charts: selected_perms.append("view_analytics")
                        if p_add: selected_perms.append("add_lead")
                        if p_upd: selected_perms.append("update_lead")
                        if p_del: selected_perms.append("delete_lead")
                        try:
                            create_user(u_name.strip(), u_pass.strip(), u_role, selected_perms)
                            st.success(f"User '{u_name.strip()}' created successfully!")
                            st.rerun()
                        except Exception as ex:
                            st.error(f"Could not create user: {ex}")
                    else:
                        st.error("Username and password are required.")

        # 2. MODIFY EXISTING USER PERMISSIONS / PASSWORD / DELETE
        with col_edit:
            st.markdown("### 🛠️ Edit User Access & Password")
            users_list = get_all_users()
            editable_users = [u for u in users_list if u["username"] != current_user["username"]]

            if editable_users:
                user_options = {f"#{u['id']} — {u['username']} ({u['role']})": u for u in editable_users}
                sel_u_label = st.selectbox("Select User to Manage", list(user_options.keys()))
                target_u = user_options[sel_u_label]
                t_perms = target_u.get("permissions_list", [])

                with st.form(f"edit_user_form_{target_u['id']}"):
                    edit_role = st.selectbox("Role", ["Staff", "Admin"], index=0 if target_u["role"] == "Staff" else 1)
                    reset_pwd = st.text_input("New Password (leave blank to keep current)", type="password")
                    st.markdown("**Update Allowed Features:**")
                    ep_export = st.checkbox(PERMISSION_LABELS["export_excel"], value=("export_excel" in t_perms))
                    ep_charts = st.checkbox(PERMISSION_LABELS["view_analytics"], value=("view_analytics" in t_perms))
                    ep_add = st.checkbox(PERMISSION_LABELS["add_lead"], value=("add_lead" in t_perms))
                    ep_upd = st.checkbox(PERMISSION_LABELS["update_lead"], value=("update_lead" in t_perms))
                    ep_del = st.checkbox(PERMISSION_LABELS["delete_lead"], value=("delete_lead" in t_perms))

                    c_save, c_remove = st.columns(2)
                    save_u_btn = c_save.form_submit_button("💾 Save Access", use_container_width=True, type="primary")
                    del_u_btn = c_remove.form_submit_button("🗑️ Delete User", use_container_width=True)

                    if save_u_btn:
                        new_perms = []
                        if ep_export: new_perms.append("export_excel")
                        if ep_charts: new_perms.append("view_analytics")
                        if ep_add: new_perms.append("add_lead")
                        if ep_upd: new_perms.append("update_lead")
                        if ep_del: new_perms.append("delete_lead")
                        update_user_access(target_u["id"], edit_role, new_perms, reset_pwd)
                        st.success(f"Updated access for '{target_u['username']}'!")
                        st.rerun()

                    if del_u_btn:
                        delete_user_db(target_u["id"])
                        st.warning(f"Deleted user '{target_u['username']}'.")
                        st.rerun()
            else:
                st.info("No other users created yet. Create a Staff/Demo user on the left to manage their permissions.")

        st.divider()
        st.markdown("### 📋 All Registered Users & Permissions")
        all_u_rows = []
        for u in get_all_users():
            perms_readable = "Full Access (All Features)" if u["role"] == "Admin" else ", ".join(
                [PERMISSION_LABELS.get(p, p) for p in u.get("permissions_list", [])]
            ) or "View Leads Only"
            all_u_rows.append({
                "ID": u["id"],
                "Username": u["username"],
                "Role": u["role"],
                "Allowed Access": perms_readable,
                "Created At": u["created_at"]
            })
        st.dataframe(pd.DataFrame(all_u_rows), use_container_width=True, hide_index=True)