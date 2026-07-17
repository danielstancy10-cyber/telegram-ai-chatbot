import logging
from database.postgres import get_connection

logger = logging.getLogger(__name__)


def run_migrations():
    """Run database migrations safely every time the bot starts."""

    with get_connection() as conn:
        with conn.cursor() as cur:

            migrations = [

                """
                ALTER TABLE users
                ADD COLUMN IF NOT EXISTS wallet_address TEXT DEFAULT '';
                """,

                """
                ALTER TABLE users
                ADD COLUMN IF NOT EXISTS membership TEXT DEFAULT 'Free';
                """,

                """
                ALTER TABLE users
                ADD COLUMN IF NOT EXISTS referral_count INTEGER DEFAULT 0;
                """,

                """
                ALTER TABLE users
                ADD COLUMN IF NOT EXISTS total_earnings NUMERIC DEFAULT 0;
                """,

                """
                ALTER TABLE users
                ADD COLUMN IF NOT EXISTS joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
                """

            ]

            for sql in migrations:
                cur.execute(sql)

        conn.commit()

    logger.info("Database migrations completed successfully.")