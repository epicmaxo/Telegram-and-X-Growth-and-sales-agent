from datetime import datetime, timedelta

from src.agent.outreach.service import OutboundCampaignService
from src.storage.database import DatabaseService


def test_cadence_prevents_too_many_messages_in_short_window():
    database_service = DatabaseService("sqlite:///:memory:")
    service = OutboundCampaignService(database_service=database_service)

    lead = {"name": "Ada", "context": "learning design", "is_new": True}
    now = datetime(2026, 8, 3, 10, 0, 0)

    result = service.run_batch([lead], now=now, dry_run=True)
    assert result["sent_count"] == 1

    result_2 = service.run_batch([lead], now=now + timedelta(minutes=2), dry_run=True)
    assert result_2["sent_count"] == 0
    assert result_2["skipped_count"] == 1
    assert result_2["reason"] == "cooldown"


def test_cadence_allows_follow_up_after_longer_delay():
    database_service = DatabaseService("sqlite:///:memory:")
    service = OutboundCampaignService(database_service=database_service)

    lead = {"name": "Grace", "context": "learning coding", "is_new": False}
    now = datetime(2026, 8, 3, 10, 0, 0)

    service.run_batch([lead], now=now, dry_run=False)
    result = service.run_batch([lead], now=now + timedelta(hours=25), dry_run=True)

    assert result["sent_count"] == 1
    assert result["reason"] == "ok"
