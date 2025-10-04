"""
Simple test for the NASA Meteor Simulator Backend
"""

# Test basic imports
try:
    from app.models.asteroid import AsteroidCreate, AsteroidComposition
    from app.models.impact import ImpactLocation, TerrainType
    from app.physics.impact_calculator import impact_calculator
    from app.physics.damage_assessor import damage_assessor
    print("✅ All imports successful!")
except ImportError as e:
    print(f"❌ Import error: {e}")
    exit(1)

# Test asteroid creation
try:
    asteroid = AsteroidCreate(
        mass=10000000,  # 10,000 tons
        diameter=20,    # 20 meters
        velocity=19000, # 19 km/s
        impact_angle=20, # 20 degrees
        composition=AsteroidComposition.STONY
    )
    print(f"✅ Asteroid created: {asteroid.kinetic_energy_megatons:.2f} megatons")
except Exception as e:
    print(f"❌ Asteroid creation error: {e}")
    exit(1)

# Test location creation
try:
    location = ImpactLocation(
        latitude=40.7128,
        longitude=-74.0060,
        elevation=10,
        terrain_type=TerrainType.URBAN,
        population_density=10000,
        infrastructure_density=0.9
    )
    print(f"✅ Location created: {location.terrain_type}")
except Exception as e:
    print(f"❌ Location creation error: {e}")
    exit(1)

# Test impact calculation
try:
    impact_result = impact_calculator.calculate_impact_result(asteroid, location)
    print(f"✅ Impact calculated: {impact_result['crater_diameter']:.1f}m crater")
except Exception as e:
    print(f"❌ Impact calculation error: {e}")
    exit(1)

# Test damage assessment
try:
    damage_assessment = damage_assessor.assess_damage(asteroid, location, impact_result)
    print(f"✅ Damage assessed: {damage_assessment['estimated_casualties']:,} casualties")
except Exception as e:
    print(f"❌ Damage assessment error: {e}")
    exit(1)

print("\n🎉 All tests passed! The NASA Meteor Simulator Backend is working correctly.")
