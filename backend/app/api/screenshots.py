"""Screenshot processing API routes."""
import json
from datetime import date, datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from ..models import (
    User,
    Screenshot,
    DailyMetrics,
    SleepData,
    WorkoutData,
    BodyComposition,
    get_db,
)
from ..services.claude_ai import ClaudeAIService
from .auth import get_current_user

router = APIRouter(prefix="/screenshots", tags=["screenshots"])


class ScreenshotResponse(BaseModel):
    id: int
    date: date
    filename: str
    screenshot_type: Optional[str]
    processed: bool
    processed_at: Optional[datetime]
    processing_error: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class ProcessingStatus(BaseModel):
    total: int
    processed: int
    pending: int
    errors: int


@router.post("/upload")
async def upload_screenshot(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload and process a health screenshot."""
    # Validate file type
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    # Read file content
    content = await file.read()

    # Create screenshot record
    screenshot = Screenshot(
        user_id=current_user.id,
        date=date.today(),
        filename=file.filename,
        processed=False,
    )
    db.add(screenshot)
    await db.commit()
    await db.refresh(screenshot)

    # Process the screenshot
    try:
        await _process_screenshot(screenshot, content, current_user, db)
    except Exception as e:
        screenshot.processing_error = str(e)
        await db.commit()
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

    return {
        "message": "Screenshot processed successfully",
        "screenshot_id": screenshot.id,
        "type": screenshot.screenshot_type,
    }


@router.post("/process-drive")
async def process_drive_screenshots(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Process new screenshots from Google Drive."""
    from ..services.google_drive import GoogleDriveService

    try:
        drive_service = GoogleDriveService()
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to connect to Google Drive: {str(e)}"
        )

    # Get new screenshots from last 24 hours
    new_files = drive_service.get_new_screenshots(hours_back=24)

    processed = 0
    errors = []

    for file_info, file_content in new_files:
        # Check if already processed
        existing = await db.execute(
            select(Screenshot).where(
                and_(
                    Screenshot.user_id == current_user.id,
                    Screenshot.google_drive_id == file_info["id"],
                )
            )
        )
        if existing.scalar_one_or_none():
            continue

        # Create screenshot record
        screenshot = Screenshot(
            user_id=current_user.id,
            date=date.today(),
            filename=file_info["name"],
            google_drive_id=file_info["id"],
            processed=False,
        )
        db.add(screenshot)
        await db.commit()
        await db.refresh(screenshot)

        try:
            await _process_screenshot(screenshot, file_content, current_user, db)
            processed += 1
        except Exception as e:
            errors.append({"file": file_info["name"], "error": str(e)})
            screenshot.processing_error = str(e)
            await db.commit()

    return {
        "processed": processed,
        "errors": errors,
        "total_found": len(new_files),
    }


@router.get("/status", response_model=ProcessingStatus)
async def get_processing_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get screenshot processing status."""
    from sqlalchemy import func

    # Total screenshots
    total_result = await db.execute(
        select(func.count(Screenshot.id)).where(Screenshot.user_id == current_user.id)
    )
    total = total_result.scalar() or 0

    # Processed
    processed_result = await db.execute(
        select(func.count(Screenshot.id)).where(
            and_(
                Screenshot.user_id == current_user.id,
                Screenshot.processed == True,
            )
        )
    )
    processed = processed_result.scalar() or 0

    # Errors
    errors_result = await db.execute(
        select(func.count(Screenshot.id)).where(
            and_(
                Screenshot.user_id == current_user.id,
                Screenshot.processing_error.isnot(None),
            )
        )
    )
    errors = errors_result.scalar() or 0

    return ProcessingStatus(
        total=total,
        processed=processed,
        pending=total - processed - errors,
        errors=errors,
    )


@router.get("/recent", response_model=list[ScreenshotResponse])
async def get_recent_screenshots(
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get recent screenshots."""
    result = await db.execute(
        select(Screenshot)
        .where(Screenshot.user_id == current_user.id)
        .order_by(Screenshot.created_at.desc())
        .limit(limit)
    )
    return result.scalars().all()


async def _process_screenshot(
    screenshot: Screenshot,
    image_data: bytes,
    user: User,
    db: AsyncSession,
):
    """Process a screenshot and extract health data."""
    claude_service = ClaudeAIService()

    # Detect screenshot type
    screenshot_type = await claude_service.detect_screenshot_type(
        image_data, screenshot.filename
    )
    screenshot.screenshot_type = screenshot_type

    # Extract data based on type
    extracted_data = {}

    if screenshot_type == "whoop_recovery":
        extracted_data = await claude_service.analyze_whoop_recovery(
            image_data, screenshot.filename
        )
        await _save_recovery_data(extracted_data, user, screenshot.date, db)

    elif screenshot_type == "whoop_sleep":
        extracted_data = await claude_service.analyze_whoop_sleep(
            image_data, screenshot.filename
        )
        await _save_sleep_data(extracted_data, user, screenshot.date, db)

    elif screenshot_type == "whoop_dashboard":
        extracted_data = await claude_service.analyze_whoop_dashboard(
            image_data, screenshot.filename
        )
        await _save_dashboard_data(extracted_data, user, screenshot.date, db)

    elif screenshot_type == "scale":
        extracted_data = await claude_service.analyze_scale(
            image_data, screenshot.filename
        )
        await _save_body_composition(extracted_data, user, screenshot.date, db)

    elif screenshot_type == "apple_workout":
        extracted_data = await claude_service.analyze_apple_workout(
            image_data, screenshot.filename
        )
        await _save_workout_data(extracted_data, user, screenshot.date, db)

    # Save extracted data
    screenshot.extracted_data = json.dumps(extracted_data)
    screenshot.processed = True
    screenshot.processed_at = datetime.utcnow()

    await db.commit()


async def _save_recovery_data(data: dict, user: User, target_date: date, db: AsyncSession):
    """Save recovery data to daily metrics."""
    # Get or create daily metrics
    result = await db.execute(
        select(DailyMetrics).where(
            and_(
                DailyMetrics.user_id == user.id,
                DailyMetrics.date == target_date,
            )
        )
    )
    metrics = result.scalar_one_or_none()

    if not metrics:
        metrics = DailyMetrics(user_id=user.id, date=target_date)
        db.add(metrics)

    # Update fields
    if data.get("recovery_score"):
        metrics.recovery_score = data["recovery_score"]
    if data.get("hrv"):
        metrics.hrv = data["hrv"]
    if data.get("resting_heart_rate"):
        metrics.resting_heart_rate = data["resting_heart_rate"]
    if data.get("respiratory_rate"):
        metrics.respiratory_rate = data["respiratory_rate"]
    if data.get("sleep_performance"):
        metrics.sleep_performance = data["sleep_performance"]

    await db.commit()


async def _save_sleep_data(data: dict, user: User, target_date: date, db: AsyncSession):
    """Save sleep data."""
    # Get or create sleep record
    result = await db.execute(
        select(SleepData).where(
            and_(
                SleepData.user_id == user.id,
                SleepData.date == target_date,
            )
        )
    )
    sleep = result.scalar_one_or_none()

    if not sleep:
        sleep = SleepData(user_id=user.id, date=target_date)
        db.add(sleep)

    # Update fields
    if data.get("total_sleep_hours"):
        sleep.actual_sleep_minutes = int(data["total_sleep_hours"] * 60)
    if data.get("total_duration_hours"):
        sleep.total_duration_minutes = int(data["total_duration_hours"] * 60)
    if data.get("awake_minutes"):
        sleep.awake_minutes = data["awake_minutes"]
    if data.get("awake_percentage"):
        sleep.awake_percentage = data["awake_percentage"]
    if data.get("light_sleep_minutes"):
        sleep.light_sleep_minutes = data["light_sleep_minutes"]
    if data.get("light_sleep_percentage"):
        sleep.light_sleep_percentage = data["light_sleep_percentage"]
    if data.get("deep_sleep_minutes"):
        sleep.deep_sleep_minutes = data["deep_sleep_minutes"]
    if data.get("deep_sleep_percentage"):
        sleep.deep_sleep_percentage = data["deep_sleep_percentage"]
    if data.get("rem_sleep_minutes"):
        sleep.rem_sleep_minutes = data["rem_sleep_minutes"]
    if data.get("rem_sleep_percentage"):
        sleep.rem_sleep_percentage = data["rem_sleep_percentage"]

    await db.commit()


async def _save_dashboard_data(data: dict, user: User, target_date: date, db: AsyncSession):
    """Save dashboard metrics."""
    result = await db.execute(
        select(DailyMetrics).where(
            and_(
                DailyMetrics.user_id == user.id,
                DailyMetrics.date == target_date,
            )
        )
    )
    metrics = result.scalar_one_or_none()

    if not metrics:
        metrics = DailyMetrics(user_id=user.id, date=target_date)
        db.add(metrics)

    if data.get("steps"):
        metrics.steps = data["steps"]
    if data.get("calories_burned"):
        metrics.calories_burned = data["calories_burned"]
    if data.get("vo2_max"):
        metrics.vo2_max = data["vo2_max"]
    if data.get("hrv"):
        metrics.hrv = data["hrv"]
    if data.get("resting_heart_rate"):
        metrics.resting_heart_rate = data["resting_heart_rate"]
    if data.get("hr_zones_1_3_minutes"):
        metrics.hr_zones_1_3_minutes = data["hr_zones_1_3_minutes"]
    if data.get("hr_zones_4_5_minutes"):
        metrics.hr_zones_4_5_minutes = data["hr_zones_4_5_minutes"]

    await db.commit()


async def _save_body_composition(data: dict, user: User, target_date: date, db: AsyncSession):
    """Save body composition data."""
    # Always create new record for body composition (allows multiple weigh-ins)
    body = BodyComposition(
        user_id=user.id,
        date=target_date,
        measured_at=datetime.utcnow(),
        weight_kg=data.get("weight_kg", 0),
        weight_change_kg=data.get("weight_change_kg"),
        bmi=data.get("bmi"),
        body_fat_percentage=data.get("body_fat_percentage"),
        skeletal_muscle_mass_kg=data.get("skeletal_muscle_mass_kg"),
        bone_mass_kg=data.get("bone_mass_kg"),
        body_water_percentage=data.get("body_water_percentage"),
    )
    db.add(body)
    await db.commit()


async def _save_workout_data(data: dict, user: User, target_date: date, db: AsyncSession):
    """Save workout data."""
    workout = WorkoutData(
        user_id=user.id,
        date=target_date,
        workout_type=data.get("workout_type"),
        duration_minutes=data.get("duration_minutes"),
        location=data.get("location"),
        active_calories=data.get("active_calories"),
        total_calories=data.get("total_calories"),
        avg_heart_rate=data.get("avg_heart_rate"),
        max_heart_rate=data.get("max_heart_rate"),
        effort_score=data.get("effort_score"),
        effort_label=data.get("effort_label"),
    )
    db.add(workout)
    await db.commit()
