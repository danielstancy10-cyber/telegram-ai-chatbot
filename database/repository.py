from database.postgres import get_connection


# -----------------------------
# USERS
# -----------------------------

def create_user(telegram_id, username, full_name):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO users
        (telegram_id, username, full_name)
        VALUES (%s, %s, %s)
        ON CONFLICT (telegram_id)
        DO NOTHING;
    """, (telegram_id, username, full_name))

    conn.commit()

    cur.close()
    conn.close()


def get_user(telegram_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT *
        FROM users
        WHERE telegram_id=%s;
    """, (telegram_id,))

    user = cur.fetchone()

    cur.close()
    conn.close()

    return user


def get_all_users():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT *
        FROM users;
    """)

    users = cur.fetchall()

    cur.close()
    conn.close()

    return users


# -----------------------------
# WALLET
# -----------------------------

def update_wallet(telegram_id, wallet_address):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE users
        SET wallet_address=%s
        WHERE telegram_id=%s;
    """, (wallet_address, telegram_id))

    conn.commit()

    cur.close()
    conn.close()


# -----------------------------
# MEMBERSHIP
# -----------------------------

def update_membership(telegram_id, membership):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE users
        SET membership=%s
        WHERE telegram_id=%s;
    """, (membership, telegram_id))

    conn.commit()

    cur.close()
    conn.close()