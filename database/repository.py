"""
database/repository.py

User repository — all operations against the users table.
All functions are synchronous.
Call via asyncio.to_thread() from async Telegram handlers.
"""

import logging
from typing import Any

import psycopg2

from database.postgres import get_connection          # ← fixed import

logger = logging.getLogger(__name__)


# ── Users ──────────────────────────────────────────────────────────────────────

def create_user(
    telegram_id: int,
    username:    str | None = None,
    full_name:   str | None = None,
) -> None:
    """
    Insert a new user row.
    Silently ignored if telegram_id already exists.
    """
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO users (telegram_id, username, full_name)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (telegram_id) DO NOTHING
                    """,
                    (telegram_id, username, full_name),
                )
            conn.commit()
        logger.info("create_user: telegram_id=%s username=%s", telegram_id, username)
    except psycopg2.Error as err:
        logger.error(
            "create_user failed for telegram_id=%s: %s",
            telegram_id, err, exc_info=True,
        )
        raise


def get_user(telegram_id: int) -> dict[str, Any] | None:
    """Fetch a user by Telegram ID. Returns None if not found."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM users WHERE telegram_id = %s",
                    (telegram_id,),
                )
                row = cur.fetchone()
                return dict(row) if row else None
    except psycopg2.Error as err:
        logger.error(
            "get_user failed for telegram_id=%s: %s",
            telegram_id, err, exc_info=True,
        )
        return None


def get_all_users() -> list[dict[str, Any]]:
    """Return every user row as a list of dicts."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM users ORDER BY created_at DESC")
                return [dict(row) for row in cur.fetchall()]
    except psycopg2.Error as err:
        logger.error("get_all_users failed: %s", err, exc_info=True)
        return []


# ── Wallet ─────────────────────────────────────────────────────────────────────

def update_wallet(telegram_id: int, wallet_address: str) -> None:
    """Set or update the wallet address for a user."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE users
                    SET    wallet_address = %s,
                           updated_at     = NOW()
                    WHERE  telegram_id    = %s
                    """,
                    (wallet_address, telegram_id),
                )
            conn.commit()
        logger.info("update_wallet: telegram_id=%s", telegram_id)
    except psycopg2.Error as err:
        logger.error(
            "update_wallet failed for telegram_id=%s: %s",
            telegram_id, err, exc_info=True,
        )
        raise


# ── Membership ─────────────────────────────────────────────────────────────────

def update_membership(telegram_id: int, membership: str) -> None:
    """Update the membership tier for a user."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE users
                    SET    membership  = %s,
                           updated_at  = NOW()
                    WHERE  telegram_id = %s
                    """,
                    (membership, telegram_id),
                )
            conn.commit()
        logger.info(
            "update_membership: telegram_id=%s tier=%s", telegram_id, membership
        )
    except psycopg2.Error as err:
        logger.error(
            "update_membership failed for telegram_id=%s: %s",
            telegram_id, err, exc_info=True,
        )
        raise


# ── Public API ─────────────────────────────────────────────────────────────────

__all__ = [
    "create_user",
    "get_user",
    "get_all_users",
    "update_wallet",
    "update_membership",
]