"""
handlers/profile.py

Command handler: /profile
Exports: async def profile(update, context)
"""

import logging

from telegram import Update
from telegram.ext import ContextTypes

from services.profile_service import build_profile

logger = logging.getLogger(__name__)


async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /profile command.

    Fetches the user's profile from the PostgreSQL database and replies
    with a formatted summary.
    """
    if not update.message or not update.effective_user:
        return

    user_id = update.effective_user.id

    try:
        # build_profile is synchronous (uses psycopg2 pool) — run in thread
        # so the event loop is never blocked.
        import asyncio
        text = await asyncio.to_thread(build_profile, user_id)

        await update.message.reply_text(text, parse_mode="HTML")

    except Exception as exc:
        logger.exception("Profile handler error for user %s: %s", user_id, exc)
        await update.message.reply_text(
            "❌ Could not load your profile. Please try again later.",
            reply_markup=MAIN_KEYBOARD if "MAIN_KEYBOARD" in globals() else None,
        )