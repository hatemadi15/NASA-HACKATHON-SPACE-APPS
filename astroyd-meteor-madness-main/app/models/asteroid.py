"""
Asteroid data models for impact simulation
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Literal
from enum import Enum
import math

class AsteroidComposition(str, Enum):
    """Asteroid composition types"""
    IRON = "iron"
    STONY = "stony"
    CARBONACEOUS = "carbonaceous"
    MIXED = "mixed"

class Asteroid(BaseModel):
    """Asteroid parameters for impact simulation"""
    
    # Basic properties
    mass: float = Field(..., gt=0, description="Mass in kilograms")
    diameter: float = Field(..., gt=0, description="Diameter in meters")
    velocity: float = Field(..., gt=0, description="Impact velocity in m/s")
    impact_angle: float = Field(..., ge=0, le=90, description="Impact angle in degrees")
    composition: AsteroidComposition = Field(..., description="Asteroid composition type")
    
    # Optional properties
    density: Optional[float] = Field(None, gt=0, description="Density in kg/m³")
    porosity: Optional[float] = Field(0.0, ge=0, le=1, description="Porosity (0-1)")
    strength: Optional[float] = Field(None, gt=0, description="Material strength in Pa")
    
    @validator('density')
    def set_density(cls, v, values):
        """Set default density based on composition if not provided"""
        if v is None:
            composition = values.get('composition')
            if composition == AsteroidComposition.IRON:
                return 7800.0  # kg/m³
            elif composition == AsteroidComposition.STONY:
                return 3000.0  # kg/m³
            elif composition == AsteroidComposition.CARBONACEOUS:
                return 2000.0  # kg/m³
            else:  # MIXED
                return 4000.0  # kg/m³
        return v
    
    @validator('diameter')
    def validate_diameter(cls, v, values):
        """Validate diameter against mass and density"""
        mass = values.get('mass')
        density = values.get('density')
        if mass and density:
            expected_diameter = 2 * ((3 * mass) / (4 * math.pi * density)) ** (1/3)
            if abs(v - expected_diameter) / expected_diameter > 0.1:  # 10% tolerance
                raise ValueError("Diameter doesn't match mass and density")
        return v
    
    @property
    def kinetic_energy(self) -> float:
        """Calculate kinetic energy in Joules"""
        return 0.5 * self.mass * self.velocity ** 2
    
    @property
    def kinetic_energy_megatons(self) -> float:
        """Calculate kinetic energy in megatons of TNT"""
        return self.kinetic_energy / (4.184e15)  # 1 megaton = 4.184e15 J
    
    class Config:
        use_enum_values = True
        json_encoders = {
            float: lambda v: round(v, 6) if v is not None else None
        }

class AsteroidCreate(Asteroid):
    """Asteroid creation model"""
    pass

class AsteroidResponse(Asteroid):
    """Asteroid response model with calculated properties"""
    kinetic_energy: float
    kinetic_energy_megatons: float
    
    class Config:
        from_attributes = True
