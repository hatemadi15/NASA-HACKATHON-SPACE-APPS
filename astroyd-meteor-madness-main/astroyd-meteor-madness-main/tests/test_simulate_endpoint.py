"""
Pytest for the simulation endpoint
"""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_simulate_endpoint_basic():
	payload = {
		"asteroid": {
			"mass": 10000000,
			"diameter": 20,
			"velocity": 19000,
			"impact_angle": 25,
			"composition": "stony"
		},
		"impact_location": {
			"latitude": 34.05,
			"longitude": -118.24,
			"elevation": 100,
			"terrain_type": "urban",
			"population_density": 8000,
			"infrastructure_density": 0.85
		},
		"use_nasa_data": False,
		"use_ml": False
	}

	res = client.post("/api/v1/simulation/simulate", json=payload)
	assert res.status_code == 200
	data = res.json()
	assert "impact_result" in data
	assert data["impact_result"]["crater_diameter"] >= 0
	assert data["damage_assessment"]["estimated_casualties"] >= 0


def test_simulate_endpoint_with_ml():
	payload = {
		"asteroid": {
			"mass": 20000000,
			"diameter": 25,
			"velocity": 20000,
			"impact_angle": 30,
			"composition": "stony"
		},
		"impact_location": {
			"latitude": 40.7128,
			"longitude": -74.0060,
			"elevation": 10,
			"terrain_type": "urban",
			"population_density": 10000,
			"infrastructure_density": 0.9
		},
		"use_nasa_data": False,
		"use_ml": True
	}

	res = client.post("/api/v1/simulation/simulate", json=payload)
	assert res.status_code == 200
	data = res.json()
	assert data["simulation_metadata"]["ml_enhanced"] is True
