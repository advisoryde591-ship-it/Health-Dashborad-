"""Claude AI service for image analysis and chatbot functionality."""
import anthropic
import base64
import json
import re
from typing import Optional
from datetime import date
from ..config import get_settings

settings = get_settings()


class ClaudeAIService:
    """Service for interacting with Claude AI for image analysis and chat."""

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = settings.CLAUDE_MODEL

    def _encode_image(self, image_data: bytes) -> str:
        """Encode image bytes to base64."""
        return base64.standard_b64encode(image_data).decode("utf-8")

    def _get_media_type(self, filename: str) -> str:
        """Get media type from filename."""
        ext = filename.lower().split(".")[-1]
        media_types = {
            "png": "image/png",
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "gif": "image/gif",
            "webp": "image/webp",
        }
        return media_types.get(ext, "image/png")

    async def detect_screenshot_type(self, image_data: bytes, filename: str) -> str:
        """Detect the type of health screenshot."""
        prompt = """Analyze this health app screenshot and identify which type it is.

        Possible types:
        - whoop_recovery: Shows recovery percentage, HRV, resting heart rate, respiratory rate
        - whoop_sleep: Shows sleep stages (awake, light, deep/SWS, REM), sleep duration
        - whoop_dashboard: Shows daily metrics like weight, steps, calories, HR zones
        - scale: Shows body composition (weight, body fat %, muscle mass, BMI, bone mass, body water)
        - apple_workout: Shows workout details (activity type, duration, calories, heart rate)

        Respond with ONLY the type name, nothing else."""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=50,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": self._get_media_type(filename),
                                "data": self._encode_image(image_data),
                            },
                        },
                        {"type": "text", "text": prompt},
                    ],
                }
            ],
        )

        return response.content[0].text.strip().lower()

    async def analyze_whoop_recovery(self, image_data: bytes, filename: str) -> dict:
        """Extract data from Whoop recovery screenshot."""
        prompt = """Analyze this Whoop recovery screenshot and extract the following metrics.
        Return a JSON object with these fields (use null if not visible):

        {
            "recovery_score": <number 0-100>,
            "hrv": <number in ms>,
            "resting_heart_rate": <number in BPM>,
            "respiratory_rate": <number>,
            "sleep_performance": <number 0-100>
        }

        Return ONLY the JSON object, no other text."""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=200,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": self._get_media_type(filename),
                                "data": self._encode_image(image_data),
                            },
                        },
                        {"type": "text", "text": prompt},
                    ],
                }
            ],
        )

        return self._parse_json_response(response.content[0].text)

    async def analyze_whoop_sleep(self, image_data: bytes, filename: str) -> dict:
        """Extract data from Whoop sleep screenshot."""
        prompt = """Analyze this Whoop sleep screenshot and extract the following metrics.
        Return a JSON object with these fields (use null if not visible):

        {
            "total_sleep_hours": <decimal number like 6.78>,
            "total_duration_hours": <decimal number>,
            "awake_minutes": <number>,
            "awake_percentage": <number>,
            "light_sleep_minutes": <number>,
            "light_sleep_percentage": <number>,
            "deep_sleep_minutes": <number>,
            "deep_sleep_percentage": <number>,
            "rem_sleep_minutes": <number>,
            "rem_sleep_percentage": <number>,
            "sleep_start_time": <string like "23:36">,
            "sleep_end_time": <string like "06:44">
        }

        Note: Convert time formats like "3:24" to minutes (204 minutes).
        Return ONLY the JSON object, no other text."""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=300,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": self._get_media_type(filename),
                                "data": self._encode_image(image_data),
                            },
                        },
                        {"type": "text", "text": prompt},
                    ],
                }
            ],
        )

        return self._parse_json_response(response.content[0].text)

    async def analyze_whoop_dashboard(self, image_data: bytes, filename: str) -> dict:
        """Extract data from Whoop dashboard screenshot."""
        prompt = """Analyze this Whoop dashboard screenshot and extract the following metrics.
        Return a JSON object with these fields (use null if not visible):

        {
            "weight_kg": <number>,
            "hrv": <number>,
            "resting_heart_rate": <number>,
            "steps": <number>,
            "hr_zones_1_3_minutes": <number in minutes>,
            "hr_zones_4_5_minutes": <number in minutes>,
            "vo2_max": <number>,
            "calories_burned": <number>
        }

        Note: Convert time formats like "1:36" to minutes (96 minutes).
        Return ONLY the JSON object, no other text."""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=250,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": self._get_media_type(filename),
                                "data": self._encode_image(image_data),
                            },
                        },
                        {"type": "text", "text": prompt},
                    ],
                }
            ],
        )

        return self._parse_json_response(response.content[0].text)

    async def analyze_scale(self, image_data: bytes, filename: str) -> dict:
        """Extract data from smart scale screenshot."""
        prompt = """Analyze this smart scale/body composition screenshot and extract the following metrics.
        Return a JSON object with these fields (use null if not visible):

        {
            "weight_kg": <number>,
            "weight_change_kg": <number, positive or negative>,
            "bmi": <number>,
            "body_fat_percentage": <number>,
            "skeletal_muscle_mass_kg": <number>,
            "bone_mass_kg": <number>,
            "body_water_percentage": <number>
        }

        Return ONLY the JSON object, no other text."""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=200,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": self._get_media_type(filename),
                                "data": self._encode_image(image_data),
                            },
                        },
                        {"type": "text", "text": prompt},
                    ],
                }
            ],
        )

        return self._parse_json_response(response.content[0].text)

    async def analyze_apple_workout(self, image_data: bytes, filename: str) -> dict:
        """Extract data from Apple Watch workout screenshot."""
        prompt = """Analyze this Apple Watch/Fitness workout screenshot and extract the following metrics.
        Return a JSON object with these fields (use null if not visible):

        {
            "workout_type": <string like "Indoor Cycle", "Outdoor Run">,
            "date": <string like "2024-01-17">,
            "start_time": <string like "18:13">,
            "end_time": <string like "18:43">,
            "duration_minutes": <number>,
            "location": <string or null>,
            "active_calories": <number>,
            "total_calories": <number>,
            "avg_heart_rate": <number>,
            "max_heart_rate": <number or null>,
            "effort_score": <number 1-10 or null>,
            "effort_label": <string like "Easy", "Moderate" or null>
        }

        Return ONLY the JSON object, no other text."""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=300,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": self._get_media_type(filename),
                                "data": self._encode_image(image_data),
                            },
                        },
                        {"type": "text", "text": prompt},
                    ],
                }
            ],
        )

        return self._parse_json_response(response.content[0].text)

    async def estimate_food_calories(
        self, food_description: str, meal_type: str
    ) -> dict:
        """Estimate calories and macros from food description."""
        prompt = f"""A user logged their {meal_type}:

        "{food_description}"

        Estimate the nutritional content. Return a JSON object:

        {{
            "estimated_calories": <number>,
            "estimated_protein_g": <number>,
            "estimated_carbs_g": <number>,
            "estimated_fat_g": <number>,
            "ai_notes": "<brief nutritional feedback or suggestions, max 100 chars>"
        }}

        Be reasonable with estimates. If portions aren't specified, assume typical serving sizes.
        Return ONLY the JSON object, no other text."""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}],
        )

        return self._parse_json_response(response.content[0].text)

    async def generate_daily_summary(
        self,
        metrics: dict,
        food_logs: list,
        target_weight: float,
        calorie_target: int,
    ) -> str:
        """Generate a daily health summary for Telegram."""
        prompt = f"""Generate a friendly daily health summary based on this data:

        HEALTH METRICS:
        - Recovery Score: {metrics.get('recovery_score', 'N/A')}%
        - HRV: {metrics.get('hrv', 'N/A')} ms
        - Resting HR: {metrics.get('resting_heart_rate', 'N/A')} BPM
        - Sleep: {metrics.get('sleep_hours', 'N/A')} hours ({metrics.get('sleep_performance', 'N/A')}% performance)
        - Deep Sleep: {metrics.get('deep_sleep_percentage', 'N/A')}%
        - Steps: {metrics.get('steps', 'N/A')}
        - Calories Burned: {metrics.get('calories_burned', 'N/A')}

        BODY COMPOSITION:
        - Weight: {metrics.get('weight_kg', 'N/A')} kg (target: {target_weight} kg)
        - Body Fat: {metrics.get('body_fat_percentage', 'N/A')}%
        - Muscle Mass: {metrics.get('muscle_mass_kg', 'N/A')} kg

        WORKOUTS:
        {metrics.get('workout_summary', 'No workouts recorded')}

        FOOD INTAKE:
        Total calories consumed: {sum(f.get('calories', 0) for f in food_logs)} (target: {calorie_target})
        Meals: {len(food_logs)}

        Write a brief, motivating summary (max 500 chars) that:
        1. Highlights the key metrics
        2. Notes progress toward weight goal
        3. Gives one actionable recommendation

        Use emojis sparingly. Be encouraging but honest."""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}],
        )

        return response.content[0].text.strip()

    async def chat_response(
        self,
        user_message: str,
        conversation_history: list,
        user_context: dict,
    ) -> str:
        """Generate a chat response for the Telegram bot."""
        system_prompt = f"""You are a helpful health assistant for a user tracking their fitness journey.

        USER CONTEXT:
        - Current weight: {user_context.get('current_weight', 'Unknown')} kg
        - Target weight: {user_context.get('target_weight', 76)} kg
        - Today's calories consumed: {user_context.get('calories_consumed', 0)}
        - Today's calories burned: {user_context.get('calories_burned', 0)}
        - Recent recovery score: {user_context.get('recovery_score', 'Unknown')}%

        You can help with:
        1. Logging food (when user describes what they ate)
        2. Answering questions about their health data
        3. Providing motivation and tips
        4. Explaining their metrics

        Keep responses concise (under 300 chars) and friendly.
        If the user is logging food, confirm what you understood and estimate calories."""

        messages = [{"role": "user", "content": user_message}]
        if conversation_history:
            messages = conversation_history[-6:] + messages  # Keep last 3 exchanges

        response = self.client.messages.create(
            model=self.model,
            max_tokens=200,
            system=system_prompt,
            messages=messages,
        )

        return response.content[0].text.strip()

    def _parse_json_response(self, response_text: str) -> dict:
        """Parse JSON from Claude's response."""
        try:
            # Try to find JSON in the response
            json_match = re.search(r"\{[^{}]*\}", response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return json.loads(response_text)
        except json.JSONDecodeError:
            return {"error": "Failed to parse response", "raw": response_text}
