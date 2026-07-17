"""
database/__init__.py

Public interface for the database package.

Responsibilities:
    - Schema initialisation (PostgreSQL via Railway)
    - Leads CRUD (contact form captures)

All functions are synchronous — call via asyncio.to_thread() from async code.
"""

import logging

import psycopg2

from database.postgres import get_connection

logger = logging.getLogger(__name__)

# ── Schema DDL ─────────────────────────────────────────────────────────────────

_USERS_DDL = """
CREATE TABLE IF NOT EXISTS users (
    id              SERIAL PRIMARY KEY,
    telegram_id     BIGINT  UNIQUE NOT NULL,
    username        TEXT,
    full_name       TEXT,
    wallet_address  TEXT,
    membership      TEXT    NOT NULL DEFAULT 'free',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
"""

_LEADS_DDL = """
CREATE TABLE IF NOT EXISTS leads (
    id          SERIAL PRIMARY KEY,
    name        TEXT        NOT NULL,
    email       TEXT        NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
"""


def init_db() -> None:
    """
    Create all required tables in PostgreSQL if they do not already exist.

    Call this ONCE at application startup (bot.py → main()).
    Never runs automatically on import.
    """
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(_USERS_DDL)
                cur.execute(_LEADS_DDL)
            conn.commit()
        logger.info("PostgreSQL schema initialised successfully.")
    except psycopg2.Error as err:
        logger.critical(
            "Failed to initialise PostgreSQL schema: %s", err, exc_info=True
        )
        raise


# ── Leads CRUD ─────────────────────────────────────────────────────────────────

def save_lead(name: str, email: str) -> None:
    """
    Persist a contact-form lead to the leads table.

    Args:
        name:  Full name provided by the user.
        email: Email address provided by the user.
    """
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO leads (name, email) VALUES (%s, %s)",
                    (name, email),
                )
            conn.commit()
        logger.info("Lead saved: %s <%s>", name, email)
    except psycopg2.Error as err:
        logger.error(
            "Failed to save lead '%s <%s>': %s", name, email, err, exc_info=True
        )
        raise


def get_all_leads() -> list[dict]:
    """
    Return all leads ordered newest-first.
    Returns an empty list on database error.
    """
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM leads ORDER BY created_at DESC"
                )
                rows = cur.fetchall()
                return [dict(row) for row in rows]
    except psycopg2.Error as err:
        logger.error("Failed to fetch leads: %s", err, exc_info=True)
        return []


def delete_lead(lead_id: int) -> None:
    """
    Delete a lead by primary key.

    Args:
        lead_id: The integer primary key of the lead to remove.
    """
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM leads WHERE id = %s",
                    (lead_id,),
                )
            conn.commit()
        logger.info("Lead %d deleted.", lead_id)
    except psycopg2.Error as err:
        logger.error(
            "Failed to delete lead %d: %s", lead_id, err, exc_info=True
        )
        raise


# ── Public API ─────────────────────────────────────────────────────────────────

__all__ = [
    "init_db",
    "save_lead",
    "get_all_leads",
    "delete_lead",
]