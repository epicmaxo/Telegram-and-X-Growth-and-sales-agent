from src.agent.outreach.service import OutboundCampaignService


def test_daily_content_plan_prioritizes_edtech_and_volume():
    service = OutboundCampaignService()
    plan = service.build_daily_content_plan(audience="global learners")

    assert plan["reply_posts"] >= 100
    assert plan["direct_posts"] >= 10
    assert "edtech" in plan["reply_theme"].lower()
    assert "mentrast" in plan["direct_example"].lower()
    assert "global learners" in plan["direct_example"].lower() or "people" in plan["direct_example"].lower()


def test_start_daily_cycle_enforces_capped_volume():
    service = OutboundCampaignService()
    started = service.start_daily_cycle(audience="global learners")

    assert started["status"] == "started"
    assert started["reply_posts_limit"] == 100
    assert started["direct_posts_limit"] == 10
    assert started["reply_posts_remaining"] == 100
    assert started["direct_posts_remaining"] == 10

    assert service.dispatch_activity("reply")["status"] == "queued"
    for _ in range(10):
        assert service.dispatch_activity("direct")["status"] == "queued"
    assert service.dispatch_activity("direct")["status"] == "blocked"
