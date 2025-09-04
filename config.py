import os
from dataclasses import dataclass
from typing import List

@dataclass
class BotConfig:
    BOT_TOKEN: str
    APP_ID: int
    APP_HASH: str
    GEMINI_API_KEY: str
    URLSCAN_API_KEY: str
    ADMIN_ID: int
    OWNER_ID: int
    STORAGE_CHANNEL_ID: int
    USER_DATA_SAVE_CHANNEL_ID: int
    BOT_OWNER_NAME: str = "Mraprguild"

def load_config() -> BotConfig:
    """Load configuration from environment variables"""
    return BotConfig(
        BOT_TOKEN=os.getenv('BOT_TOKEN') or '',
        APP_ID=int(os.getenv('APP_ID') or '0'),
        APP_HASH=os.getenv('APP_HASH') or '',
        GEMINI_API_KEY=os.getenv('GEMINI_API_KEY') or '',
        URLSCAN_API_KEY=os.getenv('URLSCAN_API_KEY') or '',
        ADMIN_ID=int(os.getenv('ADMIN_ID') or '0'),
        OWNER_ID=int(os.getenv('OWNER_ID') or '0'),
        STORAGE_CHANNEL_ID=int(os.getenv('STORAGE_CHANNEL_ID') or '0'),
        USER_DATA_SAVE_CHANNEL_ID=int(os.getenv('USER_DATA_SAVE_CHANNEL_ID') or '0'),
    )

# Global config instance
config = load_config()