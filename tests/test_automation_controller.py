from src.automation.controller import AutomationController


def test_controller_wakes_on_activity_and_sleeps_after_idle():
    controller = AutomationController(sleep_minutes=30, idle_threshold=2)

    assert controller.mark_channel_activity("telegram", activity="message")["status"] == "awake"
    assert controller.tick()["status"] == "awake"
    assert controller.tick()["status"] == "sleeping"

    controller.mark_channel_activity("x", activity="reply")
    assert controller.get_status()["status"] == "awake"
