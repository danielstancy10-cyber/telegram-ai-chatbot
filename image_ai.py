import os
import requests
from dotenv import load_dotenv

load_dotenv()

HF_API_KEY = os.getenv("HF_API_KEY")

API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"

headers = {
    "Authorization": f"Bearer {HF_API_KEY}"
}


def generate_image(prompt):
    try:
        response = requests.post(
            API_URL,
            headers=headers,
            json={"inputs": prompt},
            timeout=120
        )

        response.raise_for_status()

        image_path = "generated_image.png"

        with open(image_path, "wb") as f:
            f.write(response.content)

        return image_path

    except requests.exceptions.RequestException as e:
        print("Image generation error:")
        print(e)
        return None