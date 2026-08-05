import os
import sys

# Add project root to sys.path
sys.path.append(r"c:\\Users\\REV.STEPHEN OKA\\Telegram-and-X-Growth-and-sales-agent")

from src.agent.conversation.service import ConversationService

def main():
    service = ConversationService()
    print("\n--- Interactive AI Chat (type 'exit' to quit) ---\n")
    while True:
        user_msg = input("You: ")
        if user_msg.lower() in ("exit", "quit"):
            print("Goodbye!")
            break
        reply = service.draft_response(user_msg)
        if not reply:
            print("[AI dropped the conversation]")
        else:
            print(f"AI: {reply}")

if __name__ == "__main__":
    main()
