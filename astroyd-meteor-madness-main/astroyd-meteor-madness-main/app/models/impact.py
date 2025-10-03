"""
Impact location and result data models
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from enum import Enum
import math
from app.models.asteroid import AsteroidCreate, AsteroidResponse

class TerrainType(str, Enum):
	"""Terrain types for impact analysis"""
	OCEAN = "ocean"
	LAND = "land"
	URBAN = "urban"
	RURAL = "rural"
	MOUNTAIN = "mountain"
	DESERT = "desert"
	FOREST = "forest"
	ICE = "ice"

class ImpactLocation(BaseModel):
	"""Impact location parameters"""
	# Geographic coordinates
	latitude: float = Field(..., ge=-90, le=90, description="Latitude in degrees")
	longitude: float = Field(..., ge=-180, le=180, description="Longitude in degrees")
	elevation: float = Field(0.0, description="Elevation above sea level in meters")
	# Terrain characteristics
	terrain_type: TerrainType = Field(..., description="Primary terrain type")
	water_depth: Optional[float] = Field(None, ge=0, description="Water depth in meters (for ocean impacts)")
	# Population and infrastructure
	population_density: float = Field(0.0, ge=0, description="Population density per km²")
	infrastructure_density: float = Field(0.0, ge=0, le=1, description="Infrastructure density (0-1)")
	# Additional properties
	soil_type: Optional[str] = Field(None, description="Soil composition type")
	bedrock_depth: Optional[float] = Field(None, ge=0, description="Bedrock depth in meters")

	@validator('water_depth')
	def validate_water_depth(cls, v, values):
		"""Validate water depth for ocean impacts"""
		terrain_type = values.get('terrain_type')
		if terrain_type == TerrainType.OCEAN and v is None:
			raise ValueError("Water depth required for ocean impacts")
		return v

class ImpactResult(BaseModel):
	"""Impact simulation results"""
	# Crater characteristics
	crater_diameter: float = Field(..., ge=0, description="Crater diameter in meters")
	crater_depth: float = Field(..., ge=0, description="Crater depth in meters")
	crater_volume: float = Field(..., ge=0, description="Crater volume in m³")
	# Blast effects
	blast_radius: float = Field(..., ge=0, description="Blast radius in meters")
	thermal_radius: float = Field(..., ge=0, description="Thermal radiation radius in meters")
	seismic_magnitude: float = Field(..., description="Seismic magnitude (Richter scale)")
	# Environmental effects
	tsunami_height: Optional[float] = Field(None, ge=0, description="Tsunami height in meters")
	fireball_radius: float = Field(..., ge=0, description="Fireball radius in meters")
	atmospheric_effects: Dict[str, Any] = Field(default_factory=dict, description="Atmospheric impact effects")
	# Damage assessment
	evacuation_radius: float = Field(..., ge=0, description="Recommended evacuation radius in meters")
	affected_area: float = Field(..., ge=0, description="Total affected area in km²")

	class Config:
		json_encoders = {
			float: lambda v: round(v, 6) if v is not None else None
		}

class DamageAssessment(BaseModel):
	"""Human and infrastructure damage assessment"""
	# Human casualties
	estimated_casualties: int = Field(..., ge=0, description="Estimated number of casualties")
	injured_count: int = Field(..., ge=0, description="Estimated number of injured")
	displaced_count: int = Field(..., ge=0, description="Estimated number of displaced people")
	# Infrastructure damage
	infrastructure_damage_cost: float = Field(..., ge=0, description="Infrastructure damage cost in USD")
	buildings_destroyed: int = Field(..., ge=0, description="Number of buildings destroyed")
	buildings_damaged: int = Field(..., ge=0, description="Number of buildings damaged")
	# Environmental impact
	environmental_impact_score: float = Field(..., ge=0, le=10, description="Environmental impact score (0-10)")
	ecosystem_affected_area: float = Field(..., ge=0, description="Ecosystem affected area in km²")
	# Economic impact
	total_economic_cost: float = Field(..., ge=0, description="Total economic cost in USD")
	recovery_time_years: float = Field(..., ge=0, description="Estimated recovery time in years")

	class Config:
		json_encoders = {
			float: lambda v: round(v, 2) if v is not None else None
		}

class SimulationRequest(BaseModel):
	"""Complete simulation request"""
	asteroid: AsteroidCreate
	impact_location: ImpactLocation
	use_nasa_data: bool = Field(False, description="If true, enrich location using NASA/USGS data")
	use_ml: bool = Field(False, description="If true, use ML enhancer on damage predictions")
	simulation_id: Optional[str] = Field(None, description="Optional simulation ID")
	# Mitigation / deflection parameters (simple MVP)
	# Apply a delta-v (m/s) prior to impact to simulate kinetic deflection
	dv_mps: float = Field(0.0, ge=0.0, description="Mitigation delta-v to reduce impact velocity (m/s)")
	deflection_method: Optional[str] = Field(None, description="Mitigation method label, e.g., 'kinetic_impactor'")

class SimulationResponse(BaseModel):
	"""Complete simulation response"""
	simulation_id: str
	asteroid: AsteroidResponse
	impact_location: ImpactLocation
	impact_result: ImpactResult
	damage_assessment: DamageAssessment
	simulation_metadata: Dict[str, Any] = Field(default_factory=dict)
	# Convenience exposure for UI overlays
	population_density: float | None = Field(None, description="Population density per km² at impact location")
	elevation: float | None = Field(None, description="Elevation (m) at impact location")
	terrain_type: str | None = Field(None, description="Terrain type at impact location")

	class Config:
		from_attributes = True
