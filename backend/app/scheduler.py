"""Scheduler for automatic screenshot processing and daily summaries."""
import asyncio
from datetime import datetime, date
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select, and_
from .config import get_settings
from .models.database import AsyncSessionLocal
from .models.health_metrics import User, DailyMetrics, SleepData, BodyComposition, FoodLog
from .services.claude_ai import ClaudeAIService
from .services.google_drive import GoogleDriveService
from .services.telegram_bot import TelegramBotService

settings = get_settings()


async def process_new_screenshots():
    """Process new screenshots from Google Drive."""
    print(f"[{datetime.now()}] Checking for new screenshots...")

    try:
        drive_service = GoogleDriveService()
    except Exception as e:
        print(f"Failed to connect to Google Drive: {e}")
        return

    async with AsyncSessionLocal() as db:
        # Get all users (in a real app, you'd have user-specific folders)
        result = await db.execute(select(User).where(User.is_active == True))
        users = result.scalars().all()

        for user in users:
            try:
                new_files = drive_service.get_new_screenshots(hours_back=2)
                print(f"Found {len(new_files)} new files for user {user.username}")

                from .api.screenshots import _process_screenshot, Screenshot

                for file_info, file_content in new_files:
                    # Check if already processed
                    existing = await db.execute(
                        select(Screenshot).where(
                            and_(
                                Screenshot.user_id == user.id,
                                Screenshot.google_drive_id == file_info["id"],
                            )
                        )
                    )
                    if existing.scalar_one_or_none():
                        continue

                    # Create and process screenshot
                    screenshot = Screenshot(
                        user_id=user.id,
                        date=date.today(),
                        filename=file_info["name"],
                        google_drive_id=file_info["id"],
                        processed=False,
                    )
                    db.add(screenshot)
                    await db.commit()
                    await db.refresh(screenshot)

                    try:
                        await _process_screenshot(screenshot, file_content, user, db)
                        print(f"Processed: {file_info['name']}")
                    except Exception as e:
                        print(f"Error processing {file_info['name']}: {e}")
                        screenshot.processing_error = str(e)
                        await db.commit()

            except Exception as e:
                print(f"Error processing screenshots for {user.username}: {e}")


async def send_daily_summaries():
    """Send daily health summaries via Telegram."""
    print(f"[{datetime.now()}] Sending daily summaries...")

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.is_active == True))
        users = result.scalars().all()

        for user in users:
            try:
                await _send_user_summary(user, db)
            except Exception as e:
                print(f"Error sending summary for {user.username}: {e}")


async def _send_user_summary(user: User, db):
    """Send daily summary for a specific user."""
    today = date.today()

    # Gather metrics
    metrics_result = await db.execute(
        select(DailyMetrics).where(
            and_(DailyMetrics.user_id == user.id, DailyMetrics.date == today)
        )
    )
    metrics = metrics_result.scalar_one_or_none()

    sleep_result = await db.execute(
        select(SleepData).where(
            and_(SleepData.user_id == user.id, SleepData.date == today)
        )
    )
    sleep = sleep_result.scalar_one_or_none()

    body_result = await db.execute(
        select(BodyComposition)
        .where(BodyComposition.user_id == user.id)
        .order_by(BodyComposition.date.desc())
        .limit(1)
    )
    body = body_result.scalar_one_or_none()

    food_result = await db.execute(
        select(FoodLog).where(
            and_(FoodLog.user_id == user.id, FoodLog.date == today)
        )
    )
    food_logs = food_result.scalars().all()

    # Build metrics dict for Claude
    metrics_dict = {
        "recovery_score": metrics.recovery_score if metrics else None,
        "hrv": metrics.hrv if metrics else None,
        "resting_heart_rate": metrics.resting_heart_rate if metrics else None,
        "sleep_hours": round(sleep.actual_sleep_minutes / 60, 1) if sleep and sleep.actual_sleep_minutes else None,
        "sleep_performance": metrics.sleep_performance if metrics else None,
        "deep_sleep_percentage": sleep.deep_sleep_percentage if sleep else None,
        "steps": metrics.steps if metrics else None,
        "calories_burned": metrics.calories_burned if metrics else None,
        "weight_kg": body.weight_kg if body else None,
        "body_fat_percentage": body.body_fat_percentage if body else None,
        "muscle_mass_kg": body.skeletal_muscle_mass_kg if body else None,
        "workout_summary": "Workout data available" if metrics else "No workouts",
    }

    food_logs_dict = [
        {"calories": f.estimated_calories or 0, "description": f.description}
        for f in food_logs
    ]

    # Generate summary with Claude
    claude_service = ClaudeAIService()
    summary = await claude_service.generate_daily_summary(
        metrics_dict,
        food_logs_dict,
        user.target_weight,
        user.daily_calorie_target,
    )

    # Send via Telegram
    telegram_service = TelegramBotService()
    await telegram_service.send_daily_summary(summary)
    print(f"Sent daily summary to {user.username}")


def start_scheduler() -> AsyncIOScheduler:
    """Start the background scheduler."""
    scheduler = AsyncIOScheduler(timezone=settings.TIMEZONE)

    # Process screenshots every 30 minutes
    scheduler.add_job(
        process_new_screenshots,
        CronTrigger(minute="*/30"),
        id="process_screenshots",
        name="Process new screenshots from Google Drive",
        replace_existing=True,
    )

    # Send daily summary at 9 AM
    scheduler.add_job(
        send_daily_summaries,
        CronTrigger(hour=9, minute=0),
        id="daily_summary",
        name="Send daily health summary via Telegram",
        replace_existing=True,
    )

    scheduler.start()
    print("Scheduler started")
    print("- Screenshot processing: every 30 minutes")
    print("- Daily summaries: 9:00 AM")

    return scheduler
