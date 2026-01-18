"""Food logging API routes."""
from datetime import date, datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from ..models import User, FoodLog, get_db
from ..services.claude_ai import ClaudeAIService
from .auth import get_current_user

router = APIRouter(prefix="/food", tags=["food"])


class FoodLogCreate(BaseModel):
    description: str
    meal_type: str = "snack"  # breakfast, lunch, dinner, snack


class FoodLogResponse(BaseModel):
    id: int
    date: date
    meal_type: str
    description: str
    estimated_calories: Optional[int]
    estimated_protein_g: Optional[float]
    estimated_carbs_g: Optional[float]
    estimated_fat_g: Optional[float]
    ai_notes: Optional[str]
    logged_at: datetime

    class Config:
        from_attributes = True


class DailyFoodSummary(BaseModel):
    date: date
    total_calories: int
    total_protein_g: float
    total_carbs_g: float
    total_fat_g: float
    meals: list[FoodLogResponse]
    target_calories: int
    remaining_calories: int


@router.post("/log", response_model=FoodLogResponse)
async def log_food(
    food_data: FoodLogCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Log a food item with AI calorie estimation."""
    # Get calorie estimate from Claude
    claude_service = ClaudeAIService()

    try:
        estimate = await claude_service.estimate_food_calories(
            food_data.description, food_data.meal_type
        )
    except Exception as e:
        # If AI fails, still log the food without estimates
        estimate = {}

    # Create food log
    food_log = FoodLog(
        user_id=current_user.id,
        date=date.today(),
        meal_type=food_data.meal_type,
        description=food_data.description,
        estimated_calories=estimate.get("estimated_calories"),
        estimated_protein_g=estimate.get("estimated_protein_g"),
        estimated_carbs_g=estimate.get("estimated_carbs_g"),
        estimated_fat_g=estimate.get("estimated_fat_g"),
        ai_notes=estimate.get("ai_notes"),
    )

    db.add(food_log)
    await db.commit()
    await db.refresh(food_log)

    return food_log


@router.get("/today", response_model=DailyFoodSummary)
async def get_today_food(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get today's food log summary."""
    return await get_food_by_date(date.today(), current_user, db)


@router.get("/date/{target_date}", response_model=DailyFoodSummary)
async def get_food_by_date(
    target_date: date,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get food log for a specific date."""
    result = await db.execute(
        select(FoodLog)
        .where(
            and_(
                FoodLog.user_id == current_user.id,
                FoodLog.date == target_date,
            )
        )
        .order_by(FoodLog.logged_at)
    )
    meals = result.scalars().all()

    # Calculate totals
    total_calories = sum(m.estimated_calories or 0 for m in meals)
    total_protein = sum(m.estimated_protein_g or 0 for m in meals)
    total_carbs = sum(m.estimated_carbs_g or 0 for m in meals)
    total_fat = sum(m.estimated_fat_g or 0 for m in meals)

    return DailyFoodSummary(
        date=target_date,
        total_calories=total_calories,
        total_protein_g=round(total_protein, 1),
        total_carbs_g=round(total_carbs, 1),
        total_fat_g=round(total_fat, 1),
        meals=list(meals),
        target_calories=current_user.daily_calorie_target,
        remaining_calories=current_user.daily_calorie_target - total_calories,
    )


@router.delete("/{food_id}")
async def delete_food_log(
    food_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a food log entry."""
    result = await db.execute(
        select(FoodLog).where(
            and_(
                FoodLog.id == food_id,
                FoodLog.user_id == current_user.id,
            )
        )
    )
    food_log = result.scalar_one_or_none()

    if not food_log:
        raise HTTPException(status_code=404, detail="Food log not found")

    await db.delete(food_log)
    await db.commit()

    return {"message": "Food log deleted"}


@router.get("/history")
async def get_food_history(
    days: int = 7,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get food log history with daily summaries."""
    from datetime import timedelta

    start_date = date.today() - timedelta(days=days)

    result = await db.execute(
        select(FoodLog)
        .where(
            and_(
                FoodLog.user_id == current_user.id,
                FoodLog.date >= start_date,
            )
        )
        .order_by(FoodLog.date.desc(), FoodLog.logged_at)
    )
    all_logs = result.scalars().all()

    # Group by date
    daily_summaries = {}
    for log in all_logs:
        date_key = log.date.isoformat()
        if date_key not in daily_summaries:
            daily_summaries[date_key] = {
                "date": date_key,
                "total_calories": 0,
                "total_protein_g": 0,
                "total_carbs_g": 0,
                "total_fat_g": 0,
                "meal_count": 0,
            }
        summary = daily_summaries[date_key]
        summary["total_calories"] += log.estimated_calories or 0
        summary["total_protein_g"] += log.estimated_protein_g or 0
        summary["total_carbs_g"] += log.estimated_carbs_g or 0
        summary["total_fat_g"] += log.estimated_fat_g or 0
        summary["meal_count"] += 1

    return {
        "target_calories": current_user.daily_calorie_target,
        "daily_summaries": list(daily_summaries.values()),
    }
