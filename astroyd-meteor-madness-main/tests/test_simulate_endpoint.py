"""Pytest for the simulation endpoints."""

import pytest
from fastapi.testclient import TestClient

from app.api.v1.endpoints import simulation as simulation_endpoints
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


def test_advanced_metrics_refreshes_population(monkeypatch):
    fetched_density = 4321.0
    captured = {}

    async def fake_population(lat: float, lon: float):  # type: ignore[override]
        captured["called"] = True
        captured["lat"] = lat
        captured["lon"] = lon
        return {"population_density": fetched_density}

    def fake_assess(asteroid, location, impact_result):  # type: ignore[override]
        captured["density_seen"] = location.population_density
        return {
            "estimated_casualties": int(location.population_density),
            "injured_count": int(location.population_density * 2),
            "displaced_count": int(location.population_density * 3),
            "infrastructure_damage_cost": location.population_density * 4,
            "buildings_destroyed": int(location.population_density * 0.1),
            "buildings_damaged": int(location.population_density * 0.2),
            "environmental_impact_score": 1.0,
            "ecosystem_affected_area": 2.0,
            "total_economic_cost": location.population_density * 5,
            "recovery_time_years": 3.5,
        }

    monkeypatch.setattr(
        simulation_endpoints.nasa_client,
        "get_population_data",
        fake_population,
        raising=True,
    )
    monkeypatch.setattr(
        simulation_endpoints.damage_assessor,
        "assess_damage",
        fake_assess,
        raising=True,
    )

    payload = {
        "asteroid": {
            "mass": 5000000,
            "diameter": 15,
            "velocity": 18000,
            "impact_angle": 40,
            "composition": "stony",
        },
        "impact_location": {
            "latitude": 12.34,
            "longitude": 56.78,
            "elevation": 5,
            "terrain_type": "urban",
            "population_density": 0,
            "infrastructure_density": 0.5,
        },
        "use_nasa_population": True,
    }

    res = client.post("/api/v1/simulation/advanced", json=payload)

    assert res.status_code == 200
    data = res.json()

    assert captured.get("called") is True
    assert pytest.approx(fetched_density) == data["population_density"]
    assert pytest.approx(fetched_density) == data["impact_location"]["population_density"]
    assert pytest.approx(fetched_density) == captured.get("density_seen", 0.0)
    assert data["damage_assessment"]["estimated_casualties"] == int(fetched_density)
    assert data["damage_assessment"]["total_economic_cost"] == pytest.approx(fetched_density * 5)
