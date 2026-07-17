import os
import uuid
import logging
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# ── Configuration ──────────────────────────────────────────────────────────────

_HF_API_KEY: str | None = os.getenv("HF_API_KEY")

_API_URL: str = (
    "https://api-inference.huggingface.co/models/"
    "stabilityai/stable-diffusion-xl-base-1.0"
)

# Directory where generated images are saved temporarily.
# Uses the system temp dir by default; override via IMAGE_OUTPUT_DIR env var.
_OUTPUT_DIR: Path = Path(os.getenv("IMAGE_OUTPUT_DIR", "."))


def _get_headers() -> dict[str, str]:
    """
    Build request headers at call time so that a missing key is caught
    immediately rather than silently sending 'Bearer None'.
    """
    if not _HF_API_KEY:
        raise EnvironmentError(
            "HF_API_KEY environment variable is not set. "
            "Image generation is unavailable."
        )
    return {
        "Authorization": f"Bearer {_HF_API_KEY}",
        "Content-Type": "application/json",
    }


def generate_image(prompt: str) -> str:
    """
    Generate an image from *prompt* using the Hugging Face Inference API
    (Stable Diffusion XL).

    Saves the result to a uniquely named PNG file so concurrent calls
    from different users never overwrite each other.

    Args:
        prompt: Natural-language description of the desired image.

    Returns:
        Absolute path string of the saved PNG file.

    Raises:
        EnvironmentError: If HF_API_KEY is not configured.
        requests.exceptions.RequestException: On any HTTP / network error.
        ValueError: If the API returns a non-image response body.
    """
    # ── Guard: API key must be present ────────────────────────────────────────
    headers = _get_headers()

    # ── Unique output path — one file per call, no collisions ─────────────────
    unique_name  = f"generated_{uuid.uuid4().hex}.png"
    image_path   = _OUTPUT_DIR / unique_name

    logger.info("Requesting image generation for prompt: %.80s…", prompt)

    try:
        response = requests.post(
            _API_URL,
            headers=headers,
            json={"inputs": prompt},
            timeout=120,
        )

        # ── Surface HTTP errors with full context ──────────────────────────────
        if response.status_code != 200:
            error_body = response.text[:500]          # truncate huge HTML pages
            logger.error(
                "Image API returned HTTP %d: %s",
                response.status_code,
                error_body,
            )
            response.raise_for_status()               # raises HTTPError

        # ── Validate content type — API returns JSON on model-loading delays ───
        content_type = response.headers.get("Content-Type", "")
        if "image" not in content_type:
            # The model is still loading; the body is a JSON error message.
            error_detail = response.text[:300]
            logger.warning(
                "Unexpected Content-Type '%s'. Body: %s",
                content_type,
                error_detail,
            )
            raise ValueError(
                f"Expected image response but got '{content_type}'. "
                "The model may still be loading — please try again in 20 seconds."
            )

        # ── Write image bytes to disk ──────────────────────────────────────────
        _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        image_path.write_bytes(response.content)

        logger.info(
            "Image saved to '%s' (%d bytes).",
            image_path,
            len(response.content),
        )
        return str(image_path)

    except EnvironmentError:
        raise

    except ValueError:
        raise

    except requests.exceptions.RequestException as err:
        logger.error("Image generation request failed: %s", err, exc_info=True)
        raise

    except OSError as err:
        logger.error(
            "Failed to write image to disk at '%s': %s", image_path, err, exc_info=True
        )
        raise