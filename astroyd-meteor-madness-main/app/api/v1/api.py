"""
API v1 router configuration with all endpoints
"""

from fastapi import APIRouter
from app.api.v1.endpoints import simulation, nasa_data, auth, export

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(simulation.router, prefix="/simulation", tags=["simulation"])
api_router.include_router(nasa_data.router, prefix="/nasa", tags=["nasa-data"])
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(export.router, prefix="/export", tags=["export"])
