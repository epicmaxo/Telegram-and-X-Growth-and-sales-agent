# Open Source Growth Agent

A backend-only MVP for conversational customer discovery and relationship intelligence, with Telegram as the first channel.

## What is included

- FastAPI service with health and conversation endpoints
- Telegram webhook adapter and Telethon client for user-account operations
- Conversation analysis and draft-response service
- Opportunity and outcome evaluation services
- Prompt files for LLM-driven analysis and response generation
- Environment-based configuration for secrets
- Single-user password protection for the web dashboard

## Run locally

1. Install dependencies:
   python -m pip install -r requirements.txt
2. Start the API:
   python -m uvicorn src.main:app --host 0.0.0.0 --port 8000
3. Check the health endpoint:
   curl http://127.0.0.1:8000/health

## Environment Variables

- `TELEGRAM_API_ID`: Your Telegram API ID
- `TELEGRAM_API_HASH`: Your Telegram API Hash
- `TELEGRAM_PHONE`: Your Telegram Phone Number
- `TELEGRAM_SESSION_STRING`: Your generated Telegram string session
- `ADMIN_PASSWORD`: The password for accessing the dashboard (default is `Mrnaijad`)

## Notes

- Human approval is required for outbound messages in V1.
- The current implementation uses deterministic service logic as a backend-first MVP; LLM integration can be layered in later through the LLM service and prompt files.
