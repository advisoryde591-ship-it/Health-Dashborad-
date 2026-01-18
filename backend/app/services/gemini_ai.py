"""Gemini AI service for conversational chat and image analysis."""
import google.generativeai as genai
import json
import os
from typing import Optional
from PIL import Image
import io


class GeminiAIService:
    """Service for conversational AI and image analysis using Google Gemini."""

    def __init__(self):
        # Read directly from environment
        self.api_key = os.environ.get("GEMINI_API_KEY", "")
        self.model_name = os.environ.get("GEMINI_MODEL", "gemini-1.5-flash")
        self.model = None
        self.vision_model = None
        self.chat_sessions = {}  # Store chat sessions by user_id

        print(f"Gemini API key present: {bool(self.api_key)}")
        print(f"Gemini model: {self.model_name}")

        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(
                model_name=self.model_name,
                system_instruction=self._get_system_prompt(),
            )
            # Vision model for image analysis (no system instruction)
            self.vision_model = genai.GenerativeModel(model_name=self.model_name)

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

    def _bytes_to_image(self, image_data: bytes) -> Image.Image:
        """Convert bytes to PIL Image."""
        return Image.open(io.BytesIO(image_data))

    async def detect_screenshot_type(self, image_data: bytes, filename: str) -> str:
        """Detect the type of health screenshot."""
        if not self.vision_model:
            return "unknown"

        prompt = """Analyze this health app screenshot and identify which type it is.

Possible types:
- whoop_recovery: Shows recovery percentage (like 86%), HRV, resting heart rate
- whoop_sleep: Shows sleep data, sleep stages, hours of sleep
- whoop_dashboard: Shows daily overview with weight, steps, calories, heart rate zones
- scale: Shows body composition - weight, body fat %, muscle mass, BMI
- apple_workout: Shows workout from Apple Watch - activity type, duration, calories burned

Look at the main content of the image. If you see:
- A recovery score percentage → whoop_recovery
- Sleep hours and stages → whoop_sleep
- Weight/steps/calories overview → whoop_dashboard
- Body fat/muscle/BMI numbers → scale
- Workout activity details → apple_workout

Respond with ONLY one of these exact words: whoop_recovery, whoop_sleep, whoop_dashboard, scale, apple_workout"""

        try:
            image = self._bytes_to_image(image_data)
            response = self.vision_model.generate_content([prompt, image])
            result = response.text.strip().lower()

            # Normalize the response
            if "recovery" in result:
                return "whoop_recovery"
            elif "sleep" in result:
                return "whoop_sleep"
            elif "dashboard" in result or "overview" in result:
                return "whoop_dashboard"
            elif "scale" in result or "body" in result or "composition" in result:
                return "scale"
            elif "workout" in result or "apple" in result or "exercise" in result:
                return "apple_workout"

            return result
        except Exception as e:
            print(f"Gemini screenshot detection error: {e}")
            return "unknown"

    async def analyze_whoop_recovery(self, image_data: bytes, filename: str) -> dict:
        """Extract data from Whoop recovery screenshot."""
        prompt = """Analyze this Whoop recovery screenshot and extract the following metrics.
Return a JSON object with these fields (use null if not visible):

{"recovery_score": <number 0-100>, "hrv": <number in ms>, "resting_heart_rate": <number in BPM>, "respiratory_rate": <number>, "sleep_performance": <number 0-100>}

Return ONLY the JSON object, no other text or markdown."""

        return await self._analyze_image(image_data, prompt)

    async def analyze_whoop_sleep(self, image_data: bytes, filename: str) -> dict:
        """Extract data from Whoop sleep screenshot."""
        prompt = """Analyze this Whoop sleep screenshot and extract the following metrics.
Return a JSON object with these fields (use null if not visible):

{"total_sleep_hours": <decimal number>, "awake_minutes": <number>, "awake_percentage": <number>, "light_sleep_minutes": <number>, "light_sleep_percentage": <number>, "deep_sleep_minutes": <number>, "deep_sleep_percentage": <number>, "rem_sleep_minutes": <number>, "rem_sleep_percentage": <number>}

Convert time formats like "3:24" to minutes (204 minutes).
Return ONLY the JSON object, no other text or markdown."""

        return await self._analyze_image(image_data, prompt)

    async def analyze_whoop_dashboard(self, image_data: bytes, filename: str) -> dict:
        """Extract data from Whoop dashboard screenshot."""
        prompt = """Analyze this Whoop dashboard screenshot and extract the following metrics.
Return a JSON object with these fields (use null if not visible):

{"weight_kg": <number>, "hrv": <number>, "resting_heart_rate": <number>, "steps": <number>, "calories_burned": <number>}

Convert time formats like "1:36" to minutes (96 minutes).
Return ONLY the JSON object, no other text or markdown."""

        return await self._analyze_image(image_data, prompt)

    async def analyze_scale(self, image_data: bytes, filename: str) -> dict:
        """Extract data from smart scale screenshot."""
        prompt = """Analyze this smart scale/body composition screenshot and extract the following metrics.
Return a JSON object with these fields (use null if not visible):

{"weight_kg": <number>, "bmi": <number>, "body_fat_percentage": <number>, "skeletal_muscle_mass_kg": <number>, "bone_mass_kg": <number>, "body_water_percentage": <number>}

Return ONLY the JSON object, no other text or markdown."""

        return await self._analyze_image(image_data, prompt)

    async def analyze_apple_workout(self, image_data: bytes, filename: str) -> dict:
        """Extract data from Apple Watch workout screenshot."""
        prompt = """Analyze this Apple Watch/Fitness workout screenshot and extract the following metrics.
Return a JSON object with these fields (use null if not visible):

{"workout_type": <string like "Indoor Cycle">, "duration_minutes": <number>, "active_calories": <number>, "total_calories": <number>, "avg_heart_rate": <number>, "effort_label": <string like "Easy", "Moderate">}

Return ONLY the JSON object, no other text or markdown."""

        return await self._analyze_image(image_data, prompt)

    async def _analyze_image(self, image_data: bytes, prompt: str) -> dict:
        """Generic image analysis helper."""
        if not self.vision_model:
            return {"error": "Gemini not configured"}

        try:
            image = self._bytes_to_image(image_data)
            response = self.vision_model.generate_content([prompt, image])
            text = response.text.strip()

            # Clean up response if needed
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            text = text.strip()

            return json.loads(text)
        except json.JSONDecodeError as e:
            print(f"Gemini JSON parse error: {e}")
            return {"error": "Failed to parse response"}
        except Exception as e:
            print(f"Gemini image analysis error: {e}")
            return {"error": str(e)}
