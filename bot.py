import os
import re
import logging
import asyncio
from typing import Final, NoReturn
from enum import StrEnum
from pathlib import Path
from dotenv import load_dotenv
from database.migrations import run_migrations
from telegram import Update, ReplyKeyboardMarkup
from telegram.constants import ChatAction
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from telegram.error import TelegramError

# ── Third-party business logic imports ────────────────────────────────────────
from ai import ask_ai
from translator import translate
from database import save_lead
from voice import speech_to_text
from image_ai import generate_image
from database.repository import create_user

# ── Handler imports ────────────────────────────────────────────────────────────
from handlers.profile import profile
from handlers.membership import membership
from handlers.settings import settings
from handlers.notifications import notifications

# =============================================================================
# CONFIGURATION & LOGGING
# =============================================================================

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("AIHelperBot")

BOT_TOKEN: Final[str] = os.getenv("BOT_TOKEN", "")
if not BOT_TOKEN:
    logger.critical("BOT_TOKEN environment variable is missing.")
    raise ValueError("BOT_TOKEN environment variable must be specified.")

MAX_TELEGRAM_MESSAGE_LENGTH: Final[int] = 4096
EMAIL_REGEX: Final[re.Pattern[str]] = re.compile(
    r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
)

# =============================================================================
# ENUMS & CONSTANTS
# =============================================================================


class BotState(StrEnum):
    """Conversation flow states."""
    IDLE                = "IDLE"
    WAITING_NAME        = "WAITING_NAME"
    WAITING_EMAIL       = "WAITING_EMAIL"
    WAITING_IMAGE_PROMPT = "WAITING_IMAGE_PROMPT"


class Language(StrEnum):
    """Supported localizations."""
    ENGLISH = "English"
    FRENCH  = "French"
    SPANISH = "Spanish"
    ARABIC  = "Arabic"
    YORUBA  = "Yoruba"
    HAUSA   = "Hausa"
    IGBO    = "Igbo"


LANGUAGES_LIST: Final[list[str]] = [lang.value for lang in Language]

# =============================================================================
# KEYBOARDS
# =============================================================================

MAIN_KEYBOARD: Final[ReplyKeyboardMarkup] = ReplyKeyboardMarkup(
    [
        ["🤖 Ask AI",       "🌍 Language"],
        ["🛍 Products",     "❓ FAQs"],
        ["📞 Contact",      "🎨 Generate Image"],
        ["🎤 Voice Chat"],
    ],
    resize_keyboard=True,
    is_persistent=True,
)

LANGUAGE_KEYBOARD: Final[ReplyKeyboardMarkup] = ReplyKeyboardMarkup(
    [
        ["English", "French"],
        ["Spanish", "Arabic"],
        ["Yoruba",  "Hausa"],
        ["Igbo"],
    ],
    resize_keyboard=True,
)

# =============================================================================
# UTILITIES
# =============================================================================


def validate_email(email: str) -> bool:
    """Return True if *email* passes the RFC-ish regex check."""
    return bool(EMAIL_REGEX.match(email))


def split_message_text(
    text: str,
    max_size: int = MAX_TELEGRAM_MESSAGE_LENGTH,
) -> list[str]:
    """
    Split *text* into chunks that fit within Telegram's message size limit
    without breaking words.
    """
    if len(text) <= max_size:
        return [text]

    chunks: list[str] = []
    while text:
        if len(text) <= max_size:
            chunks.append(text)
            break

        split_index = text.rfind("\n", 0, max_size)
        if split_index == -1:
            split_index = text.rfind(" ", 0, max_size)
        if split_index == -1:
            split_index = max_size

        chunks.append(text[:split_index].strip())
        text = text[split_index:].strip()

    return chunks


async def safe_file_cleanup(file_path: str | Path) -> None:
    """Delete a temporary file without raising on failure."""
    try:
        path = Path(file_path)
        if path.exists():
            await asyncio.to_thread(path.unlink, missing_ok=True)
            logger.info("Cleaned up temporary file: %s", file_path)
    except Exception as err:
        logger.error("Could not delete '%s': %s", file_path, err, exc_info=True)


async def execute_ai_pipeline_with_retry(
    prompt: str,
    target_lang: str,
    retries: int = 2,
) -> str:
    """
    Call the AI backend, translate the result, and retry up to *retries* times
    on transient failures.
    """
    last_error: Exception | None = None

    for attempt in range(1, retries + 2):
        try:
            raw_output = await asyncio.to_thread(ask_ai, prompt)
            if not raw_output or not raw_output.strip():
                raise ValueError("AI engine returned an empty response.")

            translated = await asyncio.to_thread(translate, raw_output, target_lang)
            return translated

        except Exception as err:
            last_error = err
            logger.warning(
                "AI pipeline attempt %d/%d failed: %s",
                attempt,
                retries + 1,
                err,
            )
            if attempt <= retries:
                await asyncio.sleep(1.0 * attempt)

    logger.error("All AI pipeline retries exhausted.")
    raise last_error  # type: ignore[misc]

# =============================================================================
# COMMAND HANDLERS
# =============================================================================


async def start_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Register the user and display the main menu."""
    if not update.message:
        return

    tg_user = update.effective_user
    user_id = tg_user.id if tg_user else 0
    logger.info("User %s triggered /start", user_id)

    if tg_user:
        try:
            # create_user may be sync or async — handle both.
            result = create_user(
                telegram_id=tg_user.id,
                username=tg_user.username,
                full_name=tg_user.full_name,
            )
            # Await if the implementation is a coroutine.
            if asyncio.iscoroutine(result):
                await result
            logger.info("User %s saved to database.", tg_user.id)
        except Exception as err:
            logger.exception("Failed to save user %s: %s", user_id, err)

    context.user_data.clear()
    context.user_data["state"]    = BotState.IDLE
    context.user_data["language"] = Language.ENGLISH.value

    await update.message.reply_text(
        "👋 *Welcome to AIHelperBot!*\n\n"
        "I am your smart support assistant.\n\n"
        "Select an option from the menu below to get started.",
        reply_markup=MAIN_KEYBOARD,
        parse_mode="Markdown",
    )

# =============================================================================
# MESSAGE HANDLERS
# =============================================================================


async def handle_incoming_voice(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Transcribe a voice message and respond via the AI pipeline."""
    if not update.message or not update.message.voice:
        return

    tg_user    = update.effective_user
    user_id    = tg_user.id if tg_user else 0
    message_id = update.message.message_id
    voice_path = f"transient_audio_{user_id}_{message_id}.ogg"

    logger.info("Voice message received from user %s", user_id)

    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,  # type: ignore[union-attr]
        action=ChatAction.TYPING,
    )
    status_msg = await update.message.reply_text(
        "🎤 Processing your voice message, please wait…"
    )

    try:
        voice_file = await context.bot.get_file(update.message.voice.file_id)
        await voice_file.download_to_drive(voice_path)

        transcribed = await asyncio.to_thread(speech_to_text, voice_path)

        if not transcribed or not transcribed.strip():
            await status_msg.edit_text(
                "❌ Could not transcribe your audio. Please try again."
            )
            return

        await status_msg.edit_text(
            f"🗣 *You said:*\n\n_{transcribed.strip()}_",
            parse_mode="Markdown",
        )

        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,  # type: ignore[union-attr]
            action=ChatAction.TYPING,
        )
        thinking_msg = await update.message.reply_text("🤖 Thinking…")

        lang   = context.user_data.get("language", Language.ENGLISH.value)
        reply  = await execute_ai_pipeline_with_retry(transcribed, lang)
        chunks = split_message_text(reply)

        await thinking_msg.delete()
        for chunk in chunks:
            await update.message.reply_text(chunk)

    except Exception as err:
        logger.error("Voice handler error for user %s: %s", user_id, err, exc_info=True)
        await update.message.reply_text(
            "❌ An error occurred while processing your voice message."
        )
    finally:
        await safe_file_cleanup(voice_path)


async def handle_incoming_text(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Route text messages based on current conversation state and button presses."""
    if not update.message or not update.message.text:
        return

    tg_user       = update.effective_user
    user_id       = tg_user.id if tg_user else 0
    raw_input     = update.message.text.strip()
    current_state = context.user_data.get("state", BotState.IDLE)
    lang          = context.user_data.get("language", Language.ENGLISH.value)

    logger.info("Text from user %s | state=%s", user_id, current_state)

    # ── Conversation state machine ────────────────────────────────────────────

    if current_state == BotState.WAITING_NAME:
        context.user_data["lead_name"] = raw_input
        context.user_data["state"]     = BotState.WAITING_EMAIL
        await update.message.reply_text(
            "📧 Please enter your email address:"
        )
        return

    if current_state == BotState.WAITING_EMAIL:
        if not validate_email(raw_input):
            await update.message.reply_text(
                "❌ That doesn't look like a valid email address.\n"
                "Please try again (e.g. name@example.com)."
            )
            return

        lead_name = context.user_data.get("lead_name", "Anonymous")

        try:
            result = save_lead(lead_name, raw_input)
            if asyncio.iscoroutine(result):
                await result
            logger.info("Lead saved: %s <%s>", lead_name, raw_input)
            await update.message.reply_text(
                "✅ *Information Captured!*\n\n"
                "Thank you — our team will be in touch shortly.",
                reply_markup=MAIN_KEYBOARD,
                parse_mode="Markdown",
            )
        except Exception as err:
            logger.error("Failed to save lead: %s", err, exc_info=True)
            await update.message.reply_text(
                "❌ Failed to save your details. Please try again later.",
                reply_markup=MAIN_KEYBOARD,
            )
        finally:
            context.user_data["state"] = BotState.IDLE
            context.user_data.pop("lead_name", None)
        return

    if current_state == BotState.WAITING_IMAGE_PROMPT:
        context.user_data["state"] = BotState.IDLE

        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,  # type: ignore[union-attr]
            action=ChatAction.UPLOAD_PHOTO,
        )
        status_msg = await update.message.reply_text(
            "🎨 Generating your image, please wait…"
        )

        generated_path: str | None = None
        try:
            generated_path = await asyncio.to_thread(generate_image, raw_input)

            if generated_path and Path(generated_path).exists():
                with open(generated_path, "rb") as img_file:
                    await update.message.reply_photo(
                        photo=img_file,
                        caption=(
                            f"🎨 *Generated Image*\n"
                            f'_Prompt:_ "{raw_input}"'
                        ),
                        reply_markup=MAIN_KEYBOARD,
                        parse_mode="Markdown",
                    )
                await status_msg.delete()
            else:
                raise FileNotFoundError(
                    "Image generation succeeded but output file is missing."
                )
        except Exception as err:
            logger.error(
                "Image generation error for user %s: %s", user_id, err, exc_info=True
            )
            await status_msg.edit_text(
                "❌ Image generation failed. Please try again later."
            )
        finally:
            if generated_path:
                await safe_file_cleanup(generated_path)
        return

    # ── Static button routing ─────────────────────────────────────────────────

    if raw_input == "🌍 Language":
        await update.message.reply_text(
            "🌍 Choose your language:",
            reply_markup=LANGUAGE_KEYBOARD,
        )
        return

    if raw_input in LANGUAGES_LIST:
        context.user_data["language"] = raw_input
        await update.message.reply_text(
            f"✅ Language changed to *{raw_input}*.",
            reply_markup=MAIN_KEYBOARD,
            parse_mode="Markdown",
        )
        return

    if raw_input == "🛍 Products":
        await update.message.reply_text(
            "🛍 *Our Products*\n\n"
            "👕 *Premium Hoodie* — Thermal insulation garment.\n"
            "👟 *Sneakers* — Impact-absorption training models.\n"
            "🧥 *Jackets* — Weather-resilient outdoor gear.",
            parse_mode="Markdown",
        )
        return

    if raw_input == "❓ FAQs":
        await update.message.reply_text(
            "❓ *Frequently Asked Questions*\n\n"
            "🚚 *Shipping:* 3–7 business days worldwide.\n"
            "💳 *Payment:* Visa, Mastercard, PayPal accepted.\n"
            "🔄 *Returns:* 30-day return window guaranteed.",
            parse_mode="Markdown",
        )
        return

    if raw_input == "📞 Contact":
        context.user_data["state"] = BotState.WAITING_NAME
        await update.message.reply_text(
            "👤 Let's get your details.\n\nPlease enter your full name:"
        )
        return

    if raw_input == "🎨 Generate Image":
        context.user_data["state"] = BotState.WAITING_IMAGE_PROMPT
        await update.message.reply_text(
            "🎨 *Image Generation Active*\n\n"
            "Describe the image you want me to generate:",
            parse_mode="Markdown",
        )
        return

    if raw_input == "🎤 Voice Chat":
        await update.message.reply_text(
            "🎤 *Voice Chat Ready*\n\n"
            "Send me a voice message and I will transcribe and respond to it.",
            parse_mode="Markdown",
        )
        return

    if raw_input == "🤖 Ask AI":
        await update.message.reply_text(
            "🤖 *Ask me anything!*\n\n"
            "Type your question and I will answer it.",
            parse_mode="Markdown",
        )
        return

    # ── Default: AI inference ─────────────────────────────────────────────────

    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,  # type: ignore[union-attr]
        action=ChatAction.TYPING,
    )
    thinking_msg = await update.message.reply_text("🤖 Thinking…")

    try:
        response   = await execute_ai_pipeline_with_retry(raw_input, lang)
        chunks     = split_message_text(response)
        await thinking_msg.delete()
        for chunk in chunks:
            await update.message.reply_text(chunk)

    except Exception as err:
        logger.error(
            "AI inference error for user %s: %s", user_id, err, exc_info=True
        )
        await thinking_msg.edit_text(
            "❌ Sorry, I could not process your request. Please try again."
        )

# =============================================================================
# ERROR HANDLER
# =============================================================================


async def global_error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Log all unhandled exceptions and notify the user where possible."""
    logger.error(
        "Unhandled exception: %s", context.error, exc_info=context.error
    )

    if (
        isinstance(update, Update)
        and update.message
    ):
        try:
            await update.message.reply_text(
                "❌ An unexpected error occurred. Please try again later.",
                reply_markup=MAIN_KEYBOARD,
            )
        except TelegramError as tg_err:
            logger.critical("Failed to send error reply: %s", tg_err)

# =============================================================================
# APPLICATION ENTRYPOINT
# =============================================================================


def main() -> NoReturn:
    """Build the application, register all handlers, and start polling."""
    logger.info("Starting AIHelperBot...")

    # Run database migrations before starting the bot
    logger.info("Running database migrations...")
    run_migrations()

    # Build the Telegram application
    runtime_application = Application.builder().token(BOT_TOKEN).build()

    # ── Command handlers ───────────────────────────────────────────────────────
    runtime_application.add_handler(CommandHandler("start", start_command))
    runtime_application.add_handler(CommandHandler("profile", profile))
    runtime_application.add_handler(CommandHandler("membership", membership))
    runtime_application.add_handler(CommandHandler("settings", settings))
    runtime_application.add_handler(CommandHandler("notifications", notifications))

    # ── Message handlers ───────────────────────────────────────────────────────
    runtime_application.add_handler(
        MessageHandler(filters.VOICE, handle_incoming_voice)
    )
    runtime_application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_incoming_text)
    )

    # ── Error handler ──────────────────────────────────────────────────────────
    runtime_application.add_error_handler(global_error_handler)

    print("=" * 50)
    print("🤖 AIHelperBot is running...")
    print("✅ Groq AI Enabled")
    print("✅ Multi-language Enabled")
    print("✅ Voice Chat Enabled")
    print("✅ AI Image Generation Enabled")
    print("✅ Contact Form Enabled")
    print("✅ Database Enabled")
    print("=" * 50)

    logger.info("Bot is now polling for updates.")
    runtime_application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()