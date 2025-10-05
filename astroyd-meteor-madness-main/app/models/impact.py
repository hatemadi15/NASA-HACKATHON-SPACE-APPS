"""
Enhanced asteroid and impact data models with trajectory and environmental zones
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Tuple
from enum import Enum
import math
from datetime import datetime

class AsteroidComposition(str, Enum):
    """Asteroid composition types"""
    IRON = "iron"
    STONY = "stony"
    CARBONACEOUS = "carbonaceous"
    MIXED = "mixed"

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
    
    # NEO-derived properties
    neo_id: Optional[str] = Field(None, description="NASA NEO ID")
    designation: Optional[str] = Field(None, description="Asteroid designation")
    orbital_elements: Optional[Dict[str, float]] = Field(None, description="Orbital elements")
    
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
    
    @property
    def kinetic_energy(self) -> float:
        """Calculate kinetic energy in Joules"""
        return 0.5 * self.mass * self.velocity ** 2
    
    @property
    def kinetic_energy_megatons(self) -> float:
        """Calculate kinetic energy in megatons of TNT"""
        return self.kinetic_energy / (4.184e15)  # 1 megaton = 4.184e15 J

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

class TrajectoryPoint(BaseModel):
	"""Single point in asteroid trajectory"""
	timestamp: datetime
	latitude: float
	longitude: float
	altitude: float  # km above Earth
	velocity: float  # m/s
	distance_to_earth: float  # km

class ImpactZone(BaseModel):
	"""Environmental impact zone"""
	zone_type: str = Field(..., description="Zone type: tsunami, seismic, thermal, blast")
	radius: float = Field(..., ge=0, description="Radius in meters")
	intensity: float = Field(..., description="Intensity level (0-10)")
	affected_population: int = Field(0, ge=0, description="Estimated affected population")
	description: str = Field(..., description="Zone description")

class ImpactResult(BaseModel):
	"""Enhanced impact simulation results"""
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
	# Impact zones
	impact_zones: List[ImpactZone] = Field(default_factory=list, description="Environmental impact zones")
	# Damage assessment
	evacuation_radius: float = Field(..., ge=0, description="Recommended evacuation radius in meters")
	affected_area: float = Field(..., ge=0, description="Total affected area in km²")

class MitigationResult(BaseModel):
	"""Mitigation/deflection result"""
	method: str = Field(..., description="Mitigation method used")
	dv_applied: float = Field(..., description="Delta-v applied in m/s")
	success_probability: float = Field(..., ge=0, le=1, description="Success probability")
	new_trajectory: Optional[List[TrajectoryPoint]] = Field(None, description="New trajectory if deflected")
	miss_distance: Optional[float] = Field(None, description="Closest approach distance if deflected")
	energy_reduction: float = Field(..., description="Energy reduction percentage")

class Warning(BaseModel):
	"""System warning or error"""
	level: str = Field(..., description="Warning level: info, warning, error, critical")
	code: str = Field(..., description="Warning code")
	message: str = Field(..., description="Warning message")
	timestamp: datetime = Field(default_factory=datetime.utcnow)

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

    asteroid: Asteroid
    impact_location: ImpactLocation
    use_nasa_data: bool = Field(False, description="If true, enrich location using NASA/USGS data")
    use_ml: bool = Field(False, description="If true, use ML enhancer on damage predictions")
    simulation_id: Optional[str] = Field(None, description="Optional simulation ID")
    # Mitigation / deflection parameters
    dv_mps: float = Field(0.0, ge=0.0, description="Mitigation delta-v to reduce impact velocity (m/s)")
    deflection_method: Optional[str] = Field(None, description="Mitigation method label")
    calculate_trajectory: bool = Field(True, description="Calculate full trajectory")
    include_zones: bool = Field(True, description="Calculate environmental zones")


class SimulationResponse(BaseModel):
    """Complete simulation response"""

    simulation_id: str
    asteroid: Asteroid
    impact_location: ImpactLocation
    impact_result: ImpactResult
    damage_assessment: DamageAssessment
    mitigation_result: Optional[MitigationResult] = Field(None, description="Mitigation results if applied")
    trajectory: Optional[List[TrajectoryPoint]] = Field(None, description="Asteroid trajectory")
    warnings: List[Warning] = Field(default_factory=list, description="System warnings")
    simulation_metadata: Dict[str, Any] = Field(default_factory=dict)
    # Convenience exposure for UI overlays
    population_density: float | None = Field(None, description="Population density per km² at impact location")
    elevation: float | None = Field(None, description="Elevation (m) at impact location")
    terrain_type: str | None = Field(None, description="Terrain type at impact location")


class AdvancedImpactCalculationOptions(BaseModel):
    """Optional calculations for advanced impact analysis"""

    calculate_human_casualties: bool = Field(True, description="Include human casualty estimates")
    calculate_infrastructure_damage: bool = Field(True, description="Include infrastructure damage estimates")
    calculate_environmental_impact: bool = Field(True, description="Include environmental impact estimates")
    calculate_economic_impact: bool = Field(True, description="Include economic impact estimates")
    calculate_damage_assessment: bool = Field(True, description="Include combined damage assessment summary")
    calculate_kinetic_energy: bool = Field(True, description="Calculate kinetic energy release")
    calculate_atmospheric_entry: bool = Field(True, description="Calculate atmospheric entry effects")
    calculate_crater_formation: bool = Field(True, description="Calculate crater formation metrics")
    calculate_blast_effects: bool = Field(True, description="Calculate blast and thermal effects")
    calculate_tsunami_effects: bool = Field(True, description="Calculate tsunami impacts where applicable")
    recalculate_evacuation_radius: bool = Field(True, description="Recalculate evacuation radius")
    calculate_impact_result: bool = Field(True, description="Recalculate complete impact result")
    use_ml_enhancer: bool = Field(False, description="Apply ML enhancer to damage assessment")


class AdvancedImpactCalculationRequest(BaseModel):
    """Request payload for advanced impact calculations"""

    asteroid: Asteroid
    impact_location: ImpactLocation
    options: AdvancedImpactCalculationOptions = Field(
        default_factory=AdvancedImpactCalculationOptions,
        description="Calculation options"
    )


class AdvancedImpactCalculationResponse(BaseModel):
    """Response payload for advanced impact calculations"""

    kinetic_energy: Optional[Dict[str, float]] = Field(
        None, description="Kinetic energy release in Joules and megatons"
    )
    atmospheric_entry: Optional[Dict[str, float]] = Field(
        None, description="Atmospheric entry characteristics"
    )
    crater_formation: Optional[Dict[str, float]] = Field(
        None, description="Crater formation metrics"
    )
    blast_effects: Optional[Dict[str, float]] = Field(
        None, description="Blast and thermal effects"
    )
    tsunami_effects: Optional[Dict[str, float]] = Field(
        None, description="Tsunami metrics for ocean impacts"
    )
    evacuation_radius: Optional[float] = Field(
        None, description="Recommended evacuation radius in meters"
    )
    impact_result: Optional[Dict[str, Any]] = Field(
        None, description="Complete impact result"
    )
    human_casualties: Optional[Dict[str, int]] = Field(
        None, description="Human casualty estimates"
    )
    infrastructure_damage: Optional[Dict[str, Any]] = Field(
        None, description="Infrastructure damage metrics"
    )
    environmental_impact: Optional[Dict[str, Any]] = Field(
        None, description="Environmental impact metrics"
    )
    economic_impact: Optional[Dict[str, float]] = Field(
        None, description="Economic impact estimates"
    )
    damage_assessment: Optional[Dict[str, Any]] = Field(
        None, description="Combined damage assessment summary"
    )
    ml_enhanced_damage: Optional[Dict[str, Any]] = Field(
        None, description="Damage assessment adjusted by ML enhancer"
    )

class DeflectionGameScoreResponse(BaseModel):
	"""Deflection game score response"""
	id: int
	player_name: str
	score: int
	asteroid_mass: float
	asteroid_diameter: float
	asteroid_velocity: float
	deflection_method: str
	dv_applied: float
	success: bool
	game_session_id: Optional[str] = None
	difficulty_level: Optional[str] = "normal"
	time_taken: Optional[float] = None
	timestamp: datetime
	user_id: Optional[int] = None

	class Config:
		from_attributes = True

class DeflectionGameScore(BaseModel):
	"""Deflection game score entry"""
	player_name: str = Field(..., description="Player name")
	score: int = Field(..., ge=0, description="Game score")
	asteroid_mass: float = Field(..., description="Asteroid mass used")
	asteroid_diameter: float = Field(..., description="Asteroid diameter used")
	asteroid_velocity: float = Field(..., description="Asteroid velocity used")
	deflection_method: str = Field(..., description="Method used")
	dv_applied: float = Field(..., description="Delta-v applied")
	success: bool = Field(..., description="Whether deflection was successful")
	game_session_id: Optional[str] = Field(None, description="Game session ID")
	difficulty_level: Optional[str] = Field("normal", description="Difficulty level")
	time_taken: Optional[float] = Field(None, description="Time taken in seconds")
	timestamp: datetime = Field(default_factory=datetime.utcnow)

class SolutionMethod(BaseModel):
	"""Mitigation solution method"""
	name: str = Field(..., description="Method name")
	description: str = Field(..., description="Method description")
	effectiveness: float = Field(..., ge=0, le=1, description="Effectiveness rating")
	cost_estimate: str = Field(..., description="Cost estimate")
	time_required: str = Field(..., description="Time required")
	technology_level: str = Field(..., description="Technology readiness level")
	pros: List[str] = Field(default_factory=list, description="Advantages")
	cons: List[str] = Field(default_factory=list, description="Disadvantages")
