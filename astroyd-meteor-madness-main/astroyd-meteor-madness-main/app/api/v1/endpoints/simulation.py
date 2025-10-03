"""
Simulation API endpoints
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List
import uuid
from datetime import datetime

from app.models.asteroid import AsteroidCreate, AsteroidResponse
from app.models.impact import (
	ImpactLocation, 
	SimulationRequest, 
	SimulationResponse,
	ImpactResult,
	DamageAssessment
)
from app.physics.impact_calculator import impact_calculator
from app.physics.damage_assessor import damage_assessor
from app.nasa.client import nasa_client
from app.services.geo_enrichment import geo_enrichment_service
from app.ml.enhancer import ml_enhancer

router = APIRouter()

@router.post("/simulate", response_model=SimulationResponse)
async def simulate_impact(request: SimulationRequest):
	"""
	Simulate meteor impact with given asteroid and location parameters
	"""
	try:
		# Generate simulation ID
		simulation_id = str(uuid.uuid4())

		# Optionally enrich location with NASA/USGS data
		location = request.impact_location
		if request.use_nasa_data:
			location = await geo_enrichment_service.enrich_location(location)


		# Apply simple mitigation deflection: reduce impact velocity by dv_mps
		asteroid_input = request.asteroid
		if getattr(request, "dv_mps", 0.0) and request.dv_mps > 0.0:
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

		# Calculate impact physics
		impact_result_data = impact_calculator.calculate_impact_result(
			asteroid_input,
			location
		)

		# Assess damage
		damage_data = damage_assessor.assess_damage(
			request.asteroid,
			location,
			impact_result_data
		)

		# Optional ML enhancement
		if request.use_ml:
			features = {
				"energy_megatons": request.asteroid.kinetic_energy_megatons,
				"terrain_type": location.terrain_type,
				"population_density": location.population_density,
			}
			damage_data = ml_enhancer.enhance(features, damage_data)

		# Create models
		impact_result = ImpactResult(**impact_result_data)
		damage_assessment_model = DamageAssessment(**damage_data)
		asteroid_response = AsteroidResponse(
			**asteroid_input.dict(),
			kinetic_energy=asteroid_input.kinetic_energy,
			kinetic_energy_megatons=asteroid_input.kinetic_energy_megatons
		)

		# Create simulation response
		response = SimulationResponse(
			simulation_id=simulation_id,
			asteroid=asteroid_response,
			impact_location=location,
			impact_result=impact_result,
			damage_assessment=damage_assessment_model,
			simulation_metadata={
				"timestamp": datetime.utcnow().isoformat(),
				"version": "1.0.0",
				"calculation_method": "physics_based",
				"data_enriched": request.use_nasa_data,
					"ml_enhanced": request.use_ml,
					"deflection_applied": bool(getattr(request, "dv_mps", 0.0) and request.dv_mps > 0.0),
					"dv_mps": getattr(request, "dv_mps", 0.0),
				"deflection_method": getattr(request, "deflection_method", None),
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

		return response

	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Simulation failed: {str(e)}")

@router.post("/batch-simulate", response_model=List[SimulationResponse])
async def batch_simulate_impacts(requests: List[SimulationRequest]):
	"""
	Simulate multiple meteor impact scenarios
	"""
	try:
		results = []
		for request in requests:
			# Generate simulation ID
			simulation_id = str(uuid.uuid4())

			# Optionally enrich location
			location = request.impact_location
			if request.use_nasa_data:
				location = await geo_enrichment_service.enrich_location(location)


			# Apply simple mitigation deflection per request
			asteroid_input = request.asteroid
			if getattr(request, "dv_mps", 0.0) and request.dv_mps > 0.0:
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

			# Calculate impact physics
			impact_result_data = impact_calculator.calculate_impact_result(
				asteroid_input,
				location
			)

			# Create impact result model
			impact_result = ImpactResult(**impact_result_data)

			# Assess damage
			damage_data = damage_assessor.assess_damage(
				request.asteroid,
				location,
				impact_result_data
			)

			# Create damage assessment model
			damage_assessment = DamageAssessment(**damage_data)

			# Create asteroid response
			asteroid_response = AsteroidResponse(
				**asteroid_input.dict(),
				kinetic_energy=asteroid_input.kinetic_energy,
				kinetic_energy_megatons=asteroid_input.kinetic_energy_megatons
			)

			# Create simulation response
			response = SimulationResponse(
				simulation_id=simulation_id,
				asteroid=asteroid_response,
				impact_location=location,
				impact_result=impact_result,
				damage_assessment=damage_assessment,
					simulation_metadata={
					"timestamp": datetime.utcnow().isoformat(),
					"version": "1.0.0",
					"calculation_method": "physics_based",
						"data_enriched": request.use_nasa_data,
						"deflection_applied": bool(getattr(request, "dv_mps", 0.0) and request.dv_mps > 0.0),
						"dv_mps": getattr(request, "dv_mps", 0.0),
						"deflection_method": getattr(request, "deflection_method", None)
				},
				population_density=location.population_density,
				elevation=location.elevation,
				terrain_type=str(location.terrain_type)
			)

			results.append(response)

		return results

	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Batch simulation failed: {str(e)}")

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
