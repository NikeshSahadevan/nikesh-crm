import datetime
import pytest
from crm import is_due_or_overdue, create_lead, make_whatsapp_link

def test_overdue_active_lead():
    yesterday = datetime.date.today() - datetime.timedelta(days=1)
    lead = {"status": "Contacted", "follow_up_date": yesterday}
    assert is_due_or_overdue(lead) is True

def test_closed_won_not_overdue():
    yesterday = datetime.date.today() - datetime.timedelta(days=1)
    lead = {"status": "Closed Won", "follow_up_date": yesterday}
    assert is_due_or_overdue(lead) is False

def test_create_lead_validation():
    with pytest.raises(ValueError):
        create_lead("", "96872461992", "Lead", datetime.date.today(), "")

def test_whatsapp_link_oman_number():
    link = make_whatsapp_link("Rahul", "72461992")
    assert link.startswith("https://api.whatsapp.com/send?phone=96872461992")