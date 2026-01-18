"""API routes for health dashboard."""
from .auth import router as auth_router
from .metrics import router as metrics_router
from .food import router as food_router
from .screenshots import router as screenshots_router

__all__ = ["auth_router", "metrics_router", "food_router", "screenshots_router"]
