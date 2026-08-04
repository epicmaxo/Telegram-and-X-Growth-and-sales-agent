from src.telegram.client.real_client import RealTelegramClient


def test_real_client_reports_configuration_state():
    client = RealTelegramClient(api_id="123", api_hash="abc", phone="+2348000000000")

    status = client.get_status()

    assert status["configured"] is True
    assert status["mode"] == "user-account"
    assert status["api_id_present"] is True
