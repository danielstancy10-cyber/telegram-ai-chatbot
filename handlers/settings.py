"""
handlers/settings.py

Command handler: /settings
Exports: async def settings(update, context)
"""

import asyncio
import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from services.settings_service import build_settings, get_settings_keyboard

logger = logging.getLogger(__name__)


async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /settings command.

    Fetches the user's real settings from PostgreSQL and replies
    with a formatted summary and an inline keyboard to change them.
    """
    if not update.message or not update.effective_user:
        return

    user_id = update.effective_user.id

    try:
        text     = await asyncio.to_thread(build_settings, user_id)
        keyboard = await asyncio.to_thread(get_settings_keyboard, user_id)

        await update.message.reply_text(
            text,
            parse_mode="HTML",
            reply_markup=keyboard,
        )

    except Exception as exc:
        logger.error(
            "Settings handler error for user %s: %s", user_id, exc, exc_info=True
        )
        await update.message.reply_text(
            "❌ Could not load your settings. Please try again later."
        )