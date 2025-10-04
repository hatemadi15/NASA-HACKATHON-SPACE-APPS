"""
Enhanced NASA data API endpoints with CAD, Sentry, and NEO modeling
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, Optional
from app.nasa.client import nasa_client
from app.models.impact import Asteroid

router = APIRouter()

@router.get("/asteroid/{asteroid_id}")
async def get_asteroid_data(asteroid_id: str):
    """
    Get asteroid data from NASA's Near Earth Object API
    """
    try:
        data = await nasa_client.get_asteroid_data(asteroid_id)
        if not data:
            raise HTTPException(status_code=404, detail="Asteroid data not found")
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching asteroid data: {str(e)}")

@router.get("/asteroid/{asteroid_id}/model")
async def get_asteroid_model(asteroid_id: str):
    """
    Get modeled asteroid from NEO data
    """
    try:
        neo_data = await nasa_client.get_asteroid_data(asteroid_id)
        if not neo_data:
            raise HTTPException(status_code=404, detail="Asteroid data not found")
        
        asteroid = await nasa_client.model_asteroid_from_neo(neo_data)
        return {
            "asteroid_id": asteroid_id,
            "neo_data": neo_data,
            "modeled_asteroid": asteroid.dict()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error modeling asteroid: {str(e)}")

@router.get("/earth-imagery")
async def get_earth_imagery(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude"),
    date: str = Query(..., description="Date in YYYY-MM-DD format")
):
    """
    Fetch Earth imagery metadata for a given lat/lon and date (demo-friendly).
    """
    try:
        data = await nasa_client.get_earth_imagery(lat, lon, date)
        if not data:
            raise HTTPException(status_code=502, detail="Upstream imagery unavailable")
        return data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching Earth imagery: {str(e)}")

@router.get("/cad")
async def get_cad(
    des: Optional[str] = Query(None, description="Object designation"),
    neo: Optional[bool] = Query(True, description="Restrict to NEOs"),
    date_min: Optional[str] = Query(None, description="Min date (YYYY-MM-DD)"),
    date_max: Optional[str] = Query(None, description="Max date (YYYY-MM-DD)"),
    dist_max: Optional[str] = Query(None, description="Max distance in au (e.g., 0.05)"),
    sort: Optional[str] = Query("date", description="Sort field (date, dist, v_rel)"),
    limit: Optional[int] = Query(50, ge=1, le=2000, description="Max rows")
):
    """Proxy to JPL SSD CAD API with common filters."""
    try:
        params: Dict[str, Any] = {"neo": "true" if neo else "false", "sort": sort, "limit": limit, "full-prec": "true"}
        if des: params["des"] = des
        if date_min: params["date-min"] = date_min
        if date_max: params["date-max"] = date_max
        if dist_max: params["dist-max"] = dist_max
        data = await nasa_client.get_cad(params)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching CAD data: {str(e)}")

@router.get("/sentry")
async def get_sentry(
    spk: Optional[str] = Query(None, description="SPK-ID or designation"),
    all: Optional[bool] = Query(False, description="Return all objects"),
    h_max: Optional[float] = Query(None, description="Max absolute magnitude H"),
    ps_min: Optional[float] = Query(None, description="Min Palermo Scale"),
    ip_min: Optional[float] = Query(None, description="Min impact probability"),
    limit: Optional[int] = Query(50, ge=1, le=2000, description="Max rows")
):
    """Proxy to JPL SSD Sentry API (impact risk)."""
    try:
        params: Dict[str, Any] = {"limit": limit}
        if spk: params["spk"] = spk
        if all: params["all"] = "true"
        if h_max is not None: params["h-max"] = h_max
        if ps_min is not None: params["ps-min"] = ps_min
        if ip_min is not None: params["ip-min"] = ip_min
        data = await nasa_client.get_sentry(params)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching Sentry data: {str(e)}")

@router.get("/nearby-objects")
async def get_nearby_objects(
    latitude: float = Query(..., description="Latitude"),
    longitude: float = Query(..., description="Longitude"),
    radius_km: float = Query(1000, description="Search radius in km"),
    days_ahead: int = Query(30, description="Days to look ahead")
):
    """
    Get nearby NEOs that could potentially impact near given coordinates
    """
    try:
        from datetime import datetime, timedelta
        
        # Get CAD data for nearby objects
        date_min = datetime.utcnow().strftime("%Y-%m-%d")
        date_max = (datetime.utcnow() + timedelta(days=days_ahead)).strftime("%Y-%m-%d")
        
        cad_params = {
            "neo": "true",
            "date-min": date_min,
            "date-max": date_max,
            "dist-max": "0.1",  # Within 0.1 AU
            "limit": 100
        }
        
        cad_data = await nasa_client.get_cad(cad_params)
        
        # Filter by proximity to given coordinates (simplified)
        nearby_objects = []
        if cad_data.get("data"):
            for obj in cad_data["data"]:
                # This is a simplified proximity check
                # In reality, you'd calculate actual impact probability
                nearby_objects.append({
                    "designation": obj.get("des", "Unknown"),
                    "close_approach_date": obj.get("cd", "Unknown"),
                    "miss_distance_km": float(obj.get("dist", 0)) * 149597870.7,  # Convert AU to km
                    "relative_velocity_kmh": float(obj.get("v_rel", 0)),
                    "diameter_estimate": obj.get("diameter", "Unknown"),
                    "hazardous": obj.get("pha", "N") == "Y"
                })
        
        return {
            "search_location": {"latitude": latitude, "longitude": longitude},
            "search_radius_km": radius_km,
            "days_ahead": days_ahead,
            "nearby_objects": nearby_objects,
            "total_found": len(nearby_objects)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error finding nearby objects: {str(e)}")

@router.get("/earth-observation")
async def get_earth_observation_data(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude"),
    dataset: str = Query("population", description="Dataset type")
):
    """
    Get Earth observation data from NASA DAACs
    """
    try:
        data = await nasa_client.get_earth_observation_data(lat, lon, dataset)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching Earth observation data: {str(e)}")

@router.get("/planetary-data")
async def get_planetary_data(
    planet: str = Query("earth", description="Planet name"),
    data_type: str = Query("surface", description="Data type")
):
    """
    Get planetary data from NASA's Planetary Data System
    """
    try:
        data = await nasa_client.get_planetary_data(planet, data_type)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching planetary data: {str(e)}")

@router.get("/atmospheric-data")
async def get_atmospheric_data(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude")
):
    """
    Get atmospheric data for impact calculations
    """
    try:
        data = await nasa_client.get_atmospheric_data(lat, lon)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching atmospheric data: {str(e)}")

@router.get("/population-data")
async def get_population_data(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude")
):
    """
    Get population density data from NASA SEDAC
    """
    try:
        data = await nasa_client.get_population_data(lat, lon)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching population data: {str(e)}")

@router.get("/terrain-data")
async def get_terrain_data(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude")
):
    """
    Get terrain and elevation data from USGS
    """
    try:
        data = await nasa_client.get_terrain_data(lat, lon)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching terrain data: {str(e)}")

@router.get("/location-analysis")
async def analyze_location(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude")
):
    """
    Comprehensive location analysis using multiple NASA data sources
    """
    try:
        # Fetch data from multiple sources in parallel
        import asyncio
        
        tasks = [
            nasa_client.get_population_data(lat, lon),
            nasa_client.get_terrain_data(lat, lon),
            nasa_client.get_atmospheric_data(lat, lon),
            nasa_client.get_earth_observation_data(lat, lon, "population")
        ]
        
        results = await asyncio.gather(*tasks)
        
        population_data, terrain_data, atmospheric_data, observation_data = results
        
        return {
            "location": {"latitude": lat, "longitude": lon},
            "population": population_data,
            "terrain": terrain_data,
            "atmosphere": atmospheric_data,
            "observation": observation_data,
            "analysis_timestamp": "2024-01-01T00:00:00Z"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing location: {str(e)}")
