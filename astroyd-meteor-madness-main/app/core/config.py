"""
Configuration settings for the NASA Meteor Simulator
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
import os

class Settings(BaseSettings):
	"""Application settings"""
	# Database
	DATABASE_URL: str = Field(default="sqlite:///./meteor_madness.db", env="DATABASE_URL")
	REDIS_URL: str = "redis://localhost:6379/0"
	# NASA API Configuration
	NASA_API_KEY: Optional[str] = None
	NASA_EARTHDATA_USERNAME: Optional[str] = None
	NASA_EARTHDATA_PASSWORD: Optional[str] = None
	NASA_EARTHDATA_TOKEN: Optional[str] = None
	# Application Settings
	DEBUG: bool = True
	SECRET_KEY: str = "your-secret-key-change-in-production"
	API_V1_STR: str = "/api/v1"
	# Demo and CORS
	DEMO_MODE: bool = True
	CORS_ALLOW_ORIGINS: str = "*"  # comma-separated
	# Caching
	CACHE_TTL_SECONDS: int = 300
	# External APIs
	USGS_API_KEY: Optional[str] = None
	NOAA_API_KEY: Optional[str] = None
	# Celery Configuration
	CELERY_BROKER_URL: str = "redis://localhost:6379/0"
	CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
	# Physics Constants
	EARTH_RADIUS: float = 6371000.0  # meters
	EARTH_MASS: float = 5.972e24  # kg
	GRAVITATIONAL_CONSTANT: float = 6.67430e-11  # m³/kg/s²
	# Game Settings
	DEFLECTION_GAME_MAX_SCORE: int = 10000
	LEADERBOARD_SIZE: int = 100
	
	class Config:
		env_file = ".env"
		case_sensitive = True

# Global settings instance
settings = Settings()
