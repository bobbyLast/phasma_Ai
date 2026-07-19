"""Re-export Telegram bot for root-level imports (main.py, utils/alert_router.py)."""
from scripts.ops.telegram_bot import TelegramBot, get_telegram_bot

__all__ = ["TelegramBot", "get_telegram_bot"]
