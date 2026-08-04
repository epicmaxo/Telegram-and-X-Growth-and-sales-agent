import asyncio

from src.social.asset_manager import AssetManager
from src.social.x_client import XClient


def test_x_client_reports_configuration_state():
    client = XClient(api_key=None, api_secret=None, access_token=None, access_token_secret=None)
    status = client.get_status()

    assert status["configured"] is False
    assert status["mode"] == "x"


def test_asset_manager_downloads_assets_to_local_dir(tmp_path):
    manager = AssetManager(base_dir=str(tmp_path))
    result = manager.download_mentrast_assets()

    assert result["status"] == "ready"
    assert len(result["assets"]) == 2
    assert any(asset["name"] == "logo" for asset in result["assets"])


def test_x_client_rewrites_hypey_content_with_guardrails():
    client = XClient(api_key="a", api_secret="b", access_token="c", access_token_secret="d")
    result = asyncio.run(client.post_tweet("Everyone should buy this now guaranteed"))

    assert result["status"] == "queued"
    assert "Mentrast" in result["message"]
