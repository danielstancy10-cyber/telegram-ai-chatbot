import logging
import subprocess
from pathlib import Path
from functools import lru_cache

import whisper

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _get_model() -> whisper.Whisper:
    """
    Load the Whisper model exactly once, on first use (not at import time).
    Cached via lru_cache so subsequent calls return the same instance.
    """
    logger.info("Loading Whisper 'base' model — this may take a moment…")
    return whisper.load_model("base")


def speech_to_text(input_file: str) -> str:
    """
    Convert a Telegram .ogg voice file to text using OpenAI Whisper.

    Steps:
        1. Convert input .ogg → a uniquely named .wav via ffmpeg.
        2. Transcribe the .wav with Whisper.
        3. Delete the .wav regardless of success or failure.

    Args:
        input_file: Path to the .ogg file downloaded from Telegram.

    Returns:
        Transcribed text string, or empty string on failure.

    Raises:
        RuntimeError: If ffmpeg conversion fails.
        FileNotFoundError: If ffmpeg is not installed.
    """
    input_path  = Path(input_file)
    # Derive a unique WAV name from the input filename to avoid collisions.
    output_path = input_path.with_suffix(".wav")

    try:
        # ── Step 1: Convert ogg → wav ─────────────────────────────────────
        result = subprocess.run(
            [
                "ffmpeg",
                "-y",          # overwrite output without asking
                "-i", str(input_path),
                str(output_path),
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,  # capture stderr so we can log errors
        )

        if result.returncode != 0:
            error_detail = result.stderr.decode(errors="replace").strip()
            logger.error("ffmpeg failed (code %d): %s", result.returncode, error_detail)
            raise RuntimeError(
                f"ffmpeg exited with code {result.returncode}: {error_detail}"
            )

        if not output_path.exists():
            raise FileNotFoundError(
                f"ffmpeg reported success but output file not found: {output_path}"
            )

        # ── Step 2: Transcribe ────────────────────────────────────────────
        model = _get_model()
        transcription = model.transcribe(str(output_path))
        text: str = transcription.get("text", "").strip()

        logger.info(
            "Transcribed '%s' → %d characters", input_file, len(text)
        )
        return text

    except FileNotFoundError as err:
        # Re-raised so the caller knows ffmpeg is not installed.
        logger.error("ffmpeg not found — please install it: %s", err)
        raise

    except RuntimeError:
        raise

    except Exception as err:
        logger.exception(
            "Unexpected error during speech-to-text for '%s': %s",
            input_file,
            err,
        )
        return ""

    finally:
        # ── Step 3: Always clean up the WAV file ─────────────────────────
        if output_path.exists():
            try:
                output_path.unlink()
                logger.debug("Deleted temporary WAV file: %s", output_path)
            except OSError as cleanup_err:
                logger.warning(
                    "Could not delete temporary file '%s': %s",
                    output_path,
                    cleanup_err,
                )