#!/usr/bin/env python3
"""Run the Telegram bot standalone."""
import asyncio
from dotenv import load_dotenv

load_dotenv()

from app.services.telegram_bot import TelegramBotService
from app.services.gemini_ai import GeminiAIService


def main():
    """Run the Telegram bot."""
    print("Starting Health Dashboard Telegram Bot...")

    gemini_service = GeminiAIService()
    bot_service = TelegramBotService(gemini_service=gemini_service)

    bot_service.run_bot()


if __name__ == "__main__":
    main()
