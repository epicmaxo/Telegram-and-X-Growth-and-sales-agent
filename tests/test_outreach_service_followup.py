from datetime import datetime

from src.agent.outreach.service import OutboundCampaignService
from src.storage.database import DatabaseService


def test_campaign_allows_follow_ups_beyond_new_user_cap():
    database_service = DatabaseService("sqlite:///:memory:")
    service = OutboundCampaignService(database_service=database_service)

    leads = [
        {"name": f"New {i}", "context": "learning software engineering", "is_new": True}
        for i in range(51)
    ] + [
        {"name": "Existing", "context": "still exploring", "is_new": False}
    ]

    result = service.run_batch(leads, now=datetime(2026, 8, 3, 10, 0, 0), dry_run=True)

    assert result["new_user_count"] == 50
    assert result["follow_up_count"] == 1
    assert result["sent_count"] == 51
