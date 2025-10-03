"""
Impact physics calculations for meteor simulation
Based on scientific models and empirical formulas
"""

import math
import numpy as np
from typing import Dict, Any, Tuple
from app.models.asteroid import Asteroid
from app.models.impact import ImpactLocation, TerrainType
from app.core.config import settings

class ImpactCalculator:
    """Calculator for meteor impact physics"""
    
    def __init__(self):
        # Physical constants
        self.earth_radius = settings.EARTH_RADIUS
        self.earth_mass = settings.EARTH_MASS
        self.g = settings.GRAVITATIONAL_CONSTANT
        
        # Atmospheric constants (Earth)
        self.atmospheric_density = 1.225  # kg/m³ at sea level
        self.atmospheric_scale_height = 8000  # m
        
        # Material properties
        self.material_properties = {
            "iron": {"density": 7800, "strength": 1e9, "thermal_conductivity": 80},
            "stony": {"density": 3000, "strength": 1e8, "thermal_conductivity": 2},
            "carbonaceous": {"density": 2000, "strength": 1e7, "thermal_conductivity": 1},
            "mixed": {"density": 4000, "strength": 5e8, "thermal_conductivity": 10}
        }
    
    def calculate_kinetic_energy(self, asteroid: Asteroid) -> float:
        """Calculate kinetic energy of the asteroid"""
        return 0.5 * asteroid.mass * asteroid.velocity ** 2
    
    def calculate_atmospheric_entry_effects(self, asteroid: Asteroid, altitude: float = 100000) -> Dict[str, float]:
        """Calculate atmospheric entry effects"""
        # Atmospheric density at altitude
        rho_atm = self.atmospheric_density * math.exp(-altitude / self.atmospheric_scale_height)
        
        # Drag force
        drag_coefficient = 0.47  # Sphere
        cross_sectional_area = math.pi * (asteroid.diameter / 2) ** 2
        drag_force = 0.5 * rho_atm * asteroid.velocity ** 2 * drag_coefficient * cross_sectional_area
        
        # Deceleration
        deceleration = drag_force / asteroid.mass
        
        # Energy lost to atmosphere
        energy_lost = drag_force * altitude  # Simplified calculation
        
        return {
            "drag_force": drag_force,
            "deceleration": deceleration,
            "energy_lost": energy_lost,
            "atmospheric_density": rho_atm
        }
    
    def calculate_crater_formation(self, asteroid: Asteroid, location: ImpactLocation) -> Dict[str, float]:
        """Calculate crater formation using empirical formulas"""
        
        # Get material properties
        material = self.material_properties.get(asteroid.composition, self.material_properties["mixed"])
        
        # Kinetic energy in megatons
        ke_mt = self.calculate_kinetic_energy(asteroid) / (4.184e15)
        
        # Gault's formula for crater diameter (simplified)
        # D = 1.25 * (E/ρ)^(1/3) * sin(θ)^(1/3)
        # where E is energy, ρ is target density, θ is impact angle
        
        target_density = 2700  # kg/m³ (average Earth crust)
        impact_angle_rad = math.radians(asteroid.impact_angle)
        
        # Crater diameter (meters)
        crater_diameter = 1.25 * (ke_mt * 4.184e15 / target_density) ** (1/3) * math.sin(impact_angle_rad) ** (1/3)
        
        # Crater depth (simplified)
        crater_depth = crater_diameter / 5.0  # Typical depth-to-diameter ratio
        
        # Crater volume
        crater_volume = (math.pi / 6) * crater_diameter ** 2 * crater_depth
        
        # Adjust for terrain type
        if location.terrain_type == TerrainType.OCEAN:
            crater_diameter *= 1.2  # Water amplifies crater formation
            crater_depth *= 0.8     # Water reduces depth
        
        return {
            "crater_diameter": crater_diameter,
            "crater_depth": crater_depth,
            "crater_volume": crater_volume
        }
    
    def calculate_blast_effects(self, asteroid: Asteroid, crater_diameter: float) -> Dict[str, float]:
        """Calculate blast effects and thermal radiation"""
        
        # Energy in megatons
        ke_mt = self.calculate_kinetic_energy(asteroid) / (4.184e15)
        
        # Blast radius (simplified scaling law)
        # R = 1.0 * E^(1/3) * 1000  # meters
        blast_radius = 1.0 * (ke_mt ** (1/3)) * 1000
        
        # Thermal radiation radius (larger than blast)
        thermal_radius = blast_radius * 1.5
        
        # Fireball radius
        fireball_radius = 0.1 * (ke_mt ** (1/3)) * 1000
        
        # Seismic magnitude (Richter scale)
        # M = 0.67 * log10(E) + 4.4
        seismic_magnitude = 0.67 * math.log10(ke_mt * 4.184e15) + 4.4
        
        return {
            "blast_radius": blast_radius,
            "thermal_radius": thermal_radius,
            "fireball_radius": fireball_radius,
            "seismic_magnitude": seismic_magnitude
        }
    
    def calculate_tsunami_effects(self, asteroid: Asteroid, location: ImpactLocation, crater_diameter: float) -> Dict[str, float]:
        """Calculate tsunami effects for ocean impacts"""
        
        if location.terrain_type != TerrainType.OCEAN:
            return {"tsunami_height": 0.0, "tsunami_radius": 0.0}
        
        # Energy in megatons
        ke_mt = self.calculate_kinetic_energy(asteroid) / (4.184e15)
        
        # Tsunami height (simplified model)
        # H = 0.5 * (E/ρ)^(1/4) * (d/D)^(1/2)
        # where d is water depth, D is crater diameter
        
        water_depth = location.water_depth or 1000  # Default 1km
        water_density = 1000  # kg/m³
        
        tsunami_height = 0.5 * (ke_mt * 4.184e15 / water_density) ** (1/4) * (water_depth / crater_diameter) ** (1/2)
        
        # Tsunami propagation radius
        tsunami_radius = 1000 * (ke_mt ** (1/3))  # km
        
        return {
            "tsunami_height": tsunami_height,
            "tsunami_radius": tsunami_radius
        }
    
    def calculate_evacuation_radius(self, blast_radius: float, thermal_radius: float, seismic_magnitude: float) -> float:
        """Calculate recommended evacuation radius"""
        
        # Base evacuation radius from blast effects
        evacuation_radius = max(blast_radius, thermal_radius)
        
        # Add seismic effects
        if seismic_magnitude > 6.0:
            evacuation_radius *= 1.5
        
        # Add safety margin
        evacuation_radius *= 1.2
        
        return evacuation_radius
    
    def calculate_impact_result(self, asteroid: Asteroid, location: ImpactLocation) -> Dict[str, Any]:
        """Calculate complete impact result"""
        
        # Atmospheric entry effects
        entry_effects = self.calculate_atmospheric_entry_effects(asteroid)
        
        # Crater formation
        crater_data = self.calculate_crater_formation(asteroid, location)
        
        # Blast effects
        blast_data = self.calculate_blast_effects(asteroid, crater_data["crater_diameter"])
        
        # Tsunami effects
        tsunami_data = self.calculate_tsunami_effects(asteroid, location, crater_data["crater_diameter"])
        
        # Evacuation radius
        evacuation_radius = self.calculate_evacuation_radius(
            blast_data["blast_radius"],
            blast_data["thermal_radius"],
            blast_data["seismic_magnitude"]
        )
        
        # Affected area
        affected_area = math.pi * (evacuation_radius / 1000) ** 2  # km²
        
        return {
            "crater_diameter": crater_data["crater_diameter"],
            "crater_depth": crater_data["crater_depth"],
            "crater_volume": crater_data["crater_volume"],
            "blast_radius": blast_data["blast_radius"],
            "thermal_radius": blast_data["thermal_radius"],
            "seismic_magnitude": blast_data["seismic_magnitude"],
            "tsunami_height": tsunami_data["tsunami_height"],
            "fireball_radius": blast_data["fireball_radius"],
            "evacuation_radius": evacuation_radius,
            "affected_area": affected_area,
            "atmospheric_effects": entry_effects
        }

# Global impact calculator instance
impact_calculator = ImpactCalculator()
