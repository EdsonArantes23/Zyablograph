import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENROUTER_KEY = os.getenv("OPENROUTER_KEY")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
DIGEST_HOUR = int(os.getenv("DIGEST_HOUR", 20))
DIGEST_MINUTE = int(os.getenv("DIGEST_MINUTE", 0))
SPONSOR_LINK = os.getenv("SPONSOR_LINK", "")
SPONSOR_TEXT = os.getenv("SPONSOR_TEXT", "")
