"""
Simple test script for the NASA Meteor Simulator Backend
"""

import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

try:
    from app.models.asteroid import AsteroidCreate, AsteroidComposition
    from app.models.impact import ImpactLocation, TerrainType, SimulationRequest
    from app.physics.impact_calculator import impact_calculator
    from app.physics.damage_assessor import damage_assessor
except ImportError as e:
    print(f"Import error: {e}")
    print("Please install required dependencies: pip install -r requirements.txt")
    sys.exit(1)

async def test_simulation():
    """Test a basic meteor impact simulation"""
    
    print("🚀 NASA Meteor Simulator Backend Test")
    print("=" * 50)
    
    # Create test asteroid (similar to Chelyabinsk meteor)
    asteroid = AsteroidCreate(
        mass=10000000,  # 10,000 tons
        diameter=20,    # 20 meters
        velocity=19000, # 19 km/s
        impact_angle=20, # 20 degrees
        composition=AsteroidComposition.STONY
    )
    
    print(f"Asteroid Properties:")
    print(f"  Mass: {asteroid.mass:,} kg")
    print(f"  Diameter: {asteroid.diameter} m")
    print(f"  Velocity: {asteroid.velocity:,} m/s")
    print(f"  Impact Angle: {asteroid.impact_angle}°")
    print(f"  Composition: {asteroid.composition}")
    print(f"  Kinetic Energy: {asteroid.kinetic_energy_megatons:.2f} megatons")
    print()
    
    # Create test impact location (New York City)
    location = ImpactLocation(
        latitude=40.7128,
        longitude=-74.0060,
        elevation=10,
        terrain_type=TerrainType.URBAN,
        population_density=10000,  # people per km²
        infrastructure_density=0.9
    )
    
    print(f"Impact Location:")
    print(f"  Coordinates: {location.latitude}, {location.longitude}")
    print(f"  Terrain: {location.terrain_type}")
    print(f"  Population Density: {location.population_density:,} people/km²")
    print(f"  Infrastructure Density: {location.infrastructure_density}")
    print()
    
    # Calculate impact physics
    print("Calculating Impact Physics...")
    impact_result = impact_calculator.calculate_impact_result(asteroid, location)
    
    print(f"Impact Results:")
    print(f"  Crater Diameter: {impact_result['crater_diameter']:.1f} m")
    print(f"  Crater Depth: {impact_result['crater_depth']:.1f} m")
    print(f"  Blast Radius: {impact_result['blast_radius']:.1f} m")
    print(f"  Thermal Radius: {impact_result['thermal_radius']:.1f} m")
    print(f"  Seismic Magnitude: {impact_result['seismic_magnitude']:.1f}")
    print(f"  Evacuation Radius: {impact_result['evacuation_radius']:.1f} m")
    print(f"  Affected Area: {impact_result['affected_area']:.1f} km²")
    print()
    
    # Assess damage
    print("Assessing Damage...")
    damage_assessment = damage_assessor.assess_damage(asteroid, location, impact_result)
    
    print(f"Damage Assessment:")
    print(f"  Estimated Casualties: {damage_assessment['estimated_casualties']:,}")
    print(f"  Injured: {damage_assessment['injured_count']:,}")
    print(f"  Displaced: {damage_assessment['displaced_count']:,}")
    print(f"  Buildings Destroyed: {damage_assessment['buildings_destroyed']:,}")
    print(f"  Buildings Damaged: {damage_assessment['buildings_damaged']:,}")
    print(f"  Infrastructure Cost: ${damage_assessment['infrastructure_damage_cost']:,.0f}")
    print(f"  Total Economic Cost: ${damage_assessment['total_economic_cost']:,.0f}")
    print(f"  Recovery Time: {damage_assessment['recovery_time_years']:.1f} years")
    print()
    
    print("✅ Test completed successfully!")

if __name__ == "__main__":
    asyncio.run(test_simulation())
