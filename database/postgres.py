"""
database/postgres.py

PostgreSQL connection pool for Railway-hosted database.

Uses psycopg2.pool.ThreadedConnectionPool so connections are reused
across calls rather than opening a new TCP connection every time.

All repository functions are synchronous and must be called via
asyncio.to_thread() from async handlers.
"""

import logging
import os
from typing import Generator
from contextlib import contextmanager

import psycopg2
import psycopg2.pool
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# ── Configuration ──────────────────────────────────────────────────────────────

# Import from config if available, fall back to direct env read so this
# module can be imported standalone without circular import risk.
try:
    from config import DATABASE_URL
except ImportError:
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")  # type: ignore[assignment]

if not DATABASE_URL:
    raise EnvironmentError(
        "DATABASE_URL is not set. "
        "Set it in your .env file or Railway environment variables."
    )

# Pool sizing — tune via env vars if needed.
_POOL_MIN: int = int(os.getenv("DB_POOL_MIN", "1"))
_POOL_MAX: int = int(os.getenv("DB_POOL_MAX", "10"))

# ── Connection pool ────────────────────────────────────────────────────────────

_pool: psycopg2.pool.ThreadedConnectionPool | None = None


def _get_pool() -> psycopg2.pool.ThreadedConnectionPool:
    """
    Initialise the connection pool on first call and return it.
    Thread-safe via module-level singleton pattern.
    """
    global _pool

    if _pool is None or _pool.closed:
        logger.info(
            "Creating PostgreSQL connection pool (min=%d, max=%d)…",
            _POOL_MIN,
            _POOL_MAX,
        )
        try:
            _pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=_POOL_MIN,
                maxconn=_POOL_MAX,
                dsn=DATABASE_URL,
                # Railway requires SSL
                sslmode="require",
                # Return dicts instead of tuples
                cursor_factory=psycopg2.extras.RealDictCursor,
                # Keep-alive so Railway doesn't close idle connections
                keepalives=1,
                keepalives_idle=30,
                keepalives_interval=10,
                keepalives_count=5,
            )
            logger.info("PostgreSQL connection pool created successfully.")
        except psycopg2.OperationalError as err:
            logger.critical(
                "Could not connect to PostgreSQL: %s", err, exc_info=True
            )
            raise

    return _pool


@contextmanager
def get_connection() -> Generator[psycopg2.extensions.connection, None, None]:
    """
    Context manager that checks out a connection from the pool,
    yields it, then returns it — even if an exception is raised.

    Usage:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(...)
            conn.commit()
    """
    pool = _get_pool()
    conn = pool.getconn()
    try:
        yield conn
    except Exception:
        conn.rollback()
        raise
    finally:
        pool.putconn(conn)


def close_pool() -> None:
    """
    Close all connections in the pool.
    Call this during application shutdown.
    """
    global _pool
    if _pool and not _pool.closed:
        _pool.closeall()
        logger.info("PostgreSQL connection pool closed.")
    _pool = None