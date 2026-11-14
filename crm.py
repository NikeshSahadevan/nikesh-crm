import datetime
from storage import (
    add_lead_db,
    get_all_leads_db,
    update_lead_db,
    delete_lead_db
)

VALID_STATUSES = ["Lead", "Contacted", "Proposal Sent", "Negotiation", "Closed Won", "Closed Lost"]

def create_lead(name: str, number: str, status: str, follow_up_date, notes: str):
    if not name or not name.strip():
        raise ValueError("Customer name is required.")
    if not number or not number.strip():
        raise ValueError("Phone number is required.")
    add_lead_db(name.strip(), number.strip(), status, follow_up_date, notes.strip())

def is_due_or_overdue(lead: dict) -> bool:
    """Checks if an active lead's follow-up date is today or already passed."""
    if lead["status"] in ("Closed Won", "Closed Lost"):
        return False
    f_date = lead.get("follow_up_date")
    if not f_date:
        return False
    if isinstance(f_date, str):
        f_date = datetime.date.fromisoformat(f_date)
    return f_date <= datetime.date.today()

def fetch_leads(search_query: str = "", status_filter: str = "All", kpi_filter: str = "Total Pipeline"):
    leads = get_all_leads_db()

    # 1. Apply KPI Card Filter first
    if kpi_filter == "Active Leads":
        leads = [l for l in leads if l["status"] not in ("Closed Won", "Closed Lost")]
    elif kpi_filter == "Won Deals":
        leads = [l for l in leads if l["status"] == "Closed Won"]
    elif kpi_filter == "Due / Overdue":
        leads = [l for l in leads if is_due_or_overdue(l)]

    # 2. Apply Dropdown Status Filter
    if status_filter != "All":
        leads = [l for l in leads if l["status"] == status_filter]

    # 3. Apply Search Query
    if search_query.strip():
        q = search_query.strip().lower()
        leads = [
            l for l in leads
            if q in l["name"].lower() or q in l["number"].lower() or q in (l["notes"] or "").lower()
        ]
    return leads

def modify_lead(lead_id: int, status: str, follow_up_date, notes: str):
    update_lead_db(lead_id, status, follow_up_date, notes.strip())

def remove_lead(lead_id: int):
    delete_lead_db(lead_id)

def get_pipeline_metrics():
    leads = get_all_leads_db()
    total = len(leads)
    won = sum(1 for l in leads if l["status"] == "Closed Won")
    active = sum(1 for l in leads if l["status"] not in ("Closed Won", "Closed Lost"))
    due_overdue = sum(1 for l in leads if is_due_or_overdue(l))
    return {
        "total": total,
        "active": active,
        "won": won,
        "due_overdue": due_overdue
    }