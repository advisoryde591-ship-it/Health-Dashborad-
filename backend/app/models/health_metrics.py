"""SQLAlchemy models for health metrics."""
from datetime import datetime, date
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    Date,
    Text,
    ForeignKey,
    Boolean,
    Enum as SQLEnum,
)
from sqlalchemy.orm import relationship
import enum
from .database import Base


class User(Base):
    """User account model."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    target_weight = Column(Float, default=76.0)
    daily_calorie_target = Column(Integer, default=2000)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    # Relationships
    daily_metrics = relationship("DailyMetrics", back_populates="user")
    sleep_data = relationship("SleepData", back_populates="user")
    workouts = relationship("WorkoutData", back_populates="user")
    body_compositions = relationship("BodyComposition", back_populates="user")
    food_logs = relationship("FoodLog", back_populates="user")
    screenshots = relationship("Screenshot", back_populates="user")


class DailyMetrics(Base):
    """Daily aggregated health metrics from Whoop."""

    __tablename__ = "daily_metrics"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    date = Column(Date, index=True, nullable=False)

    # Recovery metrics (from Whoop)
    recovery_score = Column(Float)  # Percentage 0-100
    hrv = Column(Float)  # Heart Rate Variability in ms
    resting_heart_rate = Column(Float)  # BPM
    respiratory_rate = Column(Float)  # Breaths per minute
    sleep_performance = Column(Float)  # Percentage

    # Activity metrics
    steps = Column(Integer)
    calories_burned = Column(Integer)
    vo2_max = Column(Float)

    # HR Zones (weekly tracking)
    hr_zones_1_3_minutes = Column(Integer)  # Minutes in zones 1-3
    hr_zones_4_5_minutes = Column(Integer)  # Minutes in zones 4-5

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="daily_metrics")


class SleepData(Base):
    """Sleep tracking data from Whoop."""

    __tablename__ = "sleep_data"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    date = Column(Date, index=True, nullable=False)

    # Sleep times
    sleep_start = Column(DateTime)  # When went to bed
    sleep_end = Column(DateTime)  # When woke up
    total_duration_minutes = Column(Integer)  # Total time in bed
    actual_sleep_minutes = Column(Integer)  # Actual sleep (excluding awake)

    # Sleep stages (in minutes)
    awake_minutes = Column(Integer)
    light_sleep_minutes = Column(Integer)
    deep_sleep_minutes = Column(Integer)  # SWS
    rem_sleep_minutes = Column(Integer)

    # Sleep stages (percentages)
    awake_percentage = Column(Float)
    light_sleep_percentage = Column(Float)
    deep_sleep_percentage = Column(Float)
    rem_sleep_percentage = Column(Float)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="sleep_data")


class WorkoutType(enum.Enum):
    """Types of workouts."""

    INDOOR_CYCLE = "indoor_cycle"
    OUTDOOR_RUN = "outdoor_run"
    OUTDOOR_CYCLE = "outdoor_cycle"
    STRENGTH_TRAINING = "strength_training"
    SWIMMING = "swimming"
    WALKING = "walking"
    HIIT = "hiit"
    YOGA = "yoga"
    OTHER = "other"


class WorkoutData(Base):
    """Workout/activity data from Apple Watch."""

    __tablename__ = "workout_data"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    date = Column(Date, index=True, nullable=False)

    # Workout details
    workout_type = Column(String(50))  # e.g., "Indoor Cycle"
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    duration_minutes = Column(Integer)
    location = Column(String(100))

    # Calories
    active_calories = Column(Integer)
    total_calories = Column(Integer)

    # Heart rate
    avg_heart_rate = Column(Integer)
    max_heart_rate = Column(Integer)
    min_heart_rate = Column(Integer)

    # Effort/intensity
    effort_score = Column(Integer)  # 1-10 scale
    effort_label = Column(String(20))  # e.g., "Easy", "Moderate", "Hard"

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="workouts")


class BodyComposition(Base):
    """Body composition data from smart scale."""

    __tablename__ = "body_composition"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    date = Column(Date, index=True, nullable=False)
    measured_at = Column(DateTime)

    # Weight metrics
    weight_kg = Column(Float, nullable=False)
    weight_change_kg = Column(Float)  # Change from previous measurement
    bmi = Column(Float)

    # Body composition
    body_fat_percentage = Column(Float)
    skeletal_muscle_mass_kg = Column(Float)
    bone_mass_kg = Column(Float)
    body_water_percentage = Column(Float)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="body_compositions")


class FoodLog(Base):
    """Food/meal logging for calorie tracking."""

    __tablename__ = "food_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    date = Column(Date, index=True, nullable=False)
    logged_at = Column(DateTime, default=datetime.utcnow)

    # Meal info
    meal_type = Column(String(20))  # breakfast, lunch, dinner, snack
    description = Column(Text, nullable=False)

    # Nutritional info (estimated by AI)
    estimated_calories = Column(Integer)
    estimated_protein_g = Column(Float)
    estimated_carbs_g = Column(Float)
    estimated_fat_g = Column(Float)

    # AI analysis
    ai_notes = Column(Text)  # AI feedback/suggestions

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="food_logs")


class ScreenshotType(enum.Enum):
    """Types of screenshots."""

    WHOOP_RECOVERY = "whoop_recovery"
    WHOOP_SLEEP = "whoop_sleep"
    WHOOP_DASHBOARD = "whoop_dashboard"
    SCALE = "scale"
    APPLE_WORKOUT = "apple_workout"
    UNKNOWN = "unknown"


class Screenshot(Base):
    """Screenshot metadata and processing status."""

    __tablename__ = "screenshots"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    date = Column(Date, index=True, nullable=False)

    # File info
    filename = Column(String(255), nullable=False)
    google_drive_id = Column(String(100))
    screenshot_type = Column(String(30))

    # Processing status
    processed = Column(Boolean, default=False)
    processed_at = Column(DateTime)
    processing_error = Column(Text)

    # Extracted data (JSON)
    extracted_data = Column(Text)  # JSON string of extracted metrics

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="screenshots")
