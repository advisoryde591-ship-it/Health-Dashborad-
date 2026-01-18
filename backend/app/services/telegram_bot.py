"""Telegram bot for food logging, daily summaries, and conversational AI."""
import asyncio
from datetime import date, datetime
from typing import Optional
from telegram import Update, Bot
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from ..config import get_settings

settings = get_settings()


class TelegramBotService:
    """Service for Telegram bot interactions with Gemini AI chat support."""

    def __init__(self, claude_service=None, gemini_service=None, db_session_factory=None):
        self.bot_token = settings.TELEGRAM_BOT_TOKEN
        self.chat_id = settings.TELEGRAM_CHAT_ID
        self.claude_service = claude_service
        self.gemini_service = gemini_service
        self.db_session_factory = db_session_factory
        self.bot = None
        self.application = None

        if self.bot_token:
            self.bot = Bot(token=self.bot_token)

    async def send_message(self, message: str, chat_id: Optional[str] = None) -> bool:
        """Send a message to Telegram."""
        target_chat = chat_id or self.chat_id

        if not self.bot or not target_chat:
            print("Telegram bot not configured")
            return False

        try:
            await self.bot.send_message(
                chat_id=target_chat,
                text=message,
                parse_mode="Markdown",
            )
            return True
        except Exception as e:
            print(f"Failed to send Telegram message: {e}")
            return False

    async def send_daily_summary(
        self,
        summary: str,
        chat_id: Optional[str] = None,
    ) -> bool:
        """Send the daily health summary."""
        header = f"*Daily Health Summary - {date.today().strftime('%B %d, %Y')}*\n\n"
        full_message = header + summary
        return await self.send_message(full_message, chat_id)

    def setup_handlers(self, application: Application):
        """Set up message handlers for the bot."""

        async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
            """Handle /start command."""
            welcome_msg = (
                "Hey! I'm your Health Buddy! \n\n"
                "I can help you:\n"
                "- Track what you eat (just tell me!)\n"
                "- Answer health questions\n"
                "- Give you motivation\n"
                "- Show your progress\n\n"
                "*Commands:*\n"
                "/log <food> - Log a meal\n"
                "/today - Today's summary\n"
                "/weight - Weight progress\n"
                "/chat - Have a conversation\n"
                "/clear - Clear chat history\n"
                "/help - Show help\n\n"
                "Or just chat with me naturally!"
            )
            await update.message.reply_text(welcome_msg, parse_mode="Markdown")

        async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
            """Handle /help command."""
            help_msg = (
                "*Health Buddy Help*\n\n"
                "*Food Logging:*\n"
                "Just tell me what you ate:\n"
                "- 'Had eggs and toast for breakfast'\n"
                "- 'Lunch was a chicken salad'\n"
                "- '/log pizza and salad'\n\n"
                "*Chat with me:*\n"
                "Ask me anything about health, nutrition, or fitness!\n"
                "- 'How can I improve my sleep?'\n"
                "- 'What should I eat before workout?'\n"
                "- 'Give me motivation!'\n\n"
                "*Commands:*\n"
                "/today - Full health summary\n"
                "/weight - Weight trend\n"
                "/calories - Calorie summary\n"
                "/clear - Reset our conversation\n"
            )
            await update.message.reply_text(help_msg, parse_mode="Markdown")

        async def log_food_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
            """Handle /log command for food logging."""
            if not context.args:
                await update.message.reply_text(
                    "What did you eat? Example:\n/log chicken salad with avocado"
                )
                return

            food_description = " ".join(context.args)
            await self._process_food_log(update, food_description, "meal")

        async def today_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
            """Handle /today command for daily summary."""
            await update.message.reply_text(
                "Fetching today's summary..."
            )
            # TODO: Implement with database

        async def weight_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
            """Handle /weight command."""
            await update.message.reply_text(
                "Checking weight progress..."
            )
            # TODO: Implement with database

        async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
            """Clear chat history with Gemini."""
            user_id = update.effective_user.id
            if self.gemini_service:
                self.gemini_service.clear_chat_history(user_id)
            await update.message.reply_text(
                "Chat history cleared! Let's start fresh."
            )

        async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
            """Handle regular text messages - smart detection for food vs chat."""
            message_text = update.message.text
            message_lower = message_text.lower()
            user_id = update.effective_user.id

            # Detect if this is likely a food log
            food_keywords = [
                "ate", "eaten", "had ", "having", "eating",
                "breakfast", "lunch", "dinner", "snack",
                "drank", "drinking", "coffee", "tea",
                "meal", "food", "just had", "i had"
            ]

            is_food_log = any(keyword in message_lower for keyword in food_keywords)

            if is_food_log:
                # Detect meal type
                meal_type = "snack"
                if any(word in message_lower for word in ["breakfast", "morning"]):
                    meal_type = "breakfast"
                elif any(word in message_lower for word in ["lunch", "noon", "midday"]):
                    meal_type = "lunch"
                elif any(word in message_lower for word in ["dinner", "evening", "night"]):
                    meal_type = "dinner"

                await self._process_food_log(update, message_text, meal_type)
            else:
                # This is a general chat message - use Gemini
                await self._process_chat(update, message_text, user_id)

        # Register handlers
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("log", log_food_command))
        application.add_handler(CommandHandler("today", today_command))
        application.add_handler(CommandHandler("weight", weight_command))
        application.add_handler(CommandHandler("clear", clear_command))
        application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
        )

    async def _process_chat(
        self,
        update: Update,
        message: str,
        user_id: int,
    ):
        """Process a conversational message using Gemini."""
        if not self.gemini_service:
            # Fallback to basic response if Gemini not configured
            await update.message.reply_text(
                "I'm here to help! Try logging food with /log or ask me about your health.\n"
                "(AI chat coming soon - add GEMINI_API_KEY to enable)"
            )
            return

        try:
            # Send typing indicator
            await update.message.chat.send_action("typing")

            # Get user context (would come from database in production)
            user_context = {
                "current_weight": 81.1,
                "target_weight": 76,
                "calories_today": 0,  # Would fetch from DB
                "recovery_score": 86,
            }

            # Get response from Gemini
            response = await self.gemini_service.chat(
                user_id=user_id,
                message=message,
                user_context=user_context,
            )

            await update.message.reply_text(response)

        except Exception as e:
            print(f"Error in chat: {e}")
            await update.message.reply_text(
                "Sorry, I had a moment there. Could you try again?"
            )

    async def _process_food_log(
        self,
        update: Update,
        food_description: str,
        meal_type: str,
    ):
        """Process and log food entry using Gemini or Claude."""
        # Try Gemini first, fall back to Claude
        estimate = None

        if self.gemini_service:
            try:
                result = await self.gemini_service.estimate_food(food_description, meal_type)
                if result and result.get("calories"):
                    estimate = {
                        "estimated_calories": result.get("calories"),
                        "estimated_protein_g": result.get("protein_g"),
                        "estimated_carbs_g": result.get("carbs_g"),
                        "estimated_fat_g": result.get("fat_g"),
                        "ai_notes": result.get("note", ""),
                    }
            except Exception as e:
                print(f"Gemini food estimation error: {e}")

        if not estimate and self.claude_service:
            try:
                estimate = await self.claude_service.estimate_food_calories(
                    food_description, meal_type
                )
            except Exception as e:
                print(f"Claude food estimation error: {e}")

        if not estimate or "error" in estimate:
            await update.message.reply_text(
                f"Got it! Logged: {food_description}\n(Calorie estimate unavailable)"
            )
            return

        # Format response
        response = (
            f"*{meal_type.title()} logged!*\n\n"
            f"Estimated:\n"
            f"- Calories: {estimate.get('estimated_calories', '?')} kcal\n"
            f"- Protein: {estimate.get('estimated_protein_g', '?')}g\n"
            f"- Carbs: {estimate.get('estimated_carbs_g', '?')}g\n"
            f"- Fat: {estimate.get('estimated_fat_g', '?')}g\n\n"
            f"{estimate.get('ai_notes', '')}"
        )

        await update.message.reply_text(response, parse_mode="Markdown")

    def run_bot(self):
        """Run the Telegram bot (blocking)."""
        if not self.bot_token:
            print("Telegram bot token not configured")
            return

        # Initialize services
        from .gemini_ai import GeminiAIService
        from .claude_ai import ClaudeAIService

        try:
            self.gemini_service = GeminiAIService()
            print("Gemini AI initialized")
        except Exception as e:
            print(f"Gemini not available: {e}")

        try:
            self.claude_service = ClaudeAIService()
            print("Claude AI initialized")
        except Exception as e:
            print(f"Claude not available: {e}")

        self.application = Application.builder().token(self.bot_token).build()
        self.setup_handlers(self.application)

        print("Starting Telegram bot with AI support...")
        print("- Chat: Gemini" if self.gemini_service else "- Chat: Basic mode")
        print("- Images: Claude" if self.claude_service else "- Images: Disabled")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)


async def send_notification(message: str, chat_id: Optional[str] = None) -> bool:
    """Standalone function to send a Telegram notification."""
    service = TelegramBotService()
    return await service.send_message(message, chat_id)
