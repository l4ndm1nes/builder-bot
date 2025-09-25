import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Telegram Bot
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    
    # Google Sheets
    GOOGLE_SHEETS_CREDENTIALS_FILE = os.getenv('GOOGLE_SHEETS_CREDENTIALS_FILE', 'credentials.json')
    GOOGLE_SHEET_ID = os.getenv('GOOGLE_SHEET_ID')
    
    # Database
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///construction_bot.db')
    
    # Admin
    try:
        ADMIN_USER_ID = int(os.getenv('ADMIN_USER_ID', '0'))
    except ValueError:
        ADMIN_USER_ID = 0
    
    # Bot settings
    MAX_REQUESTS_PER_USER = 10
    REQUEST_EXPIRY_HOURS = 24
