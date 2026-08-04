import os


class Settings:
    app_name: str = "mentrast-growth-intelligence"
    telegram_api_id: str | None = os.getenv("TELEGRAM_API_ID")
    telegram_api_hash: str | None = os.getenv("TELEGRAM_API_HASH")
    telegram_phone: str | None = os.getenv("TELEGRAM_PHONE")
    telegram_session_path: str | None = os.getenv("TELEGRAM_SESSION_PATH", "./sessions/telegram_account")
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    azure_openai_api_key: str | None = os.getenv("AZURE_OPENAI_API_KEY")
    azure_openai_endpoint: str | None = os.getenv("AZURE_OPENAI_ENDPOINT")
    azure_openai_deployment_name: str | None = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
    azure_openai_api_version: str | None = os.getenv("AZURE_OPENAI_API_VERSION")
    automation_sleep_minutes: int = int(os.getenv("AUTOMATION_SLEEP_MINUTES", "30"))
    automation_idle_threshold: int = int(os.getenv("AUTOMATION_IDLE_THRESHOLD", "3"))
