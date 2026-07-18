import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GROQ_API_KEY")

URL = "https://api.groq.com/openai/v1/chat/completions"

# Stores conversation history for each Telegram user
conversation_history = {}


def ask_ai(user_id, question):
    """
    Sends the user's conversation history to Groq so the AI
    remembers previous messages during the chat.
    """

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }

    # Create a new conversation if this user is chatting for the first time
    if user_id not in conversation_history:
        conversation_history[user_id] = [
            {
                "role": "system",
                "content": (
                    "You are AIHelperBot, a friendly customer support "
                    "assistant. Give clear, helpful, and concise answers. "
                    "Remember previous messages in the conversation and "
                    "respond naturally."
                ),
            }
        ]

    history = conversation_history[user_id]

    # Save the user's message
    history.append(
        {
            "role": "user",
            "content": question,
        }
    )

    data = {
        "model": "llama-3.1-8b-instant",
        "messages": history,
        "temperature": 0.7,
        "max_tokens": 1024,
    }

    try:
        response = requests.post(
            URL,
            headers=headers,
            json=data,
            timeout=30,
        )

        if response.status_code != 200:
            print("Status:", response.status_code)
            print("Response:", response.text)
            return f"❌ AI Error ({response.status_code})"

        result = response.json()

        reply = result["choices"][0]["message"]["content"]

        # Save AI reply
        history.append(
            {
                "role": "assistant",
                "content": reply,
            }
        )

        # Keep only the latest 20 user/assistant exchanges
        if len(history) > 41:
            conversation_history[user_id] = [history[0]] + history[-40:]

        return reply

    except requests.exceptions.RequestException as e:
        print(e)
        return "❌ Network error. Please try again."

    except Exception as e:
        print(e)
        return "❌ Something went wrong."