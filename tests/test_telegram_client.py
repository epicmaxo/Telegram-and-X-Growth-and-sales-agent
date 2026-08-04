from src.telegram.client.client import TelegramAccountClient


def test_client_reports_missing_credentials():
    client = TelegramAccountClient(api_id=None, api_hash=None)

    status = client.get_status()

    assert status["configured"] is False
    assert "api_id" in status["missing"]
    assert "api_hash" in status["missing"]


def test_client_reports_telethon_dependency_state():
    client = TelegramAccountClient(api_id="123", api_hash="abc", phone="+2348000000000")

    status = client.get_status()

    assert "telethon_installed" in status
    assert isinstance(status["telethon_installed"], bool)
