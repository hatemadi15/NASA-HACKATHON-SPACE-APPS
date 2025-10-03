"""
API v1 router configuration
"""

from fastapi import APIRouter
from app.api.v1.endpoints import simulation, nasa_data

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(simulation.router, prefix="/simulation", tags=["simulation"])
api_router.include_router(nasa_data.router, prefix="/nasa", tags=["nasa-data"])
