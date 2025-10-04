"""
Damage assessment calculations for meteor impacts
"""

import math
import numpy as np
from typing import Dict, Any, Tuple
from app.models.asteroid import Asteroid
from app.models.impact import ImpactLocation, ImpactResult, TerrainType
from app.physics.impact_calculator import impact_calculator

class DamageAssessor:
    """Assessor for human and infrastructure damage from meteor impacts"""
    
    def __init__(self):
        # Damage scaling factors
        self.casualty_scaling = {
            "urban": 1.0,
            "rural": 0.3,
            "mountain": 0.1,
            "desert": 0.05,
            "forest": 0.2,
            "ice": 0.1,
            "ocean": 0.0  # No direct casualties from ocean impacts
        }
        
        # Infrastructure damage factors
        self.infrastructure_scaling = {
            "urban": 1.0,
            "rural": 0.4,
            "mountain": 0.2,
            "desert": 0.1,
            "forest": 0.3,
            "ice": 0.1,
            "ocean": 0.0
        }
        
        # Economic cost factors (USD per person affected)
        self.economic_factors = {
            "casualty_cost": 1000000,  # $1M per casualty
            "injury_cost": 100000,     # $100K per injury
            "displacement_cost": 50000, # $50K per displaced person
            "infrastructure_cost_per_km2": 1000000  # $1M per km²
        }
    
    def calculate_human_casualties(self, impact_result: Dict[str, Any], location: ImpactLocation) -> Dict[str, int]:
        """Calculate human casualties based on impact effects"""
        
        # Get population within blast radius
        blast_radius_km = impact_result["blast_radius"] / 1000
        population_in_blast = location.population_density * math.pi * blast_radius_km ** 2
        
        # Get population within thermal radius
        thermal_radius_km = impact_result["thermal_radius"] / 1000
        population_in_thermal = location.population_density * math.pi * thermal_radius_km ** 2
        
        # Casualty rates based on distance from impact
        blast_casualty_rate = 0.9  # 90% within blast radius
        thermal_casualty_rate = 0.3  # 30% within thermal radius
        
        # Calculate casualties
        blast_casualties = int(population_in_blast * blast_casualty_rate)
        thermal_casualties = int((population_in_thermal - population_in_blast) * thermal_casualty_rate)
        
        total_casualties = blast_casualties + thermal_casualties
        
        # Apply terrain scaling
        terrain_factor = self.casualty_scaling.get(location.terrain_type, 0.5)
        total_casualties = int(total_casualties * terrain_factor)
        
        # Calculate injuries (3x casualties)
        total_injuries = total_casualties * 3
        
        # Calculate displaced (10x casualties)
        total_displaced = total_casualties * 10
        
        return {
            "estimated_casualties": total_casualties,
            "injured_count": total_injuries,
            "displaced_count": total_displaced
        }
    
    def calculate_infrastructure_damage(self, impact_result: Dict[str, Any], location: ImpactLocation) -> Dict[str, Any]:
        """Calculate infrastructure damage and costs"""
        
        # Affected area in km²
        affected_area = impact_result["affected_area"]
        
        # Infrastructure density factor
        terrain_factor = self.infrastructure_scaling.get(location.terrain_type, 0.5)
        infrastructure_density = location.infrastructure_density * terrain_factor
        
        # Building damage estimates
        buildings_per_km2 = 1000  # Average buildings per km² in urban areas
        buildings_affected = int(affected_area * buildings_per_km2 * infrastructure_density)
        
        # Damage distribution
        buildings_destroyed = int(buildings_affected * 0.3)  # 30% destroyed
        buildings_damaged = int(buildings_affected * 0.7)    # 70% damaged
        
        # Cost calculations
        destruction_cost = buildings_destroyed * 500000  # $500K per destroyed building
        damage_cost = buildings_damaged * 100000         # $100K per damaged building
        infrastructure_damage_cost = destruction_cost + damage_cost
        
        return {
            "infrastructure_damage_cost": infrastructure_damage_cost,
            "buildings_destroyed": buildings_destroyed,
            "buildings_damaged": buildings_damaged
        }
    
    def calculate_environmental_impact(self, impact_result: Dict[str, Any], location: ImpactLocation) -> Dict[str, Any]:
        """Calculate environmental impact score and effects"""
        
        # Base environmental impact score (0-10)
        base_score = min(10.0, impact_result["seismic_magnitude"] - 4.0)
        
        # Adjust for terrain type
        terrain_impact = {
            "urban": 0.8,      # Lower environmental impact
            "rural": 1.0,      # Baseline
            "mountain": 1.2,   # Higher impact on fragile ecosystems
            "desert": 0.6,     # Lower impact on sparse ecosystems
            "forest": 1.5,     # High impact on forest ecosystems
            "ice": 2.0,        # Very high impact on polar regions
            "ocean": 1.0       # Baseline for ocean
        }
        
        terrain_factor = terrain_impact.get(location.terrain_type, 1.0)
        environmental_impact_score = base_score * terrain_factor
        
        # Ecosystem affected area
        ecosystem_affected_area = impact_result["affected_area"] * 1.5  # 50% larger than direct impact
        
        # Additional environmental effects
        atmospheric_effects = {
            "dust_cloud_radius": impact_result["affected_area"] * 10,  # km
            "temperature_drop": min(5.0, impact_result["seismic_magnitude"] - 4.0),  # °C
            "precipitation_change": 0.1 * (impact_result["seismic_magnitude"] - 4.0)  # %
        }
        
        return {
            "environmental_impact_score": min(10.0, environmental_impact_score),
            "ecosystem_affected_area": ecosystem_affected_area,
            "atmospheric_effects": atmospheric_effects
        }
    
    def calculate_economic_impact(self, human_damage: Dict[str, int], infrastructure_damage: Dict[str, Any], 
                                environmental_impact: Dict[str, Any]) -> Dict[str, float]:
        """Calculate total economic impact"""
        
        # Human cost
        casualty_cost = human_damage["estimated_casualties"] * self.economic_factors["casualty_cost"]
        injury_cost = human_damage["injured_count"] * self.economic_factors["injury_cost"]
        displacement_cost = human_damage["displaced_count"] * self.economic_factors["displacement_cost"]
        
        # Infrastructure cost
        infrastructure_cost = infrastructure_damage["infrastructure_damage_cost"]
        
        # Environmental cost (based on impact score)
        environmental_cost = environmental_impact["environmental_impact_score"] * 1e9  # $1B per point
        
        # Total economic cost
        total_economic_cost = (casualty_cost + injury_cost + displacement_cost + 
                             infrastructure_cost + environmental_cost)
        
        # Recovery time estimate (years)
        recovery_time = min(50.0, environmental_impact["environmental_impact_score"] * 5.0)
        
        return {
            "total_economic_cost": total_economic_cost,
            "recovery_time_years": recovery_time,
            "casualty_cost": casualty_cost,
            "injury_cost": injury_cost,
            "displacement_cost": displacement_cost,
            "infrastructure_cost": infrastructure_cost,
            "environmental_cost": environmental_cost
        }
    
    def assess_damage(self, asteroid: Asteroid, location: ImpactLocation, impact_result: Dict[str, Any]) -> Dict[str, Any]:
        """Complete damage assessment"""
        
        # Human casualties
        human_damage = self.calculate_human_casualties(impact_result, location)
        
        # Infrastructure damage
        infrastructure_damage = self.calculate_infrastructure_damage(impact_result, location)
        
        # Environmental impact
        environmental_impact = self.calculate_environmental_impact(impact_result, location)
        
        # Economic impact
        economic_impact = self.calculate_economic_impact(human_damage, infrastructure_damage, environmental_impact)
        
        return {
            **human_damage,
            **infrastructure_damage,
            **environmental_impact,
            **economic_impact
        }

# Global damage assessor instance
damage_assessor = DamageAssessor()
