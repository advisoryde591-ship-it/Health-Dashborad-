"""Gemini AI service for conversational chat."""
import google.generativeai as genai
from typing import Optional
from ..config import get_settings

settings = get_settings()


class GeminiAIService:
    """Service for conversational AI using Google Gemini."""

    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.model_name = settings.GEMINI_MODEL
        self.model = None
        self.chat_sessions = {}  # Store chat sessions by user_id

        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(
                model_name=self.model_name,
                system_instruction=self._get_system_prompt(),
            )

    def _get_system_prompt(self) -> str:
        """Get the system prompt for the health assistant."""
        return """You are a friendly and knowledgeable health assistant named "Health Buddy".

Your role is to:
1. Help users track and understand their health metrics (weight, sleep, recovery, calories)
2. Provide motivation and encouragement for their fitness journey
3. Answer questions about nutrition, exercise, and wellness
4. Log food when users tell you what they ate
5. Give personalized recommendations based on their data

Personality:
- Friendly and supportive, like a fitness coach friend
- Encouraging but honest - celebrate wins, gently address areas to improve
- Knowledgeable but not preachy
- Use occasional emojis to be friendly (but not too many)

When users tell you what they ate:
- Acknowledge it positively
- Estimate calories and macros
- Give a brief tip if relevant

Keep responses concise (under 200 words) since this is a chat interface.
Always be supportive of their goal to reach 76kg through healthy habits."""

    def get_or_create_chat(self, user_id: int):
        """Get or create a chat session for a user."""
        if not self.model:
            return None

        if user_id not in self.chat_sessions:
            self.chat_sessions[user_id] = self.model.start_chat(history=[])

        return self.chat_sessions[user_id]

    async def chat(
        self,
        user_id: int,
        message: str,
        user_context: Optional[dict] = None,
    ) -> str:
        """Send a message and get a response.

        Args:
            user_id: User identifier for session management
            message: User's message
            user_context: Optional dict with user's health context

        Returns:
            AI response text
        """
        if not self.model:
            return "Gemini is not configured. Please add GEMINI_API_KEY to your settings."

        chat = self.get_or_create_chat(user_id)

        # Add context to the message if provided
        context_prefix = ""
        if user_context:
            context_parts = []
            if user_context.get("current_weight"):
                context_parts.append(f"Current weight: {user_context['current_weight']}kg")
            if user_context.get("target_weight"):
                context_parts.append(f"Target: {user_context['target_weight']}kg")
            if user_context.get("calories_today"):
                context_parts.append(f"Calories today: {user_context['calories_today']}")
            if user_context.get("recovery_score"):
                context_parts.append(f"Recovery: {user_context['recovery_score']}%")

            if context_parts:
                context_prefix = f"[User context: {', '.join(context_parts)}]\n\n"

        try:
            response = chat.send_message(context_prefix + message)
            return response.text
        except Exception as e:
            print(f"Gemini error: {e}")
            return "Sorry, I had trouble processing that. Could you try again?"

    async def estimate_food(self, food_description: str, meal_type: str) -> dict:
        """Estimate calories and macros from food description.

        Args:
            food_description: What the user ate
            meal_type: breakfast, lunch, dinner, or snack

        Returns:
            Dict with estimated calories and macros
        """
        if not self.model:
            return {"error": "Gemini not configured"}

        prompt = f"""Estimate the nutritional content of this {meal_type}:

"{food_description}"

Respond ONLY with a JSON object in this exact format (no markdown, no explanation):
{{"calories": 500, "protein_g": 30, "carbs_g": 50, "fat_g": 20, "note": "Brief healthy tip"}}

Use realistic estimates. If portions unclear, assume typical serving sizes."""

        try:
            response = self.model.generate_content(prompt)
            text = response.text.strip()

            # Clean up response if needed
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            text = text.strip()

            import json
            return json.loads(text)
        except Exception as e:
            print(f"Gemini food estimation error: {e}")
            return {
                "calories": None,
                "protein_g": None,
                "carbs_g": None,
                "fat_g": None,
                "note": "Could not estimate - logged for tracking",
            }

    def clear_chat_history(self, user_id: int):
        """Clear chat history for a user."""
        if user_id in self.chat_sessions:
            del self.chat_sessions[user_id]

    async def get_daily_motivation(self, user_context: dict) -> str:
        """Generate a personalized daily motivation message.

        Args:
            user_context: Dict with user's recent health data

        Returns:
            Motivational message string
        """
        if not self.model:
            return "Have a great day! Keep working toward your goals!"

        prompt = f"""Generate a brief, personalized morning motivation message (2-3 sentences) for someone with these stats:

- Current weight: {user_context.get('weight', 'unknown')} kg
- Target weight: {user_context.get('target_weight', 76)} kg
- Yesterday's recovery: {user_context.get('recovery', 'unknown')}%
- Sleep quality: {user_context.get('sleep_quality', 'unknown')}
- Week's progress: {user_context.get('week_change', 'unknown')} kg

Be encouraging, specific to their data, and suggest one actionable tip for today."""

        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Gemini motivation error: {e}")
            return "Good morning! Every day is a chance to get closer to your goals. Let's make today count!"
