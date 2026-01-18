"""Health metrics API routes."""
from datetime import date, datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from ..models import (
    User,
    DailyMetrics,
    SleepData,
    WorkoutData,
    BodyComposition,
    get_db,
)
from .auth import get_current_user

router = APIRouter(prefix="/metrics", tags=["metrics"])


# Response models
class DailyMetricsResponse(BaseModel):
    id: int
    date: date
    recovery_score: Optional[float]
    hrv: Optional[float]
    resting_heart_rate: Optional[float]
    respiratory_rate: Optional[float]
    sleep_performance: Optional[float]
    steps: Optional[int]
    calories_burned: Optional[int]
    vo2_max: Optional[float]

    class Config:
        from_attributes = True


class SleepDataResponse(BaseModel):
    id: int
    date: date
    total_duration_minutes: Optional[int]
    actual_sleep_minutes: Optional[int]
    awake_minutes: Optional[int]
    light_sleep_minutes: Optional[int]
    deep_sleep_minutes: Optional[int]
    rem_sleep_minutes: Optional[int]
    awake_percentage: Optional[float]
    light_sleep_percentage: Optional[float]
    deep_sleep_percentage: Optional[float]
    rem_sleep_percentage: Optional[float]

    class Config:
        from_attributes = True


class WorkoutResponse(BaseModel):
    id: int
    date: date
    workout_type: Optional[str]
    duration_minutes: Optional[int]
    active_calories: Optional[int]
    total_calories: Optional[int]
    avg_heart_rate: Optional[int]
    effort_score: Optional[int]
    effort_label: Optional[str]

    class Config:
        from_attributes = True


class BodyCompositionResponse(BaseModel):
    id: int
    date: date
    weight_kg: float
    weight_change_kg: Optional[float]
    bmi: Optional[float]
    body_fat_percentage: Optional[float]
    skeletal_muscle_mass_kg: Optional[float]
    bone_mass_kg: Optional[float]
    body_water_percentage: Optional[float]

    class Config:
        from_attributes = True


class DashboardSummary(BaseModel):
    """Complete dashboard data for a date."""

    date: date
    metrics: Optional[DailyMetricsResponse]
    sleep: Optional[SleepDataResponse]
    body: Optional[BodyCompositionResponse]
    workouts: list[WorkoutResponse]
    weight_progress: dict
    calorie_summary: dict


class TrendData(BaseModel):
    """Trend data for charts."""

    dates: list[str]
    weight: list[Optional[float]]
    body_fat: list[Optional[float]]
    muscle_mass: list[Optional[float]]
    recovery: list[Optional[float]]
    sleep_hours: list[Optional[float]]
    steps: list[Optional[int]]
    calories_burned: list[Optional[int]]


@router.get("/today", response_model=DashboardSummary)
async def get_today_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get today's complete health summary."""
    return await get_date_summary(date.today(), current_user, db)


@router.get("/date/{target_date}", response_model=DashboardSummary)
async def get_date_summary(
    target_date: date,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get health summary for a specific date."""
    # Get daily metrics
    metrics_result = await db.execute(
        select(DailyMetrics).where(
            and_(
                DailyMetrics.user_id == current_user.id,
                DailyMetrics.date == target_date,
            )
        )
    )
    metrics = metrics_result.scalar_one_or_none()

    # Get sleep data
    sleep_result = await db.execute(
        select(SleepData).where(
            and_(
                SleepData.user_id == current_user.id,
                SleepData.date == target_date,
            )
        )
    )
    sleep = sleep_result.scalar_one_or_none()

    # Get body composition
    body_result = await db.execute(
        select(BodyComposition).where(
            and_(
                BodyComposition.user_id == current_user.id,
                BodyComposition.date == target_date,
            )
        )
    )
    body = body_result.scalar_one_or_none()

    # Get workouts
    workouts_result = await db.execute(
        select(WorkoutData).where(
            and_(
                WorkoutData.user_id == current_user.id,
                WorkoutData.date == target_date,
            )
        )
    )
    workouts = workouts_result.scalars().all()

    # Calculate weight progress
    weight_progress = await _get_weight_progress(current_user, db)

    # Calculate calorie summary
    calorie_summary = await _get_calorie_summary(current_user, target_date, db)

    return DashboardSummary(
        date=target_date,
        metrics=metrics,
        sleep=sleep,
        body=body,
        workouts=list(workouts),
        weight_progress=weight_progress,
        calorie_summary=calorie_summary,
    )


@router.get("/trends", response_model=TrendData)
async def get_trends(
    period: str = Query("week", enum=["week", "month", "3months"]),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get trend data for charts."""
    # Calculate date range
    today = date.today()
    if period == "week":
        start_date = today - timedelta(days=7)
    elif period == "month":
        start_date = today - timedelta(days=30)
    else:  # 3months
        start_date = today - timedelta(days=90)

    # Generate all dates in range
    dates = []
    current = start_date
    while current <= today:
        dates.append(current)
        current += timedelta(days=1)

    # Fetch all data
    metrics_result = await db.execute(
        select(DailyMetrics)
        .where(
            and_(
                DailyMetrics.user_id == current_user.id,
                DailyMetrics.date >= start_date,
                DailyMetrics.date <= today,
            )
        )
        .order_by(DailyMetrics.date)
    )
    metrics_by_date = {m.date: m for m in metrics_result.scalars().all()}

    sleep_result = await db.execute(
        select(SleepData)
        .where(
            and_(
                SleepData.user_id == current_user.id,
                SleepData.date >= start_date,
                SleepData.date <= today,
            )
        )
        .order_by(SleepData.date)
    )
    sleep_by_date = {s.date: s for s in sleep_result.scalars().all()}

    body_result = await db.execute(
        select(BodyComposition)
        .where(
            and_(
                BodyComposition.user_id == current_user.id,
                BodyComposition.date >= start_date,
                BodyComposition.date <= today,
            )
        )
        .order_by(BodyComposition.date)
    )
    body_by_date = {b.date: b for b in body_result.scalars().all()}

    # Build trend arrays
    weight = []
    body_fat = []
    muscle_mass = []
    recovery = []
    sleep_hours = []
    steps = []
    calories_burned = []

    for d in dates:
        # Body composition
        body = body_by_date.get(d)
        weight.append(body.weight_kg if body else None)
        body_fat.append(body.body_fat_percentage if body else None)
        muscle_mass.append(body.skeletal_muscle_mass_kg if body else None)

        # Daily metrics
        metrics = metrics_by_date.get(d)
        recovery.append(metrics.recovery_score if metrics else None)
        steps.append(metrics.steps if metrics else None)
        calories_burned.append(metrics.calories_burned if metrics else None)

        # Sleep
        sleep = sleep_by_date.get(d)
        if sleep and sleep.actual_sleep_minutes:
            sleep_hours.append(round(sleep.actual_sleep_minutes / 60, 2))
        else:
            sleep_hours.append(None)

    return TrendData(
        dates=[d.isoformat() for d in dates],
        weight=weight,
        body_fat=body_fat,
        muscle_mass=muscle_mass,
        recovery=recovery,
        sleep_hours=sleep_hours,
        steps=steps,
        calories_burned=calories_burned,
    )


@router.get("/weight-history")
async def get_weight_history(
    days: int = Query(30, ge=7, le=365),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get weight history for progress tracking."""
    start_date = date.today() - timedelta(days=days)

    result = await db.execute(
        select(BodyComposition)
        .where(
            and_(
                BodyComposition.user_id == current_user.id,
                BodyComposition.date >= start_date,
            )
        )
        .order_by(BodyComposition.date)
    )
    records = result.scalars().all()

    return {
        "target_weight": current_user.target_weight,
        "history": [
            {
                "date": r.date.isoformat(),
                "weight": r.weight_kg,
                "body_fat": r.body_fat_percentage,
                "muscle_mass": r.skeletal_muscle_mass_kg,
            }
            for r in records
        ],
    }


async def _get_weight_progress(user: User, db: AsyncSession) -> dict:
    """Calculate weight progress toward goal."""
    # Get latest weight
    latest_result = await db.execute(
        select(BodyComposition)
        .where(BodyComposition.user_id == user.id)
        .order_by(BodyComposition.date.desc())
        .limit(1)
    )
    latest = latest_result.scalar_one_or_none()

    # Get weight from 7 days ago
    week_ago = date.today() - timedelta(days=7)
    week_ago_result = await db.execute(
        select(BodyComposition)
        .where(
            and_(
                BodyComposition.user_id == user.id,
                BodyComposition.date <= week_ago,
            )
        )
        .order_by(BodyComposition.date.desc())
        .limit(1)
    )
    week_ago_record = week_ago_result.scalar_one_or_none()

    current_weight = latest.weight_kg if latest else None
    target_weight = user.target_weight
    week_change = None

    if latest and week_ago_record:
        week_change = round(latest.weight_kg - week_ago_record.weight_kg, 2)

    to_goal = None
    if current_weight and target_weight:
        to_goal = round(current_weight - target_weight, 2)

    return {
        "current": current_weight,
        "target": target_weight,
        "to_goal": to_goal,
        "week_change": week_change,
    }


async def _get_calorie_summary(
    user: User, target_date: date, db: AsyncSession
) -> dict:
    """Get calorie summary for a date."""
    from ..models import FoodLog

    # Get calories consumed
    food_result = await db.execute(
        select(func.sum(FoodLog.estimated_calories)).where(
            and_(
                FoodLog.user_id == user.id,
                FoodLog.date == target_date,
            )
        )
    )
    consumed = food_result.scalar() or 0

    # Get calories burned from daily metrics
    metrics_result = await db.execute(
        select(DailyMetrics.calories_burned).where(
            and_(
                DailyMetrics.user_id == user.id,
                DailyMetrics.date == target_date,
            )
        )
    )
    burned = metrics_result.scalar() or 0

    return {
        "consumed": consumed,
        "burned": burned,
        "target": user.daily_calorie_target,
        "net": consumed - burned,
        "remaining": user.daily_calorie_target - consumed,
    }
