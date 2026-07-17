"""
services/notification_service.py

Notification preferences business logic using PostgreSQL.

Each notification type is a boolean column in the
user_notifications table. Defaults to True for important
alerts, False for optional ones.
"""

import logging
from typing import Any

import psycopg2
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from database.postgres import get_connection
from database.repository import get_user

logger = logging.getLogger(__name__)

# ── Defaults ───────────────────────────────────────────────────────────────────

DEFAULT_NOTIFICATIONS: dict[str, bool] = {
    "system_alerts":      True,
    "membership_updates": True,
    "weekly_digest":      False,
    "promotional":        False,
    "ai_responses":       True,
    "voice_transcripts":  False,
}

# Human-readable labels for each notification type
NOTIFICATION_LABELS: dict[str, str] = {
    "system_alerts":      "🚨 System Alerts",
    "membership_updates": "💎 Membership Updates",
    "weekly_digest":      "📋 Weekly Digest",
    "promotional":        "📣 Promotional",
    "ai_responses":       "🤖 AI Responses",
    "voice_transcripts":  "🎤 Voice Transcripts",
}

# ── Database helpers ───────────────────────────────────────────────────────────

def _get_raw_notifications(telegram_id: int) -> dict[str, Any]:
    """
    Fetch raw notification row for *telegram_id*.
    Returns DEFAULT_NOTIFICATIONS if no row exists.
    """
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM user_notifications WHERE telegram_id = %s",
                    (telegram_id,),
                )
                row = cur.fetchone()
                if row is None:
                    return dict(DEFAULT_NOTIFICATIONS)
                # Strip non-notification columns before returning
                data = dict(row)
                data.pop("telegram_id", None)
                data.pop("updated_at",  None)
                return data
    except psycopg2.Error as err:
        logger.error(
            "Failed to fetch notifications for %s: %s",
            telegram_id, err, exc_info=True,
        )
        return dict(DEFAULT_NOTIFICATIONS)


def _upsert_notifications(
    telegram_id: int,
    updates: dict[str, bool],
) -> None:
    """
    Insert or update notification columns for *telegram_id*.
    Only keys present in *updates* are written.
    """
    if not updates:
        return

    # Only allow known notification keys to prevent SQL injection
    safe_updates = {
        k: v for k, v in updates.items()
        if k in DEFAULT_NOTIFICATIONS
    }

    if not safe_updates:
        return

    set_clauses = ", ".join(f"{col} = %s" for col in safe_updates)
    values      = list(safe_updates.values()) + [telegram_id]

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                # Ensure row exists first
                cur.execute(
                    """
                    INSERT INTO user_notifications (telegram_id)
                    VALUES (%s)
                    ON CONFLICT (telegram_id) DO NOTHING
                    """,
                    (telegram_id,),
                )
                cur.execute(
                    f"""
                    UPDATE user_notifications
                    SET    {set_clauses},
                           updated_at = NOW()
                    WHERE  telegram_id = %s
                    """,
                    values,
                )
            conn.commit()
        logger.info(
            "Notifications updated for telegram_id=%s: %s",
            telegram_id, safe_updates,
        )
    except psycopg2.Error as err:
        logger.error(
            "Failed to update notifications for %s: %s",
            telegram_id, err, exc_info=True,
        )
        raise


# ── Public service functions ───────────────────────────────────────────────────

def get_user_notifications(telegram_id: int) -> dict[str, Any]:
    """
    Return notification preferences for *telegram_id*.
    Falls back to DEFAULT_NOTIFICATIONS if no row exists.

    Args:
        telegram_id: Telegram user ID.

    Returns:
        Dict mapping notification type keys to bool values.
    """
    return _get_raw_notifications(telegram_id)


def toggle_notification(telegram_id: int, key: str) -> dict[str, Any]:
    """
    Toggle a single notification type for *telegram_id*.

    Args:
        telegram_id: Telegram user ID.
        key:         Notification key e.g. 'system_alerts'.

    Returns:
        Updated notifications dict.

    Raises:
        ValueError: If *key* is not a recognised notification type.
    """
    if key not in DEFAULT_NOTIFICATIONS:
        raise ValueError(
            f"Unknown notification key: '{key}'. "
            f"Valid keys: {list(DEFAULT_NOTIFICATIONS.keys())}"
        )

    current = _get_raw_notifications(telegram_id)
    new_val = not current.get(key, DEFAULT_NOTIFICATIONS[key])
    _upsert_notifications(telegram_id, {key: new_val})

    logger.info(
        "Notification toggled: telegram_id=%s key=%s value=%s",
        telegram_id, key, new_val,
    )
    return _get_raw_notifications(telegram_id)


def update_user_notifications(
    telegram_id: int,
    new_settings: dict[str, bool],
) -> dict[str, Any]:
    """
    Update multiple notification preferences at once.

    Args:
        telegram_id:  Telegram user ID.
        new_settings: Dict of notification keys → bool values.

    Returns:
        Updated notifications dict.
    """
    _upsert_notifications(telegram_id, new_settings)
    return _get_raw_notifications(telegram_id)


def build_notifications(telegram_id: int) -> str:
    """
    Build an HTML-formatted notification settings summary for *telegram_id*.

    Args:
        telegram_id: Telegram user ID.

    Returns:
        HTML string ready to send via reply_text(parse_mode='HTML').
    """
    user = get_user(telegram_id)
    if user is None:
        return (
            "🔔 <b>Notifications</b>\n\n"
            "No account found. Use /start to register first."
        )

    prefs = _get_raw_notifications(telegram_id)

    def _row(key: str) -> str:
        label = NOTIFICATION_LABELS.get(key, key)
        value = prefs.get(key, DEFAULT_NOTIFICATIONS.get(key, False))
        icon  = "🔔 On" if value else "🔕 Off"
        return f"<b>{label}:</b> {icon}"

    rows = "\n".join(_row(k) for k in DEFAULT_NOTIFICATIONS)

    return (
        "🔔 <b>Your Notification Settings</b>\n\n"
        f"{rows}\n\n"
        "Use the buttons below to toggle each notification type."
    )


def get_notifications_keyboard(telegram_id: int) -> InlineKeyboardMarkup:
    """
    Build an inline keyboard for toggling each notification type.

    Args:
        telegram_id: Telegram user ID.

    Returns:
        InlineKeyboardMarkup with one toggle button per notification type.
    """
    prefs = _get_raw_notifications(telegram_id)

    buttons = []
    for key, label in NOTIFICATION_LABELS.items():
        value = prefs.get(key, DEFAULT_NOTIFICATIONS.get(key, False))
        icon  = "🔔" if value else "🔕"
        buttons.append([
            InlineKeyboardButton(
                f"{icon} {label}",
                callback_data=f"notif:toggle:{key}",
            )
        ])

    return InlineKeyboardMarkup(buttons)