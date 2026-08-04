from src.agent.feedback.service import FeedbackService


def test_feedback_service_classifies_negative_feedback():
    service = FeedbackService()

    result = service.evaluate("No, I am not interested right now")

    assert result.feedback_received is True
    assert result.summary == "negative feedback"
    assert result.next_action == "pause and log the objection"
