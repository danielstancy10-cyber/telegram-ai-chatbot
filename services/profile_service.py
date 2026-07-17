"""
services/profile_service.py

Profile business logic using the PostgreSQL repository.
"""

import logging
from typing import Any

from database.repository import get_user, get_all_users

logger = logging.getLogger(__name__)

# Optional: import for enhancement if needed
# from services.membership_service import get_membership_display


def build_profile(telegram_id: int) -> str:
    """
    Build a formatted profile message for *telegram_id*.

    Args:
        telegram_id: The Telegram user ID.

    Returns:
        HTML-formatted profile string.
    """
    user = get_user(telegram_id)

    if user is None:
        return (
            "👤 <b>Profile Not Found</b>\n\n"
            "You don't have a profile yet. Use /start to register."
        )

    username = user.get("username") or "Not set"
    full_name = user.get("full_name") or "Not set"
    created = user.get("created_at", "Unknown")
    membership = user.get("membership", "free").capitalize()
    wallet = user.get("wallet_address") or "Not connected"

    # Format timestamp if it is a datetime object
    if hasattr(created, "strftime"):
        created_str = created.strftime("%Y-%m-%d")
    else:
        created_str = str(created)[:10]

    return (
        "👤 <b>Your Profile</b>\n\n"
        f"<b>Telegram ID:</b> <code>{telegram_id}</code>\n"
        f"<b>Username:</b> @{username}\n"
        f"<b>Full Name:</b> {full_name}\n"
        f"<b>Member Since:</b> {created_str}\n"
        f"<b>Membership:</b> {membership}\n"
        f"<b>Wallet:</b> {wallet}\n"
    )