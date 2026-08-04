from src.agent.outreach.service import OutboundCampaignService


def test_outreach_service_gives_conversation_ready_posts():
    service = OutboundCampaignService()
    post = service.build_social_post(topic="learn a new skill", audience="people who feel stuck")
    reply = service.build_social_reply("That is a fair point", audience="people who feel stuck")

    assert "clear" in post.lower() or "practical" in post.lower()
    assert len(post.split()) <= 30
    assert "mentrast" in reply.lower() or "practical" in reply.lower()
    assert len(reply.split()) <= 30


def test_outreach_service_suggests_non_stock_images():
    service = OutboundCampaignService()
    strategy = service.suggest_image_strategy(topic="learning a new skill")

    assert any("stock" in item.lower() for item in strategy)
    assert any("real photo" in item.lower() or "screen recording" in item.lower() for item in strategy)
