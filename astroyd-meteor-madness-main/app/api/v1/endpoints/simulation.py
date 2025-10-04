"""
Enhanced simulation API endpoints with trajectory, zones, and deflection game
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.encoders import jsonable_encoder
from typing import List, Dict, Any, Optional
import uuid
import math
from datetime import datetime, timedelta
import logging
import json

from app.models.asteroid import AsteroidCreate, AsteroidResponse
from app.models.impact import (
        ImpactLocation,
        SimulationRequest,
	SimulationResponse,
	ImpactResult,
	DamageAssessment,
	TrajectoryPoint,
	ImpactZone,
	MitigationResult,
	Warning,
        DeflectionGameScore,
        DeflectionGameScoreResponse,
        SolutionMethod
)
from app.physics.impact_calculator import impact_calculator
from app.physics.damage_assessor import damage_assessor
from app.nasa.client import nasa_client
from app.services.geo_enrichment import geo_enrichment_service
from app.ml.enhancer import ml_enhancer
from app.core.database import get_db
from app.core.models import Simulation, DeflectionGameScoreDB, User
from app.core.auth import get_current_user, get_current_user_optional
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

router = APIRouter()
logger = logging.getLogger(__name__)

# In-memory storage for demo (replace with database in production)
_solutions_cache: List[SolutionMethod] = []


class SimulationHistoryEntry(BaseModel):
	"""Serialized simulation entry for history responses"""

	simulation_id: str
	created_at: datetime
	asteroid: AsteroidResponse
	impact_location: ImpactLocation
	impact_result: ImpactResult
	damage_assessment: DamageAssessment
	trajectory: Optional[List[TrajectoryPoint]] = None
	impact_zones: Optional[List[ImpactZone]] = None
	mitigation_result: Optional[MitigationResult] = None
	warnings: List[Warning] = Field(default_factory=list)
	simulation_metadata: Dict[str, Any]
	request_parameters: Dict[str, Any]


class SimulationHistoryResponse(BaseModel):
	"""Paginated simulation history list"""

	total: int
	skip: int
	limit: int
	simulations: List[SimulationHistoryEntry]

@router.post("/simulate", response_model=SimulationResponse)
async def simulate_impact(
        request: SimulationRequest,
        db: Session = Depends(get_db),
        current_user: Optional[User] = Depends(get_current_user_optional)
):
	"""
	Enhanced meteor impact simulation with trajectory and environmental zones
	"""
	try:
		# Generate simulation ID
		simulation_id = str(uuid.uuid4())
		warnings = []

		# Optionally enrich location with NASA/USGS data
		location = request.impact_location
		if request.use_nasa_data:
			try:
				location = await geo_enrichment_service.enrich_location(location)
			except Exception as e:
				warnings.append(Warning(
					level="warning",
					code="DATA_ENRICHMENT_FAILED",
					message=f"Failed to enrich location data: {str(e)}"
				))

		# Apply mitigation deflection if specified
		asteroid_input = request.asteroid
		mitigation_result = None
		if request.dv_mps > 0.0:
			adjusted_velocity = max(0.0, asteroid_input.velocity - request.dv_mps)
			asteroid_input = AsteroidCreate(
				mass=asteroid_input.mass,
				diameter=asteroid_input.diameter,
				velocity=adjusted_velocity,
				impact_angle=asteroid_input.impact_angle,
				composition=asteroid_input.composition,
				density=asteroid_input.density,
				porosity=asteroid_input.porosity,
				strength=asteroid_input.strength
			)
			
			# Calculate mitigation success probability
			success_prob = min(1.0, request.dv_mps / (asteroid_input.velocity * 0.1))
			energy_reduction = (request.asteroid.kinetic_energy - asteroid_input.kinetic_energy) / request.asteroid.kinetic_energy * 100
			
			mitigation_result = MitigationResult(
				method=request.deflection_method or "kinetic_impactor",
				dv_applied=request.dv_mps,
				success_probability=success_prob,
				energy_reduction=energy_reduction
			)

		# Calculate impact physics
		impact_result_data = impact_calculator.calculate_impact_result(
			asteroid_input,
			location
		)

		# Calculate environmental impact zones
		impact_zones = []
		if request.include_zones:
			impact_zones = await _calculate_impact_zones(asteroid_input, location, impact_result_data)

		# Create enhanced impact result
		impact_result = ImpactResult(
			crater_diameter=impact_result_data["crater_diameter"],
			crater_depth=impact_result_data["crater_depth"],
			crater_volume=impact_result_data["crater_volume"],
			blast_radius=impact_result_data["blast_radius"],
			thermal_radius=impact_result_data["thermal_radius"],
			seismic_magnitude=impact_result_data["seismic_magnitude"],
			tsunami_height=impact_result_data.get("tsunami_height"),
			fireball_radius=impact_result_data["fireball_radius"],
			atmospheric_effects=impact_result_data["atmospheric_effects"],
			impact_zones=impact_zones,
			evacuation_radius=impact_result_data["evacuation_radius"],
			affected_area=impact_result_data["affected_area"]
		)

		# Calculate trajectory if requested
		trajectory = None
		if request.calculate_trajectory:
			try:
				trajectory = await nasa_client.calculate_trajectory(asteroid_input, location)
			except Exception as e:
				warnings.append(Warning(
					level="warning",
					code="TRAJECTORY_CALCULATION_FAILED",
					message=f"Failed to calculate trajectory: {str(e)}"
				))

		# Assess damage
		damage_data = damage_assessor.assess_damage(
			asteroid_input,
			location,
			impact_result_data
		)

		# Optional ML enhancement
		if request.use_ml:
			try:
				features = {
					"energy_megatons": asteroid_input.kinetic_energy_megatons,
					"terrain_type": location.terrain_type,
					"population_density": location.population_density,
				}
				damage_data = ml_enhancer.enhance(features, damage_data)
			except Exception as e:
				warnings.append(Warning(
					level="warning",
					code="ML_ENHANCEMENT_FAILED",
					message=f"ML enhancement failed: {str(e)}"
				))

		# Create damage assessment model
		damage_assessment_model = DamageAssessment(**damage_data)

		# Create asteroid response
		asteroid_response = AsteroidResponse(
			**asteroid_input.dict(),
			kinetic_energy=asteroid_input.kinetic_energy,
			kinetic_energy_megatons=asteroid_input.kinetic_energy_megatons
		)

		# Create simulation response
		response = SimulationResponse(
				simulation_id=simulation_id,
				asteroid=asteroid_response.model_dump(),
				impact_location=location.model_dump(),
				impact_result=impact_result,
				mitigation_result=mitigation_result,
				trajectory=trajectory,
				warnings=warnings,
				simulation_metadata={
					"timestamp": datetime.utcnow().isoformat(),
					"version": "2.0.0",
					"calculation_method": "enhanced_physics",
					"data_enriched": request.use_nasa_data,
					"ml_enhanced": request.use_ml,
					"deflection_applied": bool(request.dv_mps > 0.0),
					"dv_mps": request.dv_mps,
					"deflection_method": request.deflection_method,
					"provenance": {
						"population": "demo_or_cached",
						"terrain": "demo_or_cached",
						"imagery": "demo_or_cached"
					}
				},
				population_density=location.population_density,
				elevation=location.elevation,
				terrain_type=str(location.terrain_type)
		)

		# Save simulation to database
		# Save simulation to database
		try:
			db_simulation = Simulation(
				simulation_id=simulation_id,
				user_id=current_user.id if current_user else None,
				asteroid_data=jsonable_encoder(asteroid_response),
				impact_location=jsonable_encoder(location),
				simulation_request=jsonable_encoder(request),
				impact_result=jsonable_encoder(impact_result),
				damage_assessment=jsonable_encoder(damage_assessment_model),
				trajectory_data=jsonable_encoder(trajectory) if trajectory else None,
				impact_zones=jsonable_encoder(impact_zones) if impact_zones else None,
				mitigation_result=jsonable_encoder(mitigation_result) if mitigation_result else None,
				warnings=jsonable_encoder(warnings) if warnings else None,
				simulation_metadata=jsonable_encoder(response.simulation_metadata)
			)
			db.add(db_simulation)
			db.commit()
			db.refresh(db_simulation)
		except Exception as e:
			db.rollback()
			logger.error("Failed to save simulation to database: %s", e, exc_info=True)
			# Continue without failing the request

		return response

	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Simulation failed: {str(e)}")


@router.get("/history", response_model=SimulationHistoryResponse)
async def get_simulation_history(
	skip: int = 0,
	limit: int = 20,
	db: Session = Depends(get_db),
	current_user: Optional[User] = Depends(get_current_user)
):
	"""Return paginated simulation history for the current user"""
	if not current_user:
		raise HTTPException(status_code=401, detail="Authentication required")

	if limit <= 0 or limit > 100:
		raise HTTPException(status_code=400, detail="Limit must be between 1 and 100")

	base_query = db.query(Simulation).filter(
		Simulation.user_id == current_user.id
	).order_by(Simulation.created_at.desc())

	total = base_query.count()
	simulations = base_query.offset(max(0, skip)).limit(limit).all()

	history_entries: List[SimulationHistoryEntry] = []
	for record in simulations:
		try:
			asteroid_payload = _ensure_json_struct(record.asteroid_data, {})
			location_payload = _ensure_json_struct(record.impact_location, {})
			impact_result_payload = _ensure_json_struct(record.impact_result, {})
			damage_payload = _ensure_json_struct(record.damage_assessment, {})
			trajectory_payload = _ensure_json_struct(record.trajectory_data, None)
			impact_zones_payload = _ensure_json_struct(record.impact_zones, None)
			mitigation_payload = _ensure_json_struct(record.mitigation_result, None)
			warnings_payload = _ensure_json_struct(record.warnings, [])
			metadata_payload = _ensure_json_struct(record.simulation_metadata, {})
			request_payload = _ensure_json_struct(record.simulation_request, {})

			history_entries.append(
				SimulationHistoryEntry(
					simulation_id=record.simulation_id,
					created_at=record.created_at,
					asteroid=AsteroidResponse(**asteroid_payload),
					impact_location=ImpactLocation(**location_payload),
					impact_result=ImpactResult(**impact_result_payload),
					damage_assessment=DamageAssessment(**damage_payload),
					trajectory=[TrajectoryPoint(**point) for point in trajectory_payload] if trajectory_payload else None,
					impact_zones=[ImpactZone(**zone) for zone in impact_zones_payload] if impact_zones_payload else None,
					mitigation_result=MitigationResult(**mitigation_payload) if mitigation_payload else None,
					warnings=[Warning(**warning) for warning in warnings_payload] if warnings_payload else [],
					simulation_metadata=metadata_payload,
					request_parameters=request_payload,
				)
			)
		except Exception as exc:
			logger.error("Failed to deserialize simulation history entry %s: %s", record.simulation_id, exc, exc_info=True)

	return SimulationHistoryResponse(
		total=total,
		skip=max(0, skip),
		limit=limit,
		simulations=history_entries
	)

def _ensure_json_struct(payload: Any, default: Any) -> Any:
        """Safely decode JSON payloads stored in the database."""

        if payload is None:
                return default

        if isinstance(payload, (dict, list)):
                return payload

        if isinstance(payload, str):
                try:
                        return json.loads(payload)
                except json.JSONDecodeError:
                        logger.error("Failed to decode JSON payload: %s", payload[:200] if isinstance(payload, str) else payload)
                        return default

        return default

async def _calculate_impact_zones(asteroid, location, impact_data) -> List[ImpactZone]:
	"""Calculate environmental impact zones"""
	zones = []
	
	# Tsunami zone (for ocean impacts)
	if location.terrain_type.value == "ocean" and impact_data.get("tsunami_height", 0) > 1:
		tsunami_radius = impact_data["tsunami_height"] * 1000  # Rough estimate
		zones.append(ImpactZone(
			zone_type="tsunami",
			radius=tsunami_radius,
			intensity=min(10, impact_data["tsunami_height"]),
			affected_population=int(tsunami_radius * 0.001 * location.population_density),
			description=f"Tsunami zone with {impact_data['tsunami_height']:.1f}m wave height"
		))
	
	# Seismic zone
	seismic_radius = impact_data["blast_radius"] * 2
	zones.append(ImpactZone(
		zone_type="seismic",
		radius=seismic_radius,
		intensity=min(10, impact_data["seismic_magnitude"]),
		affected_population=int(seismic_radius * 0.001 * location.population_density),
		description=f"Seismic zone with magnitude {impact_data['seismic_magnitude']:.1f}"
	))
	
	# Thermal zone
	thermal_radius = impact_data["thermal_radius"]
	zones.append(ImpactZone(
		zone_type="thermal",
		radius=thermal_radius,
		intensity=8.0,
		affected_population=int(thermal_radius * 0.001 * location.population_density),
		description=f"Thermal radiation zone with {thermal_radius/1000:.1f}km radius"
	))
	
	# Blast zone
	blast_radius = impact_data["blast_radius"]
	zones.append(ImpactZone(
		zone_type="blast",
		radius=blast_radius,
		intensity=10.0,
		affected_population=int(blast_radius * 0.001 * location.population_density),
		description=f"Blast zone with {blast_radius/1000:.1f}km radius"
	))
	
	return zones

@router.get("/trajectory/{asteroid_id}")
async def get_asteroid_trajectory(asteroid_id: str, hours: int = 24):
	"""Get trajectory for a specific asteroid"""
	try:
		# Get asteroid data from NEO API
		neo_data = await nasa_client.get_asteroid_data(asteroid_id)
		if not neo_data:
			raise HTTPException(status_code=404, detail="Asteroid not found")
		
		# Model asteroid from NEO data
		asteroid = await nasa_client.model_asteroid_from_neo(neo_data)
		
		# Create default impact location (center of Earth)
		impact_location = ImpactLocation(
			latitude=0.0,
			longitude=0.0,
			terrain_type="land",
			population_density=100.0
		)
		
		# Calculate trajectory
		trajectory = await nasa_client.calculate_trajectory(asteroid, impact_location, hours)
		
		return {
			"asteroid_id": asteroid_id,
			"asteroid": asteroid.dict(),
			"trajectory": [point.dict() for point in trajectory],
			"hours_ahead": hours
		}
	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Trajectory calculation failed: {str(e)}")

@router.get("/impact-zones")
async def get_impact_zones(
	latitude: float,
	longitude: float,
	mass: float,
	velocity: float,
	impact_angle: float = 45.0
):
	"""Calculate impact zones for given parameters"""
	try:
		from app.models.asteroid import AsteroidCreate
		from app.models.impact import TerrainType
		
		asteroid = AsteroidCreate(
			mass=mass,
			diameter=2 * ((3 * mass) / (4 * math.pi * 3000)) ** (1/3),  # Estimate diameter
			velocity=velocity,
			impact_angle=impact_angle,
			composition="stony"
		)
		
		location = ImpactLocation(
			latitude=latitude,
			longitude=longitude,
			terrain_type=TerrainType.LAND,
			population_density=100.0
		)
		
		impact_data = impact_calculator.calculate_impact_result(asteroid, location)
		zones = await _calculate_impact_zones(asteroid, location, impact_data)
		
		return {
			"location": {"latitude": latitude, "longitude": longitude},
			"asteroid": asteroid.dict(),
			"impact_zones": [zone.dict() for zone in zones],
			"total_affected_area": impact_data["affected_area"]
		}
	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Impact zones calculation failed: {str(e)}")

@router.post("/deflection-game/submit-score", response_model=DeflectionGameScoreResponse)
async def submit_deflection_score(
	score: DeflectionGameScore,
	db: Session = Depends(get_db),
	current_user: Optional[User] = Depends(get_current_user)
):
	"""Submit score for deflection game"""
	try:
		# Save score to database
		db_score = DeflectionGameScoreDB(
			user_id=current_user.id if current_user else None,
			player_name=score.player_name,
			score=score.score,
			asteroid_mass=score.asteroid_mass,
			asteroid_diameter=score.asteroid_diameter,
			asteroid_velocity=score.asteroid_velocity,
			deflection_method=score.deflection_method,
			dv_applied=score.dv_applied,
			success=score.success,
			game_session_id=score.game_session_id,
			difficulty_level=score.difficulty_level,
			time_taken=score.time_taken
		)
		
		db.add(db_score)
		db.commit()
		db.refresh(db_score)
		
		# Get rank
		rank_query = db.query(DeflectionGameScore).filter(
			DeflectionGameScore.score > score.score
		).count()
		rank = rank_query + 1
		
		return {
			"success": True,
			"rank": rank,
			"total_scores": db.query(DeflectionGameScore).count()
		}
	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Score submission failed: {str(e)}")

@router.get("/deflection-game/leaderboard")
async def get_deflection_leaderboard(
	limit: int = 10,
	db: Session = Depends(get_db)
):
	"""Get deflection game leaderboard"""
	try:
		scores = db.query(DeflectionGameScore).order_by(
			DeflectionGameScore.score.desc()
		).limit(limit).all()
		
		return {
			"leaderboard": [
				{
					"id": score.id,
					"player_name": score.player_name,
					"score": score.score,
					"asteroid_mass": score.asteroid_mass,
					"deflection_method": score.deflection_method,
					"success": score.success,
					"created_at": score.created_at.isoformat()
				}
				for score in scores
			],
			"total_players": db.query(DeflectionGameScore).count()
		}
	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Failed to get leaderboard: {str(e)}")

@router.get("/solutions")
async def get_mitigation_solutions():
	"""Get available mitigation solutions"""
	try:
		global _solutions_cache
		if not _solutions_cache:
			_solutions_cache = [
				SolutionMethod(
					name="Kinetic Impactor",
					description="Direct collision with asteroid to change velocity",
					effectiveness=0.8,
					cost_estimate="$500M - $1B",
					time_required="5-10 years",
					technology_level="TRL 9",
					pros=["Proven technology", "High effectiveness", "Relatively simple"],
					cons=["Requires precise targeting", "Limited to smaller asteroids"]
				),
				SolutionMethod(
					name="Gravity Tractor",
					description="Use spacecraft gravity to gradually deflect asteroid",
					effectiveness=0.6,
					cost_estimate="$1B - $2B",
					time_required="10-20 years",
					technology_level="TRL 6",
					pros=["Non-destructive", "Works on larger asteroids", "Precise control"],
					cons=["Requires long lead time", "Complex mission design"]
				),
				SolutionMethod(
					name="Nuclear Explosive",
					description="Nuclear detonation to fragment or deflect asteroid",
					effectiveness=0.9,
					cost_estimate="$2B - $5B",
					time_required="3-7 years",
					technology_level="TRL 4",
					pros=["High effectiveness", "Works on large asteroids", "Fast implementation"],
					cons=["Creates debris", "Political complications", "Uncertain outcomes"]
				),
				SolutionMethod(
					name="Laser Ablation",
					description="Use focused laser to vaporize asteroid material",
					effectiveness=0.4,
					cost_estimate="$3B - $10B",
					time_required="15-25 years",
					technology_level="TRL 3",
					pros=["Precise control", "No debris", "Scalable"],
					cons=["High power requirements", "Limited range", "Experimental technology"]
				)
			]
		
		return {
			"solutions": [solution.dict() for solution in _solutions_cache],
			"total_methods": len(_solutions_cache)
		}
	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Failed to get solutions: {str(e)}")

@router.get("/asteroid/validate")
async def validate_asteroid_parameters(
	mass: float,
	diameter: float,
	velocity: float,
	impact_angle: float,
	composition: str
):
	"""
	Validate asteroid parameters before simulation
	"""
	try:
		# Create temporary asteroid for validation
		asteroid = AsteroidCreate(
			mass=mass,
			diameter=diameter,
			velocity=velocity,
			impact_angle=impact_angle,
			composition=composition
		)

		# Calculate basic properties
		kinetic_energy = asteroid.kinetic_energy
		kinetic_energy_megatons = asteroid.kinetic_energy_megatons

		return {
			"valid": True,
			"kinetic_energy_joules": kinetic_energy,
			"kinetic_energy_megatons": kinetic_energy_megatons,
			"energy_classification": classify_energy(kinetic_energy_megatons)
		}

	except Exception as e:
		return {
			"valid": False,
			"error": str(e)
		}

def classify_energy(energy_megatons: float) -> str:
	"""Classify impact energy"""
	if energy_megatons < 0.001:
		return "Small (Fireball)"
	elif energy_megatons < 0.1:
		return "Medium (Local Damage)"
	elif energy_megatons < 10:
		return "Large (Regional Damage)"
	elif energy_megatons < 1000:
		return "Very Large (Continental Damage)"
	else:
		return "Extreme (Global Effects)"
