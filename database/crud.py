from database.postgres import get_connection


def get_user(telegram_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT telegram_id,
               username,
               full_name,
               wallet_address,
               membership,
               referral_count,
               total_earnings,
               joined_at
        FROM users
        WHERE telegram_id=%s
        """,
        (telegram_id,),
    )

    user = cur.fetchone()

    cur.close()
    conn.close()

    return user