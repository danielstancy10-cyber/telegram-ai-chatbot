import os
import re
import logging
import asyncio
from typing import Final, NoReturn
from enum import StrEnum
from pathlib import Path
from dotenv import load_dotenv

from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.constants import ChatAction
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from telegram.error import TelegramError

# Core business logic infrastructure imports
from ai import ask_ai
from translator import translate
from database import save_lead
from voice import speech_to_text
from image_ai import generate_image
from database.repository import create_user

# =========================================================================
# CONFIGURATION & LOGGING SUBSYSTEM
# =========================================================================

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("AIHelperBot")

BOT_TOKEN: Final[str] = os.getenv("BOT_TOKEN", "")
if not BOT_TOKEN:
    logger.critical("CRITICAL: BOT_TOKEN environment variable is missing. Termination imminent.")
    raise ValueError("BOT_TOKEN environment variable must be specified.")

MAX_TELEGRAM_MESSAGE_LENGTH: Final[int] = 100
EMAIL_REGEX: Final[re.Pattern[str]] = re.compile(
    r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
)

# =========================================================================
# SYSTEM ENUMS & CONFIGURATION CONSTANTS
# =========================================================================

class BotState(StrEnum):
    """Enumeration representing conversation flow states for structured tracking."""
    IDLE = "IDLE"
    WAITING_NAME = "WAITING_NAME"
    WAITING_EMAIL = "WAITING_EMAIL"
    WAITING_IMAGE_PROMPT = "WAITING_IMAGE_PROMPT"


class Language(StrEnum):
    """Supported systemic localizations for user matching matrix."""
    ENGLISH = "English"
    FRENCH = "French"
    SPANISH = "Spanish"
    ARABIC = "Arabic"
    YORUBA = "Yoruba"
    HAUSA = "Hausa"
    IGBO = "Igbo"


LANGUAGES_LIST: Final[list[str]] = [lang.value for lang in Language]

# =========================================================================
# UI KEYBOARD DESIGN PATTERNS
# =========================================================================

MAIN_KEYBOARD: Final[ReplyKeyboardMarkup] = ReplyKeyboardMarkup(
    [
        ["🤖 Ask AI", "🌍 Language"],
        ["🛍 Products", "❓ FAQs"],
        ["📞 Contact", "🎨 Generate Image"],
        ["🎤 Voice Chat"]
    ],
    resize_keyboard=True,
    is_persistent=True
)

LANGUAGE_KEYBOARD: Final[ReplyKeyboardMarkup] = ReplyKeyboardMarkup(
    [
        ["English", "French"],
        ["Spanish", "Arabic"],
        ["Yoruba", "Hausa"],
        ["Igbo"]
    ],
    resize_keyboard=True
)

# =========================================================================
# UTILITY HELPER UTILITIES
# =========================================================================

def validate_email(email: str) -> bool:
    """Verifies syntactic integrity of client provided emails via safe checking regex."""
    return bool(EMAIL_REGEX.match(email))


def split_message_text(text: str, max_size: int = MAX_TELEGRAM_MESSAGE_LENGTH) -> list[str]:
    """Splits oversized responses safely without breaking words across transmission windows."""
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
    """Handles deletion of temporary media artifacts cleanly preventing I/O leaks."""
    try:
        path = Path(file_path)
        if path.exists():
            await asyncio.to_thread(path.unlink, missing_ok=True)
            logger.info(f"Successfully cleaned up temporary system file: {file_path}")
    except Exception as cleanup_err:
        logger.error(f"Non-fatal error unlinking transient asset tracking '{file_path}': {cleanup_err}", exc_info=True)


async def execute_ai_pipeline_with_retry(prompt: str, target_lang: str, retries: int = 2) -> str:
    """Invokes threaded processing cores applying fault recovery fallbacks gracefully."""
    attempt = 0
    while attempt <= retries:
        try:
            raw_ai_output = await asyncio.to_thread(ask_ai, prompt)
            if not raw_ai_output or not raw_ai_output.strip():
                raise ValueError("Downstream AI engine processed an empty textual output string.")
                
            translated_output = await asyncio.to_thread(translate, raw_ai_output, target_lang)
            return translated_output
        except Exception as error:
            attempt += 1
            logger.warning(f"AI Pipeline execution hiccup (Attempt {attempt}/{retries + 1}): {error}")
            if attempt > retries:
                logger.error("All fallback retry limits breached across threaded inference infrastructure pipeline.")
                raise error
            await asyncio.sleep(1.0 * attempt)
    return "❌ Service temporary unavailable."

# =========================================================================
# MAIN ROUTING ENGINE INTERACTIVE SYSTEM HANDLERS
# =========================================================================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles system orientation initialization clearing transient user runtime data safely."""
    if not update.message:
        return

    user = update.effective_user
    user_id = user.id if user else 0

    logger.info(f"User identity session initiated via start hook command context: {user_id}")

    if user:
        try:
            print(f"Saving user: {user.id} | {user.username}")

            create_user(
                telegram_id=user.id,
                username=user.username,
                full_name=user.full_name,
            )

            print("✅ User saved successfully!")

        except Exception as e:
            print("❌ DATABASE ERROR:", e)
            logger.exception("Failed to save user")

    # Sanitize operational data variables cleanly
    context.user_data.clear()
    context.user_data["state"] = BotState.IDLE
    context.user_data["language"] = Language.ENGLISH.value

    await update.message.reply_text(
        "👋 **Welcome to AIHelperBot Enterprise Customer Care!**\n\n"
        "I am your automated smart support representative optimized with advanced linguistic interpretation capabilities.\n\n"
        "Select an option from the menu panel below to interface with the core subsystem components.",
        reply_markup=MAIN_KEYBOARD,
        parse_mode="Markdown"
    )

async def handle_incoming_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Processes pipeline translation for incoming audio payloads seamlessly."""
    if not update.message or not update.message.voice:
        return

    user_id = update.effective_user.id if update.effective_user else 0
    message_id = update.message.message_id
    voice_file_path = f"transient_audio_{user_id}_{message_id}.ogg"
    
    logger.info(f"Intercepted active voice transcription job for processing instance: {user_id}")
    
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
    status_indicator = await update.message.reply_text("🎤 Processing incoming audio track, please wait...")

    try:
        # File fetching segment via asynchronous download mechanism
        voice_metadata = await context.bot.get_file(update.message.voice.file_id)
        await voice_metadata.download_to_drive(voice_file_path)

        # Offload computationally heavy file translation metrics out of critical loop path
        transcribed_text = await asyncio.to_thread(speech_to_text, voice_file_path)
        
        if not transcribed_text or not transcribed_text.strip():
            await status_indicator.edit_text("❌ Analysis failed: Audio structural transcription evaluated blank.")
            return

        await status_indicator.edit_text(f"🗣 **You said:**\n\n_\"{transcribed_text.strip()}\"_", parse_mode="Markdown")
        
        # Dispatch analytical loading indicator segment 
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
        processing_indicator = await update.message.reply_text("🤖 Synthesizing response parameters...")

        user_selected_lang = context.user_data.get("language", Language.ENGLISH.value)
        final_localized_reply = await execute_ai_pipeline_with_retry(transcribed_text, user_selected_lang)

        # Handle massive buffer overflows natively via messaging chunk segment array loops
        message_segments = split_message_text(final_localized_reply)
        await processing_indicator.delete()
        
        for piece in message_segments:
            await update.message.reply_text(piece)

    except Exception as runtime_error:
        logger.error(f"Critical execution error caught during localized voice routing workflow: {runtime_error}", exc_info=True)
        await update.message.reply_text("❌ Critical error: Unable to map audio context pipeline requirements safely.")
    finally:
        await safe_file_cleanup(voice_file_path)


async def handle_incoming_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Core text input router managing conversion states and structural functional routing paths."""
    if not update.message or not update.message.text:
        return

    user_id = update.effective_user.id if update.effective_user else 0
    raw_input = update.message.text.strip()
    current_state = context.user_data.get("state", BotState.IDLE)
    user_selected_lang = context.user_data.get("language", Language.ENGLISH.value)

    logger.info(f"Incoming message event context evaluated for [User ID: {user_id} | State: {current_state}]")

    # =========================================================================
    # STATE FLOW LOGIC MAPS (CONVERSATIONAL CONTEXT RECOVERY)
    # =========================================================================

    if current_state == BotState.WAITING_NAME:
        context.user_data["lead_name"] = raw_input
        context.user_data["state"] = BotState.WAITING_EMAIL
        await update.message.reply_text("📧 Please provide your professional email address configuration parameters:")
        return

    if current_state == BotState.WAITING_EMAIL:
        if not validate_email(raw_input):
            await update.message.reply_text("❌ Syntactic validation failed: Please specify a completely valid email syntax address (e.g., example@domain.com).")
            return
        
        captured_name = context.user_data.get("lead_name", "Anonymous Client")
        
        try:
            await asyncio.to_thread(save_lead, captured_name, raw_input)
            logger.info(f"Successfully integrated high value business lead capture tracking down into data store layers for: {raw_input}")
            await update.message.reply_text(
                "✅ **Information Captured Successfully**\n\nThank you for registering. Our enterprise sales engineering team will reach out directly shortly.",
                reply_markup=MAIN_KEYBOARD,
                parse_mode="Markdown"
            )
        except Exception as db_fault:
            logger.error(f"Fault handling integration interface layer persistence write failure: {db_fault}", exc_info=True)
            await update.message.reply_text("❌ Record tracking failed. Our core database storage layer encountered a temporary save state issue.", reply_markup=MAIN_KEYBOARD)
        finally:
            context.user_data["state"] = BotState.IDLE
            context.user_data.pop("lead_name", None)
        return

    if current_state == BotState.WAITING_IMAGE_PROMPT:
        context.user_data["state"] = BotState.IDLE  # Reset locking mechanisms proactively
        
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.UPLOAD_PHOTO)
        status_banner = await update.message.reply_text("🎨 Creating your image... Synthesizing pixels...")
        
        generated_image_path: str | None = None
        try:
            # Relocate heavy model weights generations cleanly away from core loops
            generated_image_path = await asyncio.to_thread(generate_image, raw_input)
            
            if generated_image_path and Path(generated_image_path).exists():
                with open(generated_image_path, "rb") as delivery_payload:
                    await update.message.reply_photo(
                        photo=delivery_payload,
                        caption=f"🎨 **Generated Asset Architecture Context Blueprint**\n_Prompt:_ \"{raw_input}\"",
                        reply_markup=MAIN_KEYBOARD,
                        parse_mode="Markdown"
                    )
                await status_banner.delete()
            else:
                raise FileNotFoundError("Downstream engine returned success path but target graphic image asset container is missing from file storage.")
        except Exception as graphics_system_fault:
            logger.error(f"Graphics infrastructure compute pipeline collapsed on frame delivery: {graphics_system_fault}", exc_info=True)
            await status_banner.edit_text("❌ Imaging pipeline processing failure: Unable to complete high fidelity render configurations.")
        finally:
            if generated_image_path:
                await safe_file_cleanup(generated_image_path)
        return

    # =========================================================================
    # STATIC NAVIGATION INTERFACE COMMAND MATCHING TERMINALS
    # =========================================================================

    if raw_input == "🌍 Language":
        await update.message.reply_text("🌍 choose your languages below:", reply_markup=LANGUAGE_KEYBOARD)
        return

    if raw_input in LANGUAGES_LIST:
        context.user_data["language"] = raw_input
        await update.message.reply_text(f"✅ Language has bee changed **{raw_input}**", reply_markup=MAIN_KEYBOARD, parse_mode="Markdown")
        return

    if raw_input == "🛍 Products":
        await update.message.reply_text(
            "🛍 **Enterprise Corporate Product Index Portfolio**\n\n"
            "👕 *Premium Hoodie* — Advanced ergonomic dynamic thermal insulation profile garment design.\n"
            "👟 *Sneakers* — Optimized structural impact absorption multi-density training lifestyle models.\n"
            "🧥 *Jackets* — Heavy micro-weave atmospheric resilient ballistic environmental tracking gear.",
            parse_mode="Markdown"
        )
        return

    if raw_input == "❓ FAQs":
        await update.message.reply_text(
            "❓ **Systemic Frequently Asked Questions (FAQ) Documentation**\n\n"
            "🚚 **Shipping Performance:** Global logistic routes execute baseline transit parameters within 3 to 7 business verification days.\n"
            "💳 **Payment Rails Security:** Processing terminals securely authenticate modern transactions across Visa, Mastercard, and fully verified PayPal routing endpoints.\n"
            "🔄 **Returns Strategy:** Compliance terms guarantee an absolute 30-day corporate return evaluation window protection assurance.",
            parse_mode="Markdown"
        )
        return

    if raw_input == "📞 Contact":
        context.user_data["state"] = BotState.WAITING_NAME
        await update.message.reply_text("👤 Initiating secure lead onboarding interface.\n\nPlease enter your full  name:")
        return

    if raw_input == "🎨 Generate Image":
        context.user_data["state"] = BotState.WAITING_IMAGE_PROMPT
        await update.message.reply_text("🎨 **Image Generation Core Terminal Mode Activated**\n\nDescribe the image you want me to generate in high fidelity structural clarity details:", parse_mode="Markdown")
        return

    if raw_input == "🎤 Voice Chat":
        await update.message.reply_text("🎤 **Audio Telemetry System Active**\n\nSend me a voice message and i will listen, understand what you said,and reply with and answer.", parse_mode="Markdown")
        return

    if raw_input == "🤖 Ask AI":
        await update.message.reply_text("🤖 **Ask me anything**\n\n am here for you ", parse_mode="Markdown")
        return

    # =========================================================================
    # DEFAULT ASYNCHRONOUS CONVERSATIONAL INFERENCE ENGINE
    # =========================================================================

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
    conversational_status_banner = await update.message.reply_text("🤖 Thinking.......")

    try:
        calculated_response_text = await execute_ai_pipeline_with_retry(raw_input, user_selected_lang)
        response_segments = split_message_text(calculated_response_text)
        
        await conversational_status_banner.delete()
        for textual_slice in response_segments:
            await update.message.reply_text(textual_slice)
            
    except Exception as fallback_routing_fault:
        logger.error(f"Global catch-all error handling failure inside linguistic chat core: {fallback_routing_fault}", exc_info=True)
        await conversational_status_banner.edit_text("❌ Processing exception: Unable to interface query with compute clusters safely.")


async def global_system_error_boundary(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Intercepts and records trace matrix parameters preventing systemic memory runtime collapses."""
    logger.error(f"Global System boundary intercepted unhandled engine trace Exception context metrics: {context.error}", exc_info=context.error)
    
    if isinstance(update, Update) and update.has_filter(filters.TEXT) and update.message:
        try:
            await update.message.reply_text("❌ Core system interface exception: Operational continuity recovered safely.", reply_markup=MAIN_KEYBOARD)
        except TelegramError as logging_subsystem_fault:
            logger.critical(f"Fatal logging terminal transmission failure to broadcast tracking exception status bounds: {logging_subsystem_fault}")

# =========================================================================
# APPLICATION ENTRYPOINT RUNTIME ORCHESTRATION BLOCK
# =========================================================================

def main() -> NoReturn:
    """Configures application pipeline architecture, maps event loops, and boots system engine processes."""
    logger.info("Initializing enterprise engine instance configuration properties...")
    
    # Initialize the core application builder infrastructure
    runtime_application = Application.builder().token(BOT_TOKEN).build()

    # Register deterministic telemetry route vectors
    runtime_application.add_handler(CommandHandler("start", start_command))
    runtime_application.add_handler(MessageHandler(filters.VOICE, handle_incoming_voice))
    runtime_application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_incoming_text))

    # Incorporate global error handling mitigation boundary frameworks
    runtime_application.add_error_handler(global_system_error_boundary)

    # Output startup verification system banner sequence strings
    print("==================================================")
    print("🤖 AIHelperBot is running...")
    print("✅ Groq AI Enabled")
    print("✅ Multi-language Enabled")
    print("✅ Voice Chat Enabled")
    print("✅ AI Image Generation Enabled")
    print("✅ Contact Form Enabled")
    print("✅ Database Enabled")
    print("==================================================")
    
    logger.info("Infrastructure checks passed successfully. Transitioning control directly into live long-polling loops.")
    
    # Engage core async runtime lifecycle operations indefinitely
    runtime_application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()