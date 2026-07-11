import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GROQ_API_KEY")

URL = "https://api.groq.com/openai/v1/chat/completions"


def ask_ai(question):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are AIHelperBot, a friendly customer support "
                    "assistant. Give clear, helpful, and concise answers."
                )
            },
            {
                "role": "user",
                "content": question
            }
        ],
        "temperature": 0.7,
        "max_tokens": 1024
    }

    try:
        response = requests.post(
            URL,
            headers=headers,
            json=data,
            timeout=30
        )

        # Show errors in the terminal while testing
        if response.status_code != 200:
            print("Status:", response.status_code)
            print("Response:", response.text)
            return f"❌ AI Error ({response.status_code})"

        result = response.json()

        return result["choices"][0]["message"]["content"]

    except requests.exceptions.RequestException as e:
        print(e)
        return "❌ Network error. Please try again."

    except Exception as e:
        print(e)
        return "❌ Something went wrong."