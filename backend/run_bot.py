#!/usr/bin/env python3
"""Run the Telegram bot standalone."""
import asyncio
from dotenv import load_dotenv

load_dotenv()

from app.services.telegram_bot import TelegramBotService
from app.services.claude_ai import ClaudeAIService


def main():
    """Run the Telegram bot."""
    print("Starting Health Dashboard Telegram Bot...")

    claude_service = ClaudeAIService()
    bot_service = TelegramBotService(claude_service=claude_service)

    bot_service.run_bot()


if __name__ == "__main__":
    main()
