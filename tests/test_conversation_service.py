import pytest

from src.agent.conversation.service import ConversationService


@pytest.fixture
def conversation_service():
    return ConversationService()


def test_analyze_message_extracts_key_fields(conversation_service):
    result = conversation_service.analyze_message(
        "I want to become a software engineer. I mostly learn from YouTube and random tutorials. I feel lost because I don't know where to start."
    )

    assert result.goal == "become a software engineer"
    assert result.current_learning_method == "YouTube and random tutorials"
    assert result.stated_problem == "I don't know where to start"
    assert result.mentrast_fit == "high"
    assert result.conversation_stage == "GOAL_DISCOVERY"
    assert result.recommended_action == "Ask what they want to become and how they currently learn"


def test_draft_response_avoids_premature_pitch(conversation_service):
    draft = conversation_service.draft_response(
        "I mostly watch YouTube and I feel lost. I don't know what to learn next.",
        stage="PROBLEM_DISCOVERY",
    )

    assert "YouTube" in draft
    assert "learn next" in draft.lower() or "what to learn" in draft.lower()
    assert "mentrast" in draft.lower()
    assert len(draft.split()) <= 35


def test_draft_response_uses_simple_human_tone(conversation_service):
    draft = conversation_service.draft_response(
        "I am overwhelmed by all the advice online.",
        stage="PROBLEM_DISCOVERY",
    )

    assert "I" in draft or "you" in draft.lower()
    assert "overwhelmed" in draft.lower() or "confusing" in draft.lower()
    assert "mentrast" in draft.lower()
