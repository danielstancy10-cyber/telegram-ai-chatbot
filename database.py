import sqlite3

DB_NAME = "customer_support.db"


def connect_db():
    """Connect to the SQLite database."""
    conn = sqlite3.connect(DB_NAME)
    return conn


def create_table():
    """Create the leads table if it doesn't exist."""
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


def save_lead(name, email):
    """Save a new lead to the database."""
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO leads (name, email)
        VALUES (?, ?)
    """, (name, email))

    conn.commit()
    conn.close()


def get_all_leads():
    """Return all saved leads."""
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM leads")
    leads = cursor.fetchall()

    conn.close()
    return leads


def delete_lead(lead_id):
    """Delete a lead by ID."""
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM leads WHERE id = ?",
        (lead_id,)
    )

    conn.commit()
    conn.close()


# Create the table automatically when this file is imported
create_table()