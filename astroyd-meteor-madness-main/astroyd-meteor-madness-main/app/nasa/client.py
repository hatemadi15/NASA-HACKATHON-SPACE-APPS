"""
NASA API client for data integration
"""

import httpx
import asyncio
from typing import Dict, Any, Optional, List
from app.core.config import settings
import logging
import time

logger = logging.getLogger(__name__)

class NASAClient:
	"""Client for NASA APIs and data sources"""
	def __init__(self):
		self.nasa_api_key = settings.NASA_API_KEY
		self.earthdata_username = settings.NASA_EARTHDATA_USERNAME
		self.earthdata_password = settings.NASA_EARTHDATA_PASSWORD
		self.earthdata_token = settings.NASA_EARTHDATA_TOKEN
		self.usgs_api_key = settings.USGS_API_KEY
		self.noaa_api_key = settings.NOAA_API_KEY
		self.base_urls = {
			"nasa_api": "https://api.nasa.gov",
			"jpl_ssd": "https://ssd-api.jpl.nasa.gov",
			"cmr": "https://cmr.earthdata.nasa.gov",
			"earthdata": "https://search.earthdata.nasa.gov",
			"worldview": "https://worldview.earthdata.nasa.gov",
			"usgs": "https://earthexplorer.usgs.gov",
			"noaa": "https://www.ncei.noaa.gov"
		}

		# Simple in-memory cache for demo resilience
		self._cache: Dict[str, Any] = {}
		self._cache_expiry: Dict[str, float] = {}
		self._demo_fallback = bool(settings.DEMO_MODE)
		self._ttl_seconds = int(settings.CACHE_TTL_SECONDS)

	def _cache_get(self, key: str) -> Optional[Any]:
		"""TTL cache get."""
		exp = self._cache_expiry.get(key)
		if exp is None:
			return None
		if exp < time.time():
			self._cache.pop(key, None)
			self._cache_expiry.pop(key, None)
			return None
		return self._cache.get(key)

	def _cache_set(self, key: str, value: Any) -> None:
		self._cache[key] = value
		self._cache_expiry[key] = time.time() + self._ttl_seconds

	def _earthdata_headers(self) -> Dict[str, str]:
		"""Build auth headers for Earthdata/CMR if token is available"""
		headers: Dict[str, str] = {}
		if self.earthdata_token:
			headers["Authorization"] = f"Bearer {self.earthdata_token}"
		return headers

	async def get_asteroid_data(self, asteroid_id: str) -> Dict[str, Any]:
		"""Get asteroid data from NASA's Near Earth Object API"""
		try:
			cache_key = f"neo:{asteroid_id}"
			cached = self._cache_get(cache_key)
			if cached is not None:
				return cached
			async with httpx.AsyncClient(timeout=10.0) as client:
				url = f"{self.base_urls['nasa_api']}/neo/rest/v1/neo/{asteroid_id}"
				params = {"api_key": self.nasa_api_key} if self.nasa_api_key else {}
				response = await client.get(url, params=params)
				response.raise_for_status()
				data = response.json()
				self._cache_set(cache_key, data)
				return data
		except Exception as e:
			logger.error(f"Error fetching asteroid data: {e}")
			if self._demo_fallback:
				return {"id": asteroid_id, "name": "Impactor-2025", "estimated_diameter": {"meters": {"estimated_diameter_min": 120.0, "estimated_diameter_max": 180.0}}, "is_potentially_hazardous_asteroid": True}
			return {}

	async def get_earth_imagery(self, lat: float, lon: float, date: str) -> Dict[str, Any]:
		"""Fetch EPIC imagery metadata. Demo returns simplified payload."""
		try:
			cache_key = f"epic:{date}"
			cached = self._cache_get(cache_key)
			if cached is not None:
				return cached
			async with httpx.AsyncClient(timeout=10.0) as client:
				url = f"{self.base_urls['nasa_api']}/EPIC/api/natural/date/{date}"
				params = {"api_key": self.nasa_api_key} if self.nasa_api_key else {}
				response = await client.get(url, params=params)
				response.raise_for_status()
				data = response.json()
				self._cache_set(cache_key, data)
				return data
		except Exception as e:
			logger.error(f"Error fetching Earth imagery: {e}")
			if self._demo_fallback:
				return {"date": date, "lat": lat, "lon": lon, "images_available": True}
			return {}

	async def get_earth_observation_data(self, lat: float, lon: float, dataset: str) -> Dict[str, Any]:
		"""Get Earth observation data (placeholder until specific DAAC endpoint wired)"""
		try:
			return {
				"latitude": lat,
				"longitude": lon,
				"dataset": dataset,
				"data_available": True,
				"layers": ["population_density", "land_cover", "elevation", "temperature", "precipitation"]
			}
		except Exception as e:
			logger.error(f"Error fetching Earth observation data: {e}")
			return {}

	async def get_cad(self, params: Dict[str, Any]) -> Dict[str, Any]:
		"""Query JPL SSD CAD API (Close Approach Data)."""
		try:
			# Normalize and cache by sorted params
			items = sorted(params.items())
			cache_key = "cad:" + "&".join([f"{k}={v}" for k, v in items])
			cached = self._cache_get(cache_key)
			if cached is not None:
				return cached
			async with httpx.AsyncClient(timeout=15.0) as client:
				url = f"{self.base_urls['jpl_ssd']}/cad.api"
				response = await client.get(url, params=params)
				response.raise_for_status()
				data = response.json()
				self._cache_set(cache_key, data)
				return data
		except Exception as e:
			logger.error(f"Error fetching CAD data: {e}")
			if self._demo_fallback:
				return {"signature": {"source": "demo"}, "count": 0, "data": []}
			return {}

	async def get_sentry(self, params: Dict[str, Any]) -> Dict[str, Any]:
		"""Query JPL SSD Sentry API (impact risk)."""
		try:
			items = sorted(params.items())
			cache_key = "sentry:" + "&".join([f"{k}={v}" for k, v in items])
			cached = self._cache_get(cache_key)
			if cached is not None:
				return cached
			async with httpx.AsyncClient(timeout=15.0) as client:
				url = f"{self.base_urls['jpl_ssd']}/sentry.api"
				response = await client.get(url, params=params)
				response.raise_for_status()
				data = response.json()
				self._cache_set(cache_key, data)
				return data
		except Exception as e:
			logger.error(f"Error fetching Sentry data: {e}")
			if self._demo_fallback:
				return {"signature": {"source": "demo"}, "count": 0, "data": []}
			return {}

	async def get_planetary_data(self, planet: str, data_type: str) -> Dict[str, Any]:
		"""Get planetary data from NASA's Planetary Data System (placeholder)"""
		try:
			return {"planet": planet, "data_type": data_type, "available": True, "sources": ["pds.nasa.gov"]}
		except Exception as e:
			logger.error(f"Error fetching planetary data: {e}")
			return {}

	async def get_atmospheric_data(self, lat: float, lon: float) -> Dict[str, Any]:
		"""Get atmospheric data for impact calculations (placeholder)"""
		try:
			return {"latitude": lat, "longitude": lon, "atmospheric_pressure": 101325.0, "temperature": 288.15, "density": 1.225, "wind_speed": 0.0, "humidity": 0.5}
		except Exception as e:
			logger.error(f"Error fetching atmospheric data: {e}")
			return {}

	async def get_population_data(self, lat: float, lon: float) -> Dict[str, Any]:
		"""Get population density from SEDAC GPWv4 (placeholder; token-ready)"""
		try:
			cache_key = f"pop:{round(lat,3)}:{round(lon,3)}"
			cached = self._cache_get(cache_key)
			if cached is not None:
				return cached
			headers = self._earthdata_headers()
			# Demo heuristic: higher density near urban-like lat/lon bands
			base_density = 50.0
			if abs(lat) < 30:
				base_density = 200.0
			elif abs(lat) < 50:
				base_density = 120.0
			data = {"latitude": lat, "longitude": lon, "population_density": base_density, "total_population": int(base_density * 1000), "urban_percentage": 0.6, "data_year": 2020}
			self._cache_set(cache_key, data)
			return data
		except Exception as e:
			logger.error(f"Error fetching population data: {e}")
			if self._demo_fallback:
				return {"latitude": lat, "longitude": lon, "population_density": 100.0, "total_population": 10000, "urban_percentage": 0.8, "data_year": 2020}
			return {}

	async def get_terrain_data(self, lat: float, lon: float) -> Dict[str, Any]:
		"""Get elevation/terrain (placeholder; will use NASADEM/SRTM with token when enabled)"""
		try:
			cache_key = f"terrain:{round(lat,3)}:{round(lon,3)}"
			cached = self._cache_get(cache_key)
			if cached is not None:
				return cached
			headers = self._earthdata_headers()
			# Demo heuristic: rudimentary elevation by latitude; mark ocean for very low elevation near coasts
			elevation = max(0.0, 2000.0 * (1 - abs(lat) / 90.0))
			terrain_type = "land"
			if abs(lat) < 5 and abs(lon) < 5:
				terrain_type = "ocean"
				elevation = 0.0
			data = {"latitude": lat, "longitude": lon, "elevation": elevation, "slope": 0.0, "aspect": 0.0, "terrain_type": terrain_type, "soil_type": "clay"}
			self._cache_set(cache_key, data)
			return data
		except Exception as e:
			logger.error(f"Error fetching terrain data: {e}")
			if self._demo_fallback:
				return {"latitude": lat, "longitude": lon, "elevation": 0.0, "slope": 0.0, "aspect": 0.0, "terrain_type": "land", "soil_type": "clay"}
			return {}

# Global NASA client instance
nasa_client = NASAClient()
