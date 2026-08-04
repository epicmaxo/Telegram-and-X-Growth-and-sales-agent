from datetime import datetime, timedelta

from src.agent.relationship.service import RelationshipManager


def test_relationship_manager_blocks_after_no_and_recommends_pacing():
    manager = RelationshipManager()

    reply = manager.build_persona_reply("user-1", "No thanks, leave me alone")
    assert "leave it there" in reply.lower()
    assert manager.should_engage("user-1") is False

    manager.record_interaction("user-2", channel="telegram", outcome="active", message="I want to learn coding")
    assert manager.should_engage("user-2", now=datetime.now() + timedelta(hours=13)) is True
