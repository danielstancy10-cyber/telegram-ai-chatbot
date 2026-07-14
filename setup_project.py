import os

folders = [
    "logs",
    "utils",
    "handlers",
    "services",
    "database",
    "blockchain",
    "payments",
    "admin"
]

files = [
    "utils/logger.py",
    "logs/bot.log",
    "handlers/__init__.py",
    "services/__init__.py",
    "database/__init__.py",
    "blockchain/__init__.py",
    "payments/__init__.py",
    "admin/__init__.py"
]

print("Creating folders...")

for folder in folders:
    os.makedirs(folder, exist_ok=True)
    print(f"✅ Created: {folder}")

print("\nCreating files...")

for file in files:
    if not os.path.exists(file):
        with open(file, "w") as f:
            pass
        print(f"✅ Created: {file}")
    else:
        print(f"✔ Already exists: {file}")

print("\n🎉 Project structure created successfully!")