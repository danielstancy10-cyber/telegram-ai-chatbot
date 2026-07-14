from database.models import create_tables

try:
    create_tables()
    print("✅ Database ready! Users table created.")

except Exception as e:
    print("❌ Error creating tables:")
    print(e)