from pathlib import Path

files = {
    "handlers/start.py": "",
    "handlers/help.py": "",
    "handlers/admin.py": "",
    "handlers/payment.py": "",
    "handlers/wallet.py": "",
    "handlers/nft.py": "",
    "handlers/referral.py": "",

    "services/user_service.py": "",
    "services/payment_service.py": "",
    "services/nft_service.py": "",
    "services/referral_service.py": "",

    "database/models.py": "",
    "database/postgres.py": "",
    "database/repository.py": "",

    "blockchain/web3_client.py": "",
    "blockchain/wallet.py": "",
    "blockchain/nft.py": "",
    "blockchain/payment_monitor.py": "",

    "payments/payment_gateway.py": "",
    "payments/payment_verifier.py": "",

    "admin/dashboard.py": "",
    "admin/broadcast.py": "",

    "utils/helpers.py": "",
    "utils/constants.py": "",
}

for file in files:
    path = Path(file)

    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch()
        print(f"Created {file}")
    else:
        print(f"Already exists {file}")

print("\nPhase 3 files created successfully!")