"""
Enhanced database models for user management, authentication, and persistence
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import uuid

from app.core.database import Base

class User(Base):
    """User model for authentication and profile management"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    simulations = relationship("Simulation", back_populates="user")
    game_scores = relationship("DeflectionGameScoreDB", back_populates="user")
    exports = relationship("SimulationExport", back_populates="user")

class Simulation(Base):
    """Persistent simulation results"""
    __tablename__ = "simulations"
    
    id = Column(Integer, primary_key=True, index=True)
    simulation_id = Column(String(36), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Nullable for anonymous users
    
    # Simulation parameters
    asteroid_data = Column(JSON, nullable=False)  # Asteroid parameters
    impact_location = Column(JSON, nullable=False)  # Impact location data
    simulation_request = Column(JSON, nullable=False)  # Full request data
    
    # Results
    impact_result = Column(JSON, nullable=False)  # Impact calculations
    damage_assessment = Column(JSON, nullable=False)  # Damage assessment
    trajectory_data = Column(JSON, nullable=True)  # Trajectory points
    impact_zones = Column(JSON, nullable=True)  # Environmental zones
    mitigation_result = Column(JSON, nullable=True)  # Mitigation results
    warnings = Column(JSON, nullable=True)  # System warnings
    
    # Metadata
    simulation_metadata = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="simulations")
    exports = relationship("SimulationExport", back_populates="simulation")

class DeflectionGameScoreDB(Base):
    """Persistent deflection game scores"""
    __tablename__ = "deflection_game_scores"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Nullable for anonymous players
    player_name = Column(String(100), nullable=False)
    score = Column(Integer, nullable=False)
    
    # Game details
    asteroid_mass = Column(Float, nullable=False)
    asteroid_diameter = Column(Float, nullable=False)
    asteroid_velocity = Column(Float, nullable=False)
    deflection_method = Column(String(50), nullable=False)
    dv_applied = Column(Float, nullable=False)
    success = Column(Boolean, nullable=False)
    
    # Game session data
    game_session_id = Column(String(36), nullable=True)
    difficulty_level = Column(String(20), default="normal")
    time_taken = Column(Float, nullable=True)  # Seconds
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="game_scores")

class SimulationExport(Base):
    """Track exported simulations (PDF, images, etc.)"""
    __tablename__ = "simulation_exports"
    
    id = Column(Integer, primary_key=True, index=True)
    simulation_id = Column(Integer, ForeignKey("simulations.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    export_type = Column(String(20), nullable=False)  # "pdf", "image", "json", "csv"
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=True)  # Bytes
    export_format = Column(String(50), nullable=True)  # "A4", "PNG", "JSON", etc.
    
    # Export parameters
    include_trajectory = Column(Boolean, default=True)
    include_zones = Column(Boolean, default=True)
    include_mitigation = Column(Boolean, default=True)
    custom_title = Column(String(200), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)  # For cleanup
    
    # Relationships
    simulation = relationship("Simulation", back_populates="exports")
    user = relationship("User", back_populates="exports")

class UserSession(Base):
    """Track user sessions for analytics and security"""
    __tablename__ = "user_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    session_token = Column(String(255), unique=True, index=True, nullable=False)
    
    # Session data
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    user_agent = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Activity tracking
    simulations_run = Column(Integer, default=0)
    game_scores_submitted = Column(Integer, default=0)
    exports_created = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_activity = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)

class SystemLog(Base):
    """System logs for monitoring and debugging"""
    __tablename__ = "system_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    level = Column(String(20), nullable=False)  # "info", "warning", "error", "critical"
    component = Column(String(50), nullable=False)  # "simulation", "nasa_client", "auth", etc.
    message = Column(Text, nullable=False)
    
    # Context data
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    simulation_id = Column(String(36), nullable=True)
    request_id = Column(String(36), nullable=True)
    
    # Additional data
    extra_data = Column(JSON, nullable=True)
    stack_trace = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
