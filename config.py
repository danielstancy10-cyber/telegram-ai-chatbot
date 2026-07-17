"""
config.py
Reads all environment variables from .env / Railway service variables.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ── Telegram ───────────────────────────────────────────────────────────────────
BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")

# ── AI Services ───────────────────────────────────────────────────────────────
GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
HF_API_KEY:   str = os.getenv("HF_API_KEY",   "")

# ── Database (Railway PostgreSQL) ──────────────────────────────────────────────
DATABASE_URL: str = os.getenv("DATABASE_URL", "")

# ── Blockchain ─────────────────────────────────────────────────────────────────
PRIVATE_KEY:   str = os.getenv("PRIVATE_KEY",   "")
PUBLIC_WALLET: str = os.getenv("PUBLIC_WALLET", "")
RPC_URL:       str = os.getenv("RPC_URL",       "")

# ── NFT ────────────────────────────────────────────────────────────────────────
NFT_CONTRACT: str = os.getenv("NFT_CONTRACT", "")

# ── Admin ──────────────────────────────────────────────────────────────────────
ADMIN_ID: int = int(os.getenv("ADMIN_ID", "0"))