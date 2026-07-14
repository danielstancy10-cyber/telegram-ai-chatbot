from pathlib import Path

folders = {
    "handlers": [
        "profile.py",
        "membership.py",
        "settings.py",
        "notifications.py",
    ],
    "services": [
        "profile_service.py",
        "membership_service.py",
        "wallet_service.py",
        "notification_service.py",
        "analytics_service.py",
    ],
    "database": [
        "crud.py",
        "migrations.py",
    ],
    "blockchain": [
        "contracts.py",
        "transactions.py",
    ],
    "payments": [
        "invoice.py",
        "coinpayments.py",
        "nowpayments.py",
    ],
    "admin": [
        "users.py",
        "payments.py",
        "statistics.py",
        "memberships.py",
    ],
    "utils": [
        "validators.py",
        "decorators.py",
        "security.py",
        "formatters.py",
    ],
}

for folder, files in folders.items():
    Path(folder).mkdir(exist_ok=True)

    for file in files:
        path = Path(folder) / file

        if not path.exists():
            path.write_text(
                f'"""\n{file}\nAutomatically created.\n"""\n',
                encoding="utf-8"
            )
            print(f"Created: {path}")

print("\n✅ Project structure updated successfully!")