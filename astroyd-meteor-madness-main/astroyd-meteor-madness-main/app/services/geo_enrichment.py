"""
Geographic enrichment service using NASA/USGS/SEDAC-like data
"""

from typing import Dict, Any
from app.models.impact import ImpactLocation, TerrainType
from app.nasa.client import nasa_client

class GeoEnrichmentService:
	"""Service to enrich ImpactLocation with external data"""

	async def enrich_location(self, location: ImpactLocation) -> ImpactLocation:
		"""Fetch external datasets and merge into ImpactLocation"""
		lat = location.latitude
		lon = location.longitude

		population_data, terrain_data, atmospheric_data = await self._fetch_parallel(lat, lon)

		# Merge values if not provided or to enhance realism
		population_density = population_data.get("population_density", location.population_density)
		elevation = terrain_data.get("elevation", location.elevation)
		soil_type = terrain_data.get("soil_type", location.soil_type)
		terrain_hint = terrain_data.get("terrain_type")

		# Infer terrain type if not specified
		terrain_type = location.terrain_type
		if not terrain_type and terrain_hint:
			terrain_type = TerrainType(terrain_hint) if terrain_hint in [t.value for t in TerrainType] else TerrainType.LAND
		elif not terrain_type:
			terrain_type = TerrainType.LAND

		# If ocean terrain inferred and no water_depth provided, set a reasonable default
		water_depth = location.water_depth
		if terrain_type == TerrainType.OCEAN and water_depth is None:
			water_depth = 3000.0

		return ImpactLocation(
			latitude=lat,
			longitude=lon,
			elevation=elevation,
			terrain_type=terrain_type,
			water_depth=water_depth,
			population_density=population_density,
			infrastructure_density=location.infrastructure_density,
			soil_type=soil_type,
			bedrock_depth=location.bedrock_depth,
		)

	async def _fetch_parallel(self, lat: float, lon: float):
		import asyncio
		tasks = [
			nasa_client.get_population_data(lat, lon),
			nasa_client.get_terrain_data(lat, lon),
			nasa_client.get_atmospheric_data(lat, lon),
		]
		population_data, terrain_data, atmospheric_data = await asyncio.gather(*tasks)
		return population_data, terrain_data, atmospheric_data

geo_enrichment_service = GeoEnrichmentService()
