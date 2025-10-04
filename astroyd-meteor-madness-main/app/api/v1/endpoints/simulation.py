"""
Enhanced simulation API endpoints with trajectory, zones, and deflection game
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import uuid
import math
from datetime import datetime, timedelta
import logging
import json
import dataclasses

from app.models.asteroid import Asteroid, AsteroidCreate, AsteroidResponse
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
from app.core.auth import get_current_user
from sqlalchemy.orm import Session

router = APIRouter()
logger = logging.getLogger(__name__)

# In-memory storage for demo (replace with database in production)
_solutions_cache: List[SolutionMethod] = []

@router.post("/simulate", response_model=SimulationResponse)
async def simulate_impact(
    request: SimulationRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
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
                trajectory = await nasa_client.calculate_trajectory( asteroid_input, location)
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

        simulation_metadata = {
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
        }
        if current_user:
            simulation_metadata["user_id"] = current_user.id

        # Create simulation response
        response = SimulationResponse(
            simulation_id=simulation_id,
            asteroid=asteroid_input,
            impact_location=location,
            impact_result=impact_result,
            damage_assessment=damage_assessment_model,
            mitigation_result=mitigation_result,
            trajectory=trajectory,
            warnings=warnings,
            simulation_metadata=simulation_metadata,
            population_density=location.population_density,
            elevation=location.elevation,
            terrain_type=str(location.terrain_type)
        )


        # Save simulation to database
        try:
            db_simulation = Simulation(
                simulation_id=simulation_id,
                user_id=current_user.id if current_user else None,
                asteroid_data=asteroid_input.model_dump(),
                impact_location=location.model_dump(),
                simulation_request=request.model_dump(),
                impact_result=impact_result.model_dump(),
                damage_assessment=damage_assessment_model.model_dump(),
                trajectory_data=[{**point.model_dump(), "timestamp": point.timestamp.isoformat()} for point in trajectory] if trajectory else None,
                impact_zones=[zone.model_dump() for zone in impact_zones] if impact_zones else None,
                mitigation_result=mitigation_result.model_dump() if mitigation_result else None,
                warnings=[warning.model_dump() for warning in warnings] if warnings else None,
                simulation_metadata=simulation_metadata
            )
            db.add(db_simulation)
            db.commit()
        except Exception as e:
            logger.error(f"Failed to save simulation to database: {e}")
            # Continue without failing the request

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simulation failed: {str(e)}")

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



def _convert_to_builtin(value):
    """Convert ORM / Pydantic / dataclass objects into plain Python structures."""
    if value is None:
        return None
    if isinstance(value, BaseModel):
        return _convert_to_builtin(value.model_dump(mode="python"))
    if dataclasses.is_dataclass(value):
        return _convert_to_builtin(dataclasses.asdict(value))
    if isinstance(value, dict):
        return {key: _convert_to_builtin(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_convert_to_builtin(item) for item in value]
    return value

def _safe_json_loads(value):
    if value is None:
        return None
    if isinstance(value, str):
        raw = value.strip()
        if not raw:
            return None
        try:
            loaded = json.loads(raw)
        except json.JSONDecodeError:
            logger.warning("Failed to decode JSON string: %s", raw[:120])
            return None
        return _convert_to_builtin(loaded)
    return _convert_to_builtin(value)

def _ensure_dict(value):
    loaded = _safe_json_loads(value)
    if isinstance(loaded, dict):
        return loaded
    return None

def _ensure_list(value):
    loaded = _safe_json_loads(value)
    if loaded is None:
        return []
    if isinstance(loaded, list):
        return loaded
    if isinstance(loaded, tuple):
        return list(loaded)
    if isinstance(loaded, dict):
        return [loaded]
    return []

@router.get("/history")
async def get_simulation_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve simulation history for the current user.
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    logger.info(f"User {current_user.id} ({current_user.username}) accessed simulation history")

    simulations = db.query(Simulation).filter(Simulation.user_id == current_user.id).order_by(Simulation.created_at.desc()).all()

    logger.info(f"Retrieved {len(simulations)} simulations for user {current_user.id}")

    if not simulations:
        return []

    # Convert SQLAlchemy models to Pydantic models
    response = []
    for sim in simulations:
        try:
            logger.debug("Building history entry for simulation %s (user %s)", sim.id, sim.user_id)
            asteroid_data = _ensure_dict(sim.asteroid_data) or {}
            impact_location_data = _ensure_dict(sim.impact_location) or {}
            impact_result_data = _ensure_dict(sim.impact_result) or {}
            damage_assessment_data = _ensure_dict(sim.damage_assessment) or {}
            mitigation_data = _ensure_dict(sim.mitigation_result)
            trajectory_points = _ensure_list(sim.trajectory_data)
            warnings_data = _ensure_list(sim.warnings)
            impact_zones_data = _ensure_list(sim.impact_zones)
            metadata = _ensure_dict(sim.simulation_metadata) or {}

            if impact_zones_data and 'impact_zones' not in impact_result_data:
                impact_result_data['impact_zones'] = impact_zones_data

            impact_result_data.setdefault('blast_radius', impact_location_data.get('blast_radius', 0.0))
            impact_result_data.setdefault('crater_diameter', impact_location_data.get('crater_diameter', 0.0))
            impact_result_data.setdefault('thermal_radius', impact_location_data.get('thermal_radius', 0.0))
            impact_result_data.setdefault('fireball_radius', impact_location_data.get('fireball_radius', 0.0))
            impact_result_data.setdefault('evacuation_radius', impact_location_data.get('evacuation_radius', 0.0))
            impact_result_data.setdefault('atmospheric_effects', impact_result_data.get('atmospheric_effects', {}))
            impact_result_data.setdefault('impact_zones', impact_result_data.get('impact_zones', []))

            default_damage = {
                'estimated_casualties': 0,
                'injured_count': 0,
                'displaced_count': 0,
                'infrastructure_damage_cost': 0.0,
                'buildings_destroyed': 0,
                'buildings_damaged': 0,
                'environmental_impact_score': 0.0,
                'ecosystem_affected_area': 0.0,
                'total_economic_cost': 0.0,
                'recovery_time_years': 0.0
            }
            damage_assessment_data = {**default_damage, **damage_assessment_data}

            default_location = {
                'latitude': 0.0,
                'longitude': 0.0,
                'elevation': 0.0,
                'terrain_type': 'land',
                'population_density': 0.0,
                'infrastructure_density': 0.0
            }
            impact_location_data = {**default_location, **impact_location_data}

            default_asteroid = {
                'mass': 1.0,
                'diameter': 1.0,
                'velocity': 1.0,
                'impact_angle': 45.0,
                'composition': 'stony',
                'density': 3000.0,
                'porosity': 0.0
            }
            asteroid_data = {**default_asteroid, **asteroid_data}

            entry = {
                'simulation_id': sim.simulation_id,
                'asteroid': asteroid_data,
                'impact_location': impact_location_data,
                'impact_result': impact_result_data,
                'damage_assessment': damage_assessment_data,
                'mitigation_result': mitigation_data,
                'trajectory': trajectory_points or [],
                'warnings': warnings_data or [],
                'simulation_metadata': metadata,
                'population_density': impact_location_data.get('population_density'),
                'elevation': impact_location_data.get('elevation'),
                'terrain_type': impact_location_data.get('terrain_type')
            }
            response.append(entry)
        except Exception as e:
            logger.error(f"Failed to parse simulation record {sim.id} (sim_id: {sim.simulation_id}): {e}")
            continue
    return response

