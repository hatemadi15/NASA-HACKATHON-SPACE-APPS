"""
Main FastAPI application entry point
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os
from dotenv import load_dotenv

from app.core.config import settings
from app.api.v1.api import api_router
from app.core.database import create_tables

# Load environment variables
load_dotenv()  # .env
load_dotenv(".env.local", override=True)  # optional local overrides

# Create database tables
create_tables()

# Initialize FastAPI app
app = FastAPI(
    title="NASA Meteor Simulator API",
    description="Enhanced backend API for meteor impact simulation with NASA data integration, trajectory modeling, and deflection game",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
origins = [o.strip() for o in settings.CORS_ALLOW_ORIGINS.split(",")] if settings.CORS_ALLOW_ORIGINS else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "NASA Meteor Simulator API v2.0",
        "version": "2.0.0",
        "docs": "/docs",
        "status": "operational",
        "features": [
            "Enhanced impact simulation",
            "Trajectory modeling", 
            "Environmental impact zones",
            "NEO-based asteroid modeling",
            "Deflection game with leaderboards",
            "Mitigation solutions",
            "NASA CAD/Sentry integration"
        ]
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "meteor-simulator", "version": "2.0.0"}

@app.get("/version")
async def version():
    """Version and mode endpoint"""
    return {"version": "2.0.0", "demo_mode": settings.DEMO_MODE}

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
