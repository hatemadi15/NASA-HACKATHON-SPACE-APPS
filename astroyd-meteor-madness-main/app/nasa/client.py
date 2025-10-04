"""
NASA API client with enhanced NEO modeling and trajectory calculations
"""

import httpx
import asyncio
import math
from typing import Dict, Any, Optional, List, Tuple
from app.core.config import settings
from app.models.impact import Asteroid, TrajectoryPoint, ImpactLocation
import logging
import time
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class NASAClient:
	"""Enhanced client for NASA APIs with NEO modeling capabilities"""
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

	async def model_asteroid_from_neo(self, neo_data: Dict[str, Any]) -> Asteroid:
		"""Create Asteroid model from NEO data"""
		try:
			# Extract diameter (use average if range given)
			diameter_data = neo_data.get("estimated_diameter", {}).get("meters", {})
			if diameter_data:
				diam_min = diameter_data.get("estimated_diameter_min", 100)
				diam_max = diameter_data.get("estimated_diameter_max", 200)
				diameter = (diam_min + diam_max) / 2
			else:
				diameter = 150.0  # Default

			# Estimate mass from diameter (assuming spherical, stony composition)
			density = 3000.0  # kg/m³ for stony asteroids
			volume = (4/3) * math.pi * (diameter/2)**3
			mass = density * volume

			# Get orbital data for velocity estimation
			orbital_data = neo_data.get("orbital_data", {})
			velocity = 20000.0  # Default impact velocity m/s
			if orbital_data:
				# Use orbital velocity as rough estimate
				semi_major_axis = orbital_data.get("semi_major_axis", 1.5)  # AU
				velocity = math.sqrt(settings.GRAVITATIONAL_CONSTANT * settings.EARTH_MASS / (semi_major_axis * 1.496e11))  # Convert AU to m

			# Determine composition from absolute magnitude
			abs_magnitude = neo_data.get("absolute_magnitude_h", 20.0)
			if abs_magnitude < 16:
				composition = "iron"
			elif abs_magnitude < 20:
				composition = "stony"
			else:
				composition = "carbonaceous"

			return Asteroid(
				mass=mass,
				diameter=diameter,
				velocity=velocity,
				impact_angle=45.0,  # Default impact angle
				composition=composition,
				neo_id=neo_data.get("neo_reference_id"),
				designation=neo_data.get("name"),
				orbital_elements=orbital_data
			)
		except Exception as e:
			logger.error(f"Error modeling asteroid from NEO data: {e}")
			# Return default asteroid
			return Asteroid(
				mass=1e9,  # 1 billion kg
				diameter=150.0,
				velocity=20000.0,
				impact_angle=45.0,
				composition="stony"
			)

	async def calculate_trajectory(self, asteroid: Asteroid, impact_location: ImpactLocation, 
								  time_hours: int = 24) -> List[TrajectoryPoint]:
		"""Calculate asteroid trajectory approaching Earth"""
		try:
			trajectory = []
			earth_radius_km = settings.EARTH_RADIUS / 1000
			
			# Start from high altitude
			start_altitude = 1000.0  # km
			start_distance = start_altitude + earth_radius_km
			
			# Calculate approach trajectory (simplified)
			time_points = 50
			for i in range(time_points):
				progress = i / (time_points - 1)
				
				# Altitude decreases as asteroid approaches
				altitude = start_altitude * (1 - progress) + 0.1
				distance = altitude + earth_radius_km
				
				# Velocity increases due to gravity
				velocity_factor = 1 + (1 - progress) * 0.5
				velocity = asteroid.velocity * velocity_factor
				
				# Calculate position (simplified orbital mechanics)
				lat_offset = (1 - progress) * 10  # degrees
				lon_offset = (1 - progress) * 15
				
				timestamp = datetime.utcnow() + timedelta(hours=time_hours * progress)
				
				trajectory.append(TrajectoryPoint(
					timestamp=timestamp,
					latitude=impact_location.latitude + lat_offset,
					longitude=impact_location.longitude + lon_offset,
					altitude=altitude,
					velocity=velocity,
					distance_to_earth=distance
				))
			
			return trajectory
		except Exception as e:
			logger.error(f"Error calculating trajectory: {e}")
			return []

	async def get_cad(self, params: Dict[str, Any]) -> Dict[str, Any]:
		"""Query JPL SSD CAD API (Close Approach Data)."""
		try:
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
