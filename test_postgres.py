from database.postgres import get_connection

try:
    conn = get_connection()
    print("Connected to PostgreSQL!")

    conn.close()

except Exception as e:
    print(e)