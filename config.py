import os
from dotenv import load_dotenv

load_dotenv()

# Telegram
BOT_TOKEN = os.getenv("BOT_TOKEN")

# AI
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
HF_API_KEY = os.getenv("HF_API_KEY")

# Database
DATABASE_URL = os.getenv("DATABASE_URL")

# Blockchain
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
PUBLIC_WALLET = os.getenv("PUBLIC_WALLET")
RPC_URL = os.getenv("RPC_URL")

# NFT
NFT_CONTRACT = os.getenv("NFT_CONTRACT")

# Admin
ADMIN_ID = os.getenv("ADMIN_ID")