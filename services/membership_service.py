"""
services/membership_service.py

Membership business logic using the PostgreSQL repository.
"""

import logging
from typing import Any

from database.repository import get_user, update_membership

logger = logging.getLogger(__name__)

# ── Tier definitions ───────────────────────────────────────────────────────────

MEMBERSHIP_TIERS: dict[str, dict[str, Any]] = {
    "free": {
        "label":    "Free",
        "price":    "$0 / month",
        "features": [
            "Basic AI responses",
            "Language translation",
            "Voice chat",
        ],
    },
    "pro": {
        "label":    "Pro",
        "price":    "$9.99 / month",
        "features": [
            "Everything in Free",
            "Priority AI responses",
            "Image generation",
            "Faster support",
        ],
    },
    "enterprise": {
        "label":    "Enterprise",
        "price":    "$49.99 / month",
        "features": [
            "Everything in Pro",
            "Dedicated support",
            "Custom integrations",
            "NFT access",
        ],
    },
}

# ── Service functions ──────────────────────────────────────────────────────────

def get_membership_tier(telegram_id: int) -> str:
    """
    Return the membership tier string for *telegram_id*.
    Defaults to 'free' if the user is not found.

    Args:
        telegram_id: Telegram user ID.

    Returns:
        Tier string e.g. 'free', 'pro', 'enterprise'.
    """
    user = get_user(telegram_id)
    if user is None:
        return "free"
    return user.get("membership", "free") or "free"


def set_membership_tier(telegram_id: int, tier: str) -> None:
    """
    Update the membership tier for *telegram_id*.

    Args:
        telegram_id: Telegram user ID.
        tier:        New tier string — must be a key in MEMBERSHIP_TIERS.

    Raises:
        ValueError: If *tier* is not a recognised membership tier.
    """
    if tier not in MEMBERSHIP_TIERS:
        raise ValueError(
            f"Unknown membership tier: '{tier}'. "
            f"Valid tiers: {list(MEMBERSHIP_TIERS.keys())}"
        )
    update_membership(telegram_id, tier)
    logger.info("Membership updated: telegram_id=%s tier=%s", telegram_id, tier)


def build_membership(telegram_id: int) -> str:
    """
    Build a formatted membership summary for *telegram_id*.

    Reads the user's real tier from PostgreSQL and renders it as
    an HTML-formatted string.

    Args:
        telegram_id: Telegram user ID.

    Returns:
        HTML-formatted membership string.
    """
    user = get_user(telegram_id)

    if user is None:
        return (
            "💎 <b>Membership</b>\n\n"
            "No account found. Use /start to register first."
        )

    tier_key   = user.get("membership", "free") or "free"
    tier_info  = MEMBERSHIP_TIERS.get(tier_key, MEMBERSHIP_TIERS["free"])
    label      = tier_info["label"]
    price      = tier_info["price"]
    features   = tier_info["features"]

    features_str = "\n".join(f"  ✅ {f}" for f in features)

    return (
        "💎 <b>Your Membership</b>\n\n"
        f"<b>Current Plan:</b> {label}\n"
        f"<b>Price:</b> {price}\n\n"
        f"<b>Your Features:</b>\n"
        f"{features_str}\n\n"
        "To upgrade your plan, contact support or visit our website."
    )