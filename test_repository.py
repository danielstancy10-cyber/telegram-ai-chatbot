from database.repository import (
    create_user,
    get_user,
    get_all_users,
    update_wallet,
    update_membership,
)

# Create a test user
create_user(
    telegram_id=123456789,
    username="testuser",
    full_name="Test User"
)

print("User created.")

# Fetch user
user = get_user(123456789)
print("Fetched user:")
print(user)

# Update wallet
update_wallet(
    123456789,
    "0x123456789ABCDEF123456789ABCDEF123456789"
)

print("Wallet updated.")

# Update membership
update_membership(
    123456789,
    "Premium"
)

print("Membership updated.")

# Show all users
print("\nAll users:")
print(get_all_users())