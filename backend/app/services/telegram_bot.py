"""Telegram bot for food logging, daily summaries, and conversational AI."""
import asyncio
import io
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


def format_metrics_response(screenshot_type: str, data: dict) -> str:
    """Format extracted metrics into a readable Telegram message."""
    if "error" in data:
        return f"Could not extract data: {data.get('error', 'Unknown error')}"

    if screenshot_type == "whoop_recovery":
        return (
            f"*Recovery Data*\n\n"
            f"Recovery Score: {data.get('recovery_score', '?')}%\n"
            f"HRV: {data.get('hrv', '?')} ms\n"
            f"Resting HR: {data.get('resting_heart_rate', '?')} BPM\n"
            f"Respiratory Rate: {data.get('respiratory_rate', '?')}\n"
            f"Sleep Performance: {data.get('sleep_performance', '?')}%"
        )
    elif screenshot_type == "whoop_sleep":
        return (
            f"*Sleep Data*\n\n"
            f"Total Sleep: {data.get('total_sleep_hours', '?')} hours\n"
            f"Deep Sleep: {data.get('deep_sleep_minutes', '?')} min ({data.get('deep_sleep_percentage', '?')}%)\n"
            f"REM Sleep: {data.get('rem_sleep_minutes', '?')} min ({data.get('rem_sleep_percentage', '?')}%)\n"
            f"Light Sleep: {data.get('light_sleep_minutes', '?')} min ({data.get('light_sleep_percentage', '?')}%)\n"
            f"Awake: {data.get('awake_minutes', '?')} min"
        )
    elif screenshot_type == "whoop_dashboard":
        return (
            f"*Dashboard Data*\n\n"
            f"Weight: {data.get('weight_kg', '?')} kg\n"
            f"Steps: {data.get('steps', '?')}\n"
            f"Calories Burned: {data.get('calories_burned', '?')}\n"
            f"HRV: {data.get('hrv', '?')} ms\n"
            f"Resting HR: {data.get('resting_heart_rate', '?')} BPM"
        )
    elif screenshot_type == "scale":
        weight = data.get('weight_kg', '?')
        target = settings.TARGET_WEIGHT_KG
        diff = ""
        if weight != '?' and weight is not None:
            diff = f" ({weight - target:+.1f} from goal)"
        return (
            f"*Body Composition*\n\n"
            f"Weight: {weight} kg{diff}\n"
            f"Body Fat: {data.get('body_fat_percentage', '?')}%\n"
            f"Muscle Mass: {data.get('skeletal_muscle_mass_kg', '?')} kg\n"
            f"BMI: {data.get('bmi', '?')}\n"
            f"Body Water: {data.get('body_water_percentage', '?')}%"
        )
    elif screenshot_type == "apple_workout":
        return (
            f"*Workout*\n\n"
            f"Type: {data.get('workout_type', '?')}\n"
            f"Duration: {data.get('duration_minutes', '?')} min\n"
            f"Calories: {data.get('total_calories', '?')} kcal\n"
            f"Avg HR: {data.get('avg_heart_rate', '?')} BPM\n"
            f"Effort: {data.get('effort_label', '?')}"
        )
    else:
        return f"*Screenshot Analyzed*\n\nData: {data}"


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
                "Hey! I'm your Health Buddy!\n\n"
                "I can help you:\n"
                "- Analyze health screenshots (Whoop, Scale, Apple Watch)\n"
                "- Track what you eat (just tell me!)\n"
                "- Answer health questions\n"
                "- Give you motivation\n\n"
                "*Just send me:*\n"
                "- A screenshot to analyze\n"
                "- What you ate to log food\n"
                "- Any health question!\n\n"
                "*Commands:*\n"
                "/log <food> - Log a meal\n"
                "/today - Today's summary\n"
                "/clear - Clear chat history\n"
                "/help - Show help"
            )
            await update.message.reply_text(welcome_msg, parse_mode="Markdown")

        async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
            """Handle /help command."""
            help_msg = (
                "*Health Buddy Help*\n\n"
                "*Screenshot Analysis:*\n"
                "Send me screenshots from:\n"
                "- Whoop (Recovery, Sleep, Dashboard)\n"
                "- Smart Scale (body composition)\n"
                "- Apple Watch (workouts)\n\n"
                "*Food Logging:*\n"
                "Just tell me what you ate:\n"
                "- 'Had eggs and toast for breakfast'\n"
                "- 'Lunch was a chicken salad'\n"
                "- '/log pizza and salad'\n\n"
                "*Chat:*\n"
                "Ask me anything about health!\n\n"
                "*Commands:*\n"
                "/today - Today's summary\n"
                "/clear - Reset conversation\n"
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

        async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
            """Handle photo uploads - analyze health screenshots with Claude."""
            await self._process_photo(update)

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
        application.add_handler(
            MessageHandler(filters.PHOTO, handle_photo)
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

    async def _process_photo(self, update: Update):
        """Process a photo upload - analyze with Claude AI."""
        if not self.claude_service:
            await update.message.reply_text(
                "Image analysis is not available. Please configure ANTHROPIC_API_KEY."
            )
            return

        try:
            # Send typing indicator
            await update.message.chat.send_action("typing")
            await update.message.reply_text("Analyzing your screenshot...")

            # Get the largest photo (best quality)
            photo = update.message.photo[-1]
            file = await photo.get_file()

            # Download the photo
            photo_bytes = await file.download_as_bytearray()
            image_data = bytes(photo_bytes)
            filename = f"telegram_photo_{photo.file_id}.jpg"

            # Detect screenshot type
            screenshot_type = await self.claude_service.detect_screenshot_type(
                image_data, filename
            )

            # Analyze based on type
            data = {}
            if screenshot_type == "whoop_recovery":
                data = await self.claude_service.analyze_whoop_recovery(image_data, filename)
            elif screenshot_type == "whoop_sleep":
                data = await self.claude_service.analyze_whoop_sleep(image_data, filename)
            elif screenshot_type == "whoop_dashboard":
                data = await self.claude_service.analyze_whoop_dashboard(image_data, filename)
            elif screenshot_type == "scale":
                data = await self.claude_service.analyze_scale(image_data, filename)
            elif screenshot_type == "apple_workout":
                data = await self.claude_service.analyze_apple_workout(image_data, filename)
            else:
                await update.message.reply_text(
                    f"I detected this as: {screenshot_type}\n"
                    "I support: Whoop (recovery/sleep/dashboard), Scale, Apple Watch workouts"
                )
                return

            # Format and send response
            response = format_metrics_response(screenshot_type, data)
            await update.message.reply_text(response, parse_mode="Markdown")

        except Exception as e:
            print(f"Error processing photo: {e}")
            await update.message.reply_text(
                "Sorry, I couldn't analyze that image. Please try again with a clear screenshot."
            )

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
