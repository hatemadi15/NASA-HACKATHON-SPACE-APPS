"""Tests for NASAClient.get_population_data."""

from pathlib import Path
import sys

import pytest

import httpx

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.nasa.client import NASAClient


class _DummyResponse:
        def __init__(self, payload):
                self._payload = payload

        def raise_for_status(self) -> None:
                return None

        def json(self):
                return self._payload


class _DummyAsyncClient:
        def __init__(self, response_payload, captured):
                self._payload = response_payload
                self._captured = captured
                self._captured["client_created"] = self._captured.get("client_created", 0) + 1

        async def __aenter__(self):
                return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
                return False

        async def get(self, url, params=None):
                self._captured["url"] = url
                self._captured["params"] = params
                self._captured["call_count"] = self._captured.get("call_count", 0) + 1
                return _DummyResponse(self._payload)


@pytest.mark.asyncio
async def test_get_population_data_fetches_density(monkeypatch):
        payload = {
                "features": [
                        {
                                "attributes": {
                                        "Data_Value": "321.5",
                                }
                        }
                ]
        }
        captured = {}

        def _client_factory(*args, **kwargs):
                return _DummyAsyncClient(payload, captured)

        monkeypatch.setattr(httpx, "AsyncClient", _client_factory)

        nasa_client = NASAClient()
        nasa_client.earthdata_token = "token-123"

        lat = 10.1234
        lon = -20.5678

        data = await nasa_client.get_population_data(lat, lon)

        assert data["population_density"] == pytest.approx(321.5)
        assert data["total_population"] == int(321.5 * 1000)
        assert data["data_year"] == 2020
        assert data["data_source"] == "SEDAC GPWv4 Population Density (2020)"

        assert captured["url"].endswith("/MapServer/0/query")
        expected_geometry = f"{lon},{lat}"
        assert captured["params"]["geometry"] == expected_geometry
        assert captured["params"]["token"] == "token-123"
        assert captured["params"]["outFields"] == "Data_Value"
        assert captured.get("call_count") == 1

        # Second call should hit the cache and avoid another HTTP request
        cached = await nasa_client.get_population_data(lat, lon)

        assert cached is data
        assert captured.get("client_created") == 1
        assert captured.get("call_count") == 1
