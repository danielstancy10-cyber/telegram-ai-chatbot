"""
services/settings_service.py
Settings service for AIHelperBot.
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def build_settings(user_id: int) -> str:
    """
    Build the settings page text.
    """
    return (
        "⚙️ *Settings*\n\n"
        "Manage your AIHelperBot account.\n\n"
        "Current options:\n"
        "• 🔔 Notifications\n"
        "• 💎 Membership\n"
        "• 👤 Profile\n"
        "• 💼 Wallet"
    )


def get_settings_keyboard() -> InlineKeyboardMarkup:
    """
    Return the inline keyboard used by the settings page.
    """
    keyboard = [
        [
            InlineKeyboardButton(
                "🔔 Notifications",
                callback_data="settings_notifications"
            )
        ],
        [
            InlineKeyboardButton(
                "💎 Membership",
                callback_data="settings_membership"
            )
        ],
        [
            InlineKeyboardButton(
                "👤 Profile",
                callback_data="settings_profile"
            )
        ],
        [
            InlineKeyboardButton(
                "💼 Wallet",
                callback_data="settings_wallet"
            )
        ]
    ]

    return InlineKeyboardMarkup(keyboard)