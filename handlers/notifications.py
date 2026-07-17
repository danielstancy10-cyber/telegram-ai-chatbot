"""
handlers/notifications.py

Command handler: /notifications
Exports: async def notifications(update, context)
"""

import asyncio
import logging

from telegram import Update
from telegram.ext import ContextTypes

from services.notification_service import build_notifications, get_notifications_keyboard

logger = logging.getLogger(__name__)


async def notifications(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /notifications command.

    Fetches the user's real notification preferences from PostgreSQL
    and replies with a formatted summary and inline toggle keyboard.
    """
    if not update.message or not update.effective_user:
        return

    user_id = update.effective_user.id

    try:
        text     = await asyncio.to_thread(build_notifications, user_id)
        keyboard = await asyncio.to_thread(get_notifications_keyboard, user_id)

        await update.message.reply_text(
            text,
            parse_mode="HTML",
            reply_markup=keyboard,
        )

    except Exception as exc:
        logger.error(
            "Notifications handler error for user %s: %s", user_id, exc, exc_info=True
        )
        await update.message.reply_text(
            "❌ Could not load your notification settings. Please try again later."
        )