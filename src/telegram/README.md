# Telegram account integration

This service is designed for a Telegram user account, not a bot.

## Required environment variables

Set these before running the service:

- TELEGRAM_API_ID
- TELEGRAM_API_HASH
- TELEGRAM_PHONE
- TELEGRAM_SESSION_PATH (optional)

## How to use it

1. Install dependencies:
   python -m pip install -r requirements.txt
2. Start the service:
   python -m uvicorn src.main:app --host 0.0.0.0 --port 8000
3. Check the account status:
   curl http://127.0.0.1:8000/telegram/status
4. Run the connect flow:
   curl -X POST http://127.0.0.1:8000/telegram/connect
5. Read chat history from a group or conversation:
   curl "http://127.0.0.1:8000/telegram/chats/<chat_id>/history?limit=20"
6. Send a new message through the account:
   curl -X POST "http://127.0.0.1:8000/telegram/messages/send?chat_id=<chat_id>&message=Hello"

## Important notes

- This is a user-account integration, so it uses Telegram's account-based client flow.
- In V1, human approval is still required before sending messages.
- The current implementation uses a safe stubbed layer until the real Telegram client session is created.
