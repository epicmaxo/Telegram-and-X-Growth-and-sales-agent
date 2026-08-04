from datetime import datetime

from src.agent.outreach.service import OutboundCampaignService
from src.storage.database import DatabaseService


def test_campaign_respects_daily_cap_and_schedule():
    database_service = DatabaseService("sqlite:///:memory:")
    service = OutboundCampaignService(database_service=database_service)

    leads = [
        {"name": f"Lead {i}", "context": "wants to learn software engineering"}
        for i in range(55)
    ]

    result = service.run_batch(leads, now=datetime(2026, 8, 3, 10, 0, 0), dry_run=True)

    assert result["sent_count"] == 50
    assert len(result["queued_messages"]) == 50
    assert result["skipped_count"] == 5
    assert "Mentrast" in result["queued_messages"][0]["message"]


def test_campaign_skips_outside_allowed_window():
    database_service = DatabaseService("sqlite:///:memory:")
    service = OutboundCampaignService(database_service=database_service)

    result = service.run_batch([
        {"name": "Ada", "context": "trying to learn design"}
    ], now=datetime(2026, 8, 3, 23, 0, 0), dry_run=True)

    assert result["sent_count"] == 0
    assert len(result["queued_messages"]) == 0
    assert result["skipped_count"] == 1
    assert result["reason"] == "outside_allowed_window"
