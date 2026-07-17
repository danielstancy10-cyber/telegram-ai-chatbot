"""
handlers/membership.py

Command handler: /membership
Exports: async def membership(update, context)
"""

import asyncio
import logging

from telegram import Update
from telegram.ext import ContextTypes

from services.membership_service import build_membership

logger = logging.getLogger(__name__)


async def membership(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /membership command.

    Fetches the user's real membership tier from PostgreSQL and
    replies with a formatted summary.
    """
    if not update.message or not update.effective_user:
        return

    user_id = update.effective_user.id

    try:
        text = await asyncio.to_thread(build_membership, user_id)
        await update.message.reply_text(text, parse_mode="HTML")

    except Exception as exc:
        logger.error(
            "Membership handler error for user %s: %s", user_id, exc, exc_info=True
        )
        await update.message.reply_text(
            "❌ Could not load your membership. Please try again later."
        )