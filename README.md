# Mentrast Growth Intelligence

A backend-only MVP for conversational customer discovery and relationship intelligence for Mentrast, with Telegram as the first channel.

## What is included

- FastAPI service with health and conversation endpoints
- Telegram webhook adapter
- Conversation analysis and draft-response service
- Opportunity and outcome evaluation services
- Prompt files for LLM-driven analysis and response generation
- Environment-based configuration for secrets

## Run locally

1. Install dependencies:
   python -m pip install -r requirements.txt
2. Start the API:
   python -m uvicorn src.main:app --host 0.0.0.0 --port 8000
3. Check the health endpoint:
   curl http://127.0.0.1:8000/health

## Key endpoints

- GET /health
- POST /webhooks/telegram
- GET /opportunities
- POST /conversations/{conversation_id}/analyze
- POST /conversations/{conversation_id}/draft
- POST /conversations/{conversation_id}/outcome

## Notes

- Human approval is required for outbound messages in V1.
- The current implementation uses deterministic service logic as a backend-first MVP; GPT-4.0 integration can be layered in later through the LLM service and prompt files.
