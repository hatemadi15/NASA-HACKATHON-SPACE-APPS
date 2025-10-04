# NASA Meteor Simulator Backend

A comprehensive backend system for simulating meteor impacts with real NASA data integration.

## Features

- **Impact Physics Engine**: Accurate calculations of crater formation, blast radius, and energy release
- **Damage Assessment**: Human casualties, infrastructure damage, and environmental impact modeling
- **NASA Data Integration**: Real-time data from NASA APIs and Earth observation systems
- **Machine Learning**: Enhanced predictions using historical impact data
- **Geographic Analysis**: Population density mapping and terrain effects
- **Multi-Planet Support**: Impact simulations for various planetary bodies

## NASA Data Sources

- **NASA Earthdata Search**: Atmospheric and surface data
- **NASA Open APIs**: Real-time astronomical data
- **GIBS/Worldview**: Earth observation layers
- **USGS EarthExplorer**: High-resolution terrain data
- **NOAA Open Data**: Atmospheric and oceanographic data
- **Planetary Data System (PDS)**: Planetary impact data

## Quick Start

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
cp env.example .env
# Edit .env with your configuration; create .env.local for secrets
# Example for live NEO API:
# echo "NASA_API_KEY=YOUR_KEY" >> .env.local
```

3. Run the backend API:
```bash
uvicorn app.main:app --reload
```

4. Serve the frontend:
   - **Easiest:** the API process now exposes the UI at `/ui`, so once the backend is running you can browse to `http://127.0.0.1:8000/ui/`.
   - **Optional standalone host:**
     ```bash
     uvicorn app.frontend:app --host 0.0.0.0 --port 4173
     ```
     The JavaScript client auto-detects the backend URL, so you can open `http://127.0.0.1:4173/` without editing any configuration.

### Environment Variables

Key variables (see `env.example`):
- `NASA_API_KEY`: Required for live NASA NEO/EPIC APIs; optional in DEMO_MODE
- `DEMO_MODE`: If true, enables safe fallbacks and demo heuristics
- `CACHE_TTL_SECONDS`: In-memory cache TTL for NASA client
- `CORS_ALLOW_ORIGINS`: Comma-separated origins for CORS (e.g., http://localhost:3000)

### Using Your NASA API Key

Keep secrets out of version control:
```bash
cp env.example .env
echo "NASA_API_KEY=YOUR_KEY" >> .env.local
```

## API Documentation

Once running, visit `http://localhost:8000/docs` for interactive API documentation.

## Project Structure

```
app/
├── main.py                 # FastAPI application entry point
├── core/                   # Core configuration and utilities
├── models/                 # Pydantic data models
├── services/               # Business logic services
├── physics/                # Impact physics calculations
├── nasa/                   # NASA API integration
├── ml/                     # Machine learning models
├── database/               # Database models and connections
└── tests/                  # Test suite
```
