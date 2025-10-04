// Cesium visualization logic for meteor impact simulator
// Handles all DOM elements and events

export function setupCesiumVisualization(containerId) {
  // Wait for DOM to be ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => runCesium(containerId));
  } else {
    runCesium(containerId);
  }
}

function runCesium(containerId) {
  try {
    Cesium.Ion.defaultAccessToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiI1ZGMyMzExNS0yMDA3LTQzOTUtYWI4Zi01MTE1NDVkZjA5MmQiLCJpZCI6MzM4MzI2LCJpYXQiOjE3NTk1ODkyMjB9.mKL-h_yoK40tAU5y0x366QdYPvh_Gb1-slJDDoY-Atk';
      const viewer = new Cesium.Viewer(containerId, {
      terrain: Cesium.Terrain.fromWorldTerrain(),
      baseLayerPicker: false
    });

    viewer.infoBox.frame.sandbox = "allow-same-origin allow-top-navigation allow-pointer-lock allow-popups allow-forms allow-scripts";

    const NASA_API_KEY = window.NASA_API_KEY || 'DEMO_KEY';
    const NEO_API_URL = 'https://api.nasa.gov/neo/rest/v1/feed';

    // State
    const toNumber = (value, fallback) => {
      if (value === null || value === undefined || value === '') {
        return fallback;
      }
      const num = Number(value);
      return Number.isFinite(num) ? num : fallback;
    };

    const isFiniteNumber = (value) => typeof value === 'number' && Number.isFinite(value);

    const DEFAULT_LOCATION = {
      latitude: 33.8938,
      longitude: 35.5018,
      elevation: 0,
      terrain_type: 'land',
      population_density: 0,
      blast_radius: 50000,
      crater_diameter: 1200,
      thermal_radius: 80000,
      fireball_radius: 20000,
      evacuation_radius: 100000,
      launch_longitude: null,
      launch_latitude: null,
      launch_altitude: 100000
    };

    const DEFAULT_IMPACT_RESULT = {
      crater_diameter: 1200,
      crater_depth: 240,
      crater_volume: 0,
      blast_radius: 50000,
      thermal_radius: 80000,
      fireball_radius: 20000,
      seismic_magnitude: 0,
      tsunami_height: 0,
      atmospheric_effects: {},
      impact_zones: [],
      evacuation_radius: 100000,
      affected_area: 0
    };

    const DEFAULT_ASTEROID = {
      diameter: 50,
      mass: 1000000,
      velocity: 20000,
      density: 3000,
      impact_angle: 45,
      composition: 'stony'
    };

    const normalizeSimulationPayload = (raw) => {
      if (!raw) {
        return {
          location: { ...DEFAULT_LOCATION },
          impactResult: { ...DEFAULT_IMPACT_RESULT },
          asteroid: { ...DEFAULT_ASTEROID },
          metadata: null,
          simulationId: null
        };
      }
      const payload = typeof raw === 'object' ? raw : {};
      const locationSource = payload.location ?? payload;
      const impactSource = payload.impactResult ?? payload.impact_result ?? payload;
      const asteroidSource = payload.asteroid ?? payload;

      const location = {
        latitude: toNumber(locationSource.latitude, DEFAULT_LOCATION.latitude),
        longitude: toNumber(locationSource.longitude, DEFAULT_LOCATION.longitude),
        elevation: toNumber(locationSource.elevation, DEFAULT_LOCATION.elevation),
        terrain_type: locationSource.terrain_type ?? DEFAULT_LOCATION.terrain_type,
        population_density: toNumber(locationSource.population_density, DEFAULT_LOCATION.population_density),
        blast_radius: toNumber(impactSource.blast_radius ?? locationSource.blast_radius, DEFAULT_LOCATION.blast_radius),
        crater_diameter: toNumber(impactSource.crater_diameter ?? locationSource.crater_diameter, DEFAULT_LOCATION.crater_diameter),
        thermal_radius: toNumber(impactSource.thermal_radius ?? locationSource.thermal_radius, DEFAULT_LOCATION.thermal_radius),
        fireball_radius: toNumber(impactSource.fireball_radius ?? locationSource.fireball_radius, DEFAULT_LOCATION.fireball_radius),
        evacuation_radius: toNumber(impactSource.evacuation_radius ?? locationSource.evacuation_radius, DEFAULT_LOCATION.evacuation_radius),
        launch_longitude: toNumber(locationSource.launch_longitude ?? payload.launch_longitude, DEFAULT_LOCATION.launch_longitude),
        launch_latitude: toNumber(locationSource.launch_latitude ?? payload.launch_latitude, DEFAULT_LOCATION.launch_latitude),
        launch_altitude: toNumber(locationSource.launch_altitude ?? payload.launch_altitude, DEFAULT_LOCATION.launch_altitude)
      };

      const impactZones = Array.isArray(impactSource.impact_zones)
        ? impactSource.impact_zones
        : (Array.isArray(payload.impact_zones) ? payload.impact_zones : []);

      const impactResult = {
        ...DEFAULT_IMPACT_RESULT,
        ...impactSource,
        blast_radius: location.blast_radius,
        crater_diameter: location.crater_diameter,
        thermal_radius: location.thermal_radius,
        fireball_radius: location.fireball_radius,
        evacuation_radius: location.evacuation_radius,
        impact_zones: impactZones,
        atmospheric_effects: impactSource.atmospheric_effects ?? DEFAULT_IMPACT_RESULT.atmospheric_effects
      };

      const asteroid = {
        ...DEFAULT_ASTEROID,
        ...asteroidSource,
        diameter: toNumber(asteroidSource.diameter ?? asteroidSource.size ?? payload.asteroid_size, DEFAULT_ASTEROID.diameter),
        mass: toNumber(asteroidSource.mass ?? payload.asteroid_mass, DEFAULT_ASTEROID.mass),
        velocity: toNumber(asteroidSource.velocity ?? asteroidSource.speed ?? payload.asteroid_speed, DEFAULT_ASTEROID.velocity),
        density: toNumber(asteroidSource.density ?? payload.asteroid_density, DEFAULT_ASTEROID.density),
        impact_angle: toNumber(asteroidSource.impact_angle ?? payload.impact_angle, DEFAULT_ASTEROID.impact_angle),
        composition: asteroidSource.composition ?? payload.asteroid_composition ?? DEFAULT_ASTEROID.composition
      };

      return {
        location,
        impactResult,
        asteroid,
        metadata: payload.metadata ?? payload.simulation_metadata ?? null,
        simulationId: payload.simulationId ?? payload.simulation_id ?? null
      };
    };

   // Cesium visualization logic for meteor impact simulator
// Handles all DOM elements and events

export function setupCesiumVisualization(containerId) {
  // Wait for DOM to be ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => runCesium(containerId));
  } else {
    runCesium(containerId);
  }
}

function runCesium(containerId) {
  try {
    Cesium.Ion.defaultAccessToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiI1ZGMyMzExNS0yMDA3LTQzOTUtYWI4Zi01MTE1NDVkZjA5MmQiLCJpZCI6MzM4MzI2LCJpYXQiOjE3NTk1ODkyMjB9.mKL-h_yoK40tAU5y0x366QdYPvh_Gb1-slJDDoY-Atk';
    const viewer = new Cesium.Viewer(containerId, {
      terrain: Cesium.Terrain.fromWorldTerrain(),
      baseLayerPicker: false
    });

    viewer.infoBox.frame.sandbox = "allow-same-origin allow-top-navigation allow-pointer-lock allow-popups allow-forms allow-scripts";
    const viewer = new Cesium.Viewer(containerId, {
      terrain: Cesium.Terrain.fromWorldTerrain(),
      baseLayerPicker: false
    });

    viewer.infoBox.frame.sandbox = "allow-same-origin allow-top-navigation allow-pointer-lock allow-popups allow-forms allow-scripts";

    const NASA_API_KEY = window.NASA_API_KEY || 'DEMO_KEY';
    const NEO_API_URL = 'https://api.nasa.gov/neo/rest/v1/feed';

    // State
    const toNumber = (value, fallback) => {
      if (value === null || value === undefined || value === '') {
        return fallback;
      }
      const num = Number(value);
      return Number.isFinite(num) ? num : fallback;
    };

    const isFiniteNumber = (value) => typeof value === 'number' && Number.isFinite(value);

    const DEFAULT_LOCATION = {
      latitude: 33.8938,
      longitude: 35.5018,
      elevation: 0,
      terrain_type: 'land',
      population_density: 0,
      blast_radius: 50000,
      crater_diameter: 1200,
      thermal_radius: 80000,
      fireball_radius: 20000,
      evacuation_radius: 100000,
      launch_longitude: null,
      launch_latitude: null,
@@ -116,116 +119,344 @@ function runCesium(containerId) {
        evacuation_radius: location.evacuation_radius,
        impact_zones: impactZones,
        atmospheric_effects: impactSource.atmospheric_effects ?? DEFAULT_IMPACT_RESULT.atmospheric_effects
      };

      const asteroid = {
        ...DEFAULT_ASTEROID,
        ...asteroidSource,
        diameter: toNumber(asteroidSource.diameter ?? asteroidSource.size ?? payload.asteroid_size, DEFAULT_ASTEROID.diameter),
        mass: toNumber(asteroidSource.mass ?? payload.asteroid_mass, DEFAULT_ASTEROID.mass),
        velocity: toNumber(asteroidSource.velocity ?? asteroidSource.speed ?? payload.asteroid_speed, DEFAULT_ASTEROID.velocity),
        density: toNumber(asteroidSource.density ?? payload.asteroid_density, DEFAULT_ASTEROID.density),
        impact_angle: toNumber(asteroidSource.impact_angle ?? payload.impact_angle, DEFAULT_ASTEROID.impact_angle),
        composition: asteroidSource.composition ?? payload.asteroid_composition ?? DEFAULT_ASTEROID.composition
      };

      return {
        location,
        impactResult,
        asteroid,
        metadata: payload.metadata ?? payload.simulation_metadata ?? null,
        simulationId: payload.simulationId ?? payload.simulation_id ?? null
      };
    };

    const state = {
      activeAnimations: new Set(),
      visualizationEntities: new Set(),
      craterEntities: new Set(),
      isShowingCrater: false
    };

    let currentSimulation = normalizeSimulationPayload(window.getImpactSettings ? window.getImpactSettings() : null);
    const state = {
      activeAnimations: new Set(),
      visualizationEntities: new Set(),
      craterEntities: new Set(),
      neoEntities: new Set(),
      isShowingCrater: false
    };

    let currentSimulation = normalizeSimulationPayload(window.getImpactSettings ? window.getImpactSettings() : null);

    const neoState = {
      data: [],
      fetchedAt: 0,
      entities: [],
      visible: false,
      loading: false,
      rotationStart: Date.now()
    };
    let impact_location = { ...currentSimulation.location };
    let impact_result = { ...currentSimulation.impactResult };
    let asteroid_properties = {
      size: currentSimulation.asteroid.diameter,
      speed: currentSimulation.asteroid.velocity,
      mass: currentSimulation.asteroid.mass,
      density: currentSimulation.asteroid.density,
      impact_angle: currentSimulation.asteroid.impact_angle,
      composition: currentSimulation.asteroid.composition
    };
    let impactCartesian = Cesium.Cartesian3.fromDegrees(
      impact_location.longitude,
      impact_location.latitude,
      impact_location.elevation
    );

    function applySimulationState(payload) {
      if (payload) {
        currentSimulation = normalizeSimulationPayload(payload);
      }
      if (!currentSimulation) {
        currentSimulation = normalizeSimulationPayload(null);
      }
      impact_location = { ...impact_location, ...currentSimulation.location };
      impact_result = { ...impact_result, ...currentSimulation.impactResult };
      asteroid_properties = {
        size: currentSimulation.asteroid.diameter,
        speed: currentSimulation.asteroid.velocity,
        mass: currentSimulation.asteroid.mass,
        density: currentSimulation.asteroid.density,
        impact_angle: currentSimulation.asteroid.impact_angle,
        composition: currentSimulation.asteroid.composition
      };
      impactCartesian = Cesium.Cartesian3.fromDegrees(
        impact_location.longitude,
        impact_location.latitude,
        impact_location.elevation
      );
    }

    applySimulationState();

    window.addEventListener('impactSettingsChanged', (event) => {
      console.log('impactSettingsChanged event received', event.detail);
      applySimulationState(event.detail);
      createDangerZones();
    });

    const neoToggleButton = document.getElementById('neoToggleButton');

    const clamp = (value, min, max) => Math.min(Math.max(value, min), max);

    const seededRandom = (seed) => {
      const x = Math.sin(seed) * 10000;
      return x - Math.floor(x);
    };

    const hashString = (value) => {
      if (!value) return 0;
      let hash = 0;
      for (let i = 0; i < value.length; i++) {
        hash = (hash << 5) - hash + value.charCodeAt(i);
        hash |= 0;
      }
      return Math.abs(hash);
    };

    const neoHelpers = {
      setButtonState({ text, loading = false, error = false }) {
        if (!neoToggleButton) return;
        if (typeof text === 'string') {
          neoToggleButton.textContent = text;
        }
        neoToggleButton.classList.toggle('loading', loading);
        neoToggleButton.disabled = loading;
        neoToggleButton.setAttribute('aria-busy', loading ? 'true' : 'false');
        if (error) {
          neoToggleButton.setAttribute('title', typeof error === 'string' ? error : 'Unable to load NEO data');
        } else {
          neoToggleButton.removeAttribute('title');
        }
      },
      clearEntities() {
        neoState.entities.forEach((entity) => {
          state.neoEntities.delete(entity);
          viewer.entities.remove(entity);
        });
        neoState.entities = [];
      },
      ensureVisibility(visible) {
        neoState.entities.forEach((entity) => {
          entity.show = visible;
        });
      },
      computePlacement(neo, index) {
        const seedSource = `${neo.id || ''}-${neo.name || ''}-${index}`;
        const hash = hashString(seedSource) + 1;
        const baseLon = (hash % 360) - 180;
        const baseLat = ((Math.floor(hash / 7) % 120) - 60);
        const missDistanceKm = Number.isFinite(neo.missDistanceKm) ? neo.missDistanceKm : 0;
        const scaledDistanceMeters = clamp(missDistanceKm * 1000, 400000, 20000000);
        return {
          baseLon,
          baseLat,
          altitude: scaledDistanceMeters,
          angularSpeed: clamp((neo.relativeVelocityKps || 5) * 0.04, 0.2, 8),
          inclination: (seededRandom(hash) * 40) - 20
        };
      },
      createDynamicPosition(placement) {
        const { baseLon, baseLat, altitude, angularSpeed, inclination } = placement;
        return new Cesium.CallbackProperty((time, result) => {
          const nowDate = Cesium.JulianDate.toDate(time);
          const seconds = (nowDate.getTime() - neoState.rotationStart) / 1000;
          const currentLon = baseLon + (seconds * angularSpeed);
          const oscillation = Math.sin(seconds / 180) * 5;
          const lat = clamp(baseLat + oscillation + inclination * Math.sin(seconds / 600), -85, 85);
          const normalizedLon = ((currentLon + 540) % 360) - 180;
          return Cesium.Cartesian3.fromDegrees(normalizedLon, lat, altitude, Cesium.Ellipsoid.WGS84, result);
        }, false);
      }
    };

    async function fetchNeoFeed() {
      const today = new Date();
      const dateStr = today.toISOString().slice(0, 10);
      const url = `${NEO_API_URL}?start_date=${dateStr}&end_date=${dateStr}&detailed=true&api_key=${encodeURIComponent(NASA_API_KEY)}`;
      const response = await fetch(url);
      if (!response.ok) {
        const body = await response.text();
        throw new Error(`NASA NEO feed failed (${response.status}): ${body}`);
      }
      return response.json();
    }

    function transformNeoData(raw) {
      const results = [];
      if (!raw || !raw.near_earth_objects) {
        return results;
      }
      Object.values(raw.near_earth_objects).forEach((dateList) => {
        if (!Array.isArray(dateList)) return;
        dateList.forEach((neo) => {
          const approach = Array.isArray(neo.close_approach_data)
            ? neo.close_approach_data.find((entry) => entry.orbiting_body === 'Earth')
            : null;
          if (!approach) {
            return;
          }
          const missDistanceKm = Number(approach.miss_distance?.kilometers);
          if (!Number.isFinite(missDistanceKm)) {
            return;
          }
          const approachDate = approach.close_approach_date_full || approach.close_approach_date;
          const relativeVelocityKps = Number(approach.relative_velocity?.kilometers_per_second);
          results.push({
            id: neo.id,
            name: neo.name,
            approachDate,
            missDistanceKm,
            relativeVelocityKps,
            magnitude: Number(neo.absolute_magnitude_h),
            isPotentiallyHazardous: Boolean(neo.is_potentially_hazardous_asteroid)
          });
        });
      });
      results.sort((a, b) => a.missDistanceKm - b.missDistanceKm);
      return results;
    }

    function renderNeoEntities() {
      if (!neoState.data.length) {
        neoHelpers.clearEntities();
        return;
      }
      neoHelpers.clearEntities();
      neoState.rotationStart = Date.now();
      const limit = Math.min(neoState.data.length, 25);
      for (let i = 0; i < limit; i++) {
        const neo = neoState.data[i];
        const placement = neoHelpers.computePlacement(neo, i);
        const position = neoHelpers.createDynamicPosition(placement);
        const entity = viewer.entities.add({
          position,
          point: {
            pixelSize: 12,
            color: neo.isPotentiallyHazardous ? Cesium.Color.RED : Cesium.Color.CYAN,
            outlineWidth: 2,
            outlineColor: Cesium.Color.BLACK
          },
          label: {
            text: neo.name,
            font: '12px "Helvetica Neue", Arial, sans-serif',
            fillColor: Cesium.Color.WHITE,
            outlineColor: Cesium.Color.BLACK,
            outlineWidth: 2,
            style: Cesium.LabelStyle.FILL_AND_OUTLINE,
            pixelOffset: new Cesium.Cartesian2(0, -18),
            showBackground: true,
            backgroundColor: Cesium.Color.fromAlpha(Cesium.Color.BLACK, 0.6)
          },
          description: `
            <div style="font-family:sans-serif;">
              <h3 style="margin-top:0;">${neo.name}</h3>
              <p><strong>Miss Distance:</strong> ${neo.missDistanceKm.toLocaleString(undefined, { maximumFractionDigits: 0 })} km</p>
              <p><strong>Relative Velocity:</strong> ${Number.isFinite(neo.relativeVelocityKps) ? neo.relativeVelocityKps.toFixed(2) : 'Unknown'} km/s</p>
              ${neo.approachDate ? `<p><strong>Close Approach:</strong> ${neo.approachDate}</p>` : ''}
              ${Number.isFinite(neo.magnitude) ? `<p><strong>Absolute Magnitude:</strong> ${neo.magnitude.toFixed(1)}</p>` : ''}
              <p><strong>Potentially Hazardous:</strong> ${neo.isPotentiallyHazardous ? 'Yes' : 'No'}</p>
            </div>
          `
        });
        entity.show = neoState.visible;
        state.neoEntities.add(entity);
        neoState.entities.push(entity);
      }
    }

    async function toggleNeoLayer() {
      if (!neoToggleButton) {
        return;
      }
      if (neoState.loading) {
        return;
      }
      if (neoState.visible) {
        neoState.visible = false;
        neoHelpers.ensureVisibility(false);
        neoHelpers.setButtonState({ text: 'Show NEOs' });
        return;
      }
      try {
        const isCacheFresh = neoState.data.length && (Date.now() - neoState.fetchedAt < 10 * 60 * 1000);
        if (!isCacheFresh) {
          neoState.loading = true;
          neoHelpers.setButtonState({ text: 'Loading NEOs...', loading: true });
          const feed = await fetchNeoFeed();
          neoState.data = transformNeoData(feed);
          neoState.fetchedAt = Date.now();
        }
        renderNeoEntities();
        neoState.visible = true;
        neoHelpers.ensureVisibility(true);
        const buttonText = neoState.data.length ? `Hide NEOs (${neoState.data.length})` : 'Hide NEOs';
        neoHelpers.setButtonState({ text: buttonText });
      } catch (fetchError) {
        console.error('Failed to load NASA NEO data', fetchError);
        neoHelpers.setButtonState({ text: 'Retry NEOs', error: fetchError.message });
      } finally {
        neoState.loading = false;
        if (!neoState.visible && neoToggleButton.textContent === 'Loading NEOs...') {
          neoHelpers.setButtonState({ text: 'Show NEOs' });
        }
      }
    }

    if (neoToggleButton) {
      neoToggleButton.addEventListener('click', toggleNeoLayer);
      neoHelpers.setButtonState({ text: 'Show NEOs' });
    }
    // Animation cleanup function
     function cleanupAnimations() {
      state.activeAnimations.clear();
      viewer.entities.values.slice().forEach(entity => {
        if (
          !state.visualizationEntities.has(entity) &&
          !state.craterEntities.has(entity) &&
          !state.neoEntities.has(entity) &&
          entity !== asteroidEntity
        ) {
          viewer.entities.remove(entity);
        }
      });
    }

    // Danger zones visualization
    function createDangerZones() {
      console.log("createDangerZones called");
      state.visualizationEntities.forEach(entity => viewer.entities.remove(entity));
      state.visualizationEntities.clear();
      const rings = [
        { radius: impact_result.blast_radius, color: Cesium.Color.RED.withAlpha(0.3), name: 'Blast Radius' },
        { radius: impact_result.thermal_radius, color: Cesium.Color.ORANGE.withAlpha(0.2), name: 'Thermal Radius' },
        { radius: impact_result.fireball_radius, color: Cesium.Color.YELLOW.withAlpha(0.2), name: 'Fireball Radius' },
        { radius: impact_result.evacuation_radius, color: Cesium.Color.BLUE.withAlpha(0.1), name: 'Evacuation Radius' }
      ];
      const impactPoint = viewer.entities.add({
        position: impactCartesian,
        point: { pixelSize: 20, color: Cesium.Color.RED },
        description: 'Impact Point'
      });
      state.visualizationEntities.add(impactPoint);
      rings.forEach((ring, index) => {
        setTimeout(() => {
          const entity = viewer.entities.add({
            position: impactCartesian,
            ellipse: {
              semiMajorAxis: ring.radius,
              semiMinorAxis: ring.radius,
              material: ring.color,
              outline: true,
              outlineColor: ring.color.withAlpha(0.5)
            },
            description: ring.name
          });
          state.visualizationEntities.add(entity);
        }, index * 300);
      });
    }

    createDangerZones();

    // Create permanent crater
    function createCrater() {
      state.craterEntities.forEach(entity => viewer.entities.remove(entity));
      state.craterEntities.clear();
      const craterDiameter = impact_result.crater_diameter * 5.5;
      const rimRadius = craterDiameter * 0.7;
      const crater = viewer.entities.add({
        position: impactCartesian,
        ellipse: {
          semiMajorAxis: craterDiameter / 2,
          semiMinorAxis: craterDiameter / 2,
          height: 0,
          extrudedHeight: -craterDiameter * 0.22,
          material: new Cesium.ImageMaterialProperty({
            image: (() => {
              const canvas = document.createElement('canvas');
              canvas.width = canvas.height = 256;
              const ctx = canvas.getContext('2d');
              const grad = ctx.createRadialGradient(128, 128, 0, 128, 128, 128);
              grad.addColorStop(0, 'rgba(30,30,30,1)');
              grad.addColorStop(0.18, 'rgba(80,80,80,0.85)');
              grad.addColorStop(0.4, 'rgba(160,160,160,0.55)');
              grad.addColorStop(0.7, 'rgba(220,220,220,0.25)');
              grad.addColorStop(0.92, 'rgba(255,255,255,0.7)');
              grad.addColorStop(1, 'rgba(0,0,0,0)');
              ctx.globalAlpha = 1.0;
              ctx.fillStyle = grad;
              ctx.beginPath();
              ctx.arc(128, 128, 128, 0, 2 * Math.PI);
              ctx.fill();
              ctx.globalAlpha = 0.22;
              for (let i = 0; i < 1200; i++) {
                ctx.fillStyle = `rgba(60,60,60,${Math.random() * 0.25})`;
                ctx.beginPath();
                ctx.arc(Math.random() * 256, Math.random() * 256, 1 + Math.random() * 2, 0, 2 * Math.PI);
                ctx.fill();
              }
              return canvas;
            })(),
            transparent: true
          }),
          outline: false
        }
      });
      state.craterEntities.add(crater);
      const rim = viewer.entities.add({
        position: impactCartesian,
        ellipse: {
          semiMajorAxis: rimRadius,
          semiMinorAxis: rimRadius,
          height: 0,
          extrudedHeight: craterDiameter * 0.09,
          material: Cesium.Color.WHITE.withAlpha(0.7),
          outline: false
        }
      });
      state.craterEntities.add(rim);
      const debrisCount = 30;
      for (let i = 0; i < debrisCount; i++) {
        const angle = (i / debrisCount) * Math.PI * 2;
        const distance = craterDiameter * (0.7 + Math.random() * 0.6);
        const debrisPos = Cesium.Cartesian3.fromDegrees(
          impact_location.longitude + (Math.cos(angle) * distance / 111000),
          impact_location.latitude + (Math.sin(angle) * distance / 111000),
          0
        );
        const debris = viewer.entities.add({
          position: debrisPos,
          ellipse: {
            semiMajorAxis: distance * 0.03,
            semiMinorAxis: distance * 0.03,
            material: Cesium.Color.DARKGRAY.withAlpha(0.18),
            height: 0,
            extrudedHeight: distance * 0.01
          }
        });
        state.craterEntities.add(debris);
      }
    }

    // Asteroid trajectory and impact sequence
    let cameraMode = 'impact';
    let asteroidEntity = null;
    function animateAsteroidAndImpact() {
      // Use asteroid speed to affect animation duration and clock multiplier
      // Use asteroid size to affect visual size
      // Use mass/density for future enhancements
      // Use user input for initial launch position
      const startLon = isFiniteNumber(impact_location.launch_longitude)
        ? impact_location.launch_longitude
        : (impact_location.longitude - 5);
      const startLat = isFiniteNumber(impact_location.launch_latitude)
        ? impact_location.launch_latitude
        : (impact_location.latitude - 5);
      const startAlt = isFiniteNumber(impact_location.launch_altitude)
        ? impact_location.launch_altitude
        : DEFAULT_LOCATION.launch_altitude;
      const endLon = impact_location.longitude;
      const endLat = impact_location.latitude;
      const endAlt = impact_location.elevation;
      // Calculate straight-line distance (meters)
      const horizontalDistance = Math.sqrt(Math.pow(endLon - startLon, 2) + Math.pow(endLat - startLat, 2)) * 111000;
      const verticalDistance = Math.abs(startAlt - endAlt);
      const totalDistance = Math.sqrt(Math.pow(horizontalDistance, 2) + Math.pow(verticalDistance, 2));
      // Animation duration: time = distance / speed
      const durationSeconds = Math.max(1, totalDistance / Math.max(asteroid_properties.speed, 1));
      const now = new Date();
      const startTimeIso = new Date(now.getTime()).toISOString();
      const stopTimeIso = new Date(now.getTime() + durationSeconds * 1000).toISOString();
      const trajectory = [
        { lon: startLon, lat: startLat, alt: startAlt, time: startTimeIso },
        { lon: (startLon + endLon) / 2, lat: (startLat + endLat) / 2, alt: startAlt / 2, time: new Date(now.getTime() + durationSeconds * 500).toISOString() },
        { lon: endLon, lat: endLat, alt: endAlt, time: stopTimeIso }
      ];
      const property = new Cesium.SampledPositionProperty();
      trajectory.forEach(point => {
        const time = Cesium.JulianDate.fromIso8601(point.time);
        const position = Cesium.Cartesian3.fromDegrees(point.lon, point.lat, point.alt);
        property.addSample(time, position);
      });
      const start = Cesium.JulianDate.fromIso8601(trajectory[0].time);
      const stop = Cesium.JulianDate.fromIso8601(trajectory[trajectory.length - 1].time);
      viewer.clock.startTime = start.clone();
      viewer.clock.stopTime = stop.clone();
      viewer.clock.currentTime = start.clone();
      viewer.clock.clockRange = Cesium.ClockRange.CLAMPED;
      // Clock multiplier: higher speed = faster animation
      viewer.clock.multiplier = Math.max(1, asteroid_properties.speed / 500);
      viewer.timeline.zoomTo(start, stop);
      asteroidEntity = viewer.entities.add({
        availability: new Cesium.TimeIntervalCollection([
          new Cesium.TimeInterval({ start, stop })
        ]),
        position: property,
        point: { pixelSize: Math.max(8, Math.min(asteroid_properties.size / 2, 48)), color: Cesium.Color.ORANGE },
        path: { show: true, leadTime: 0, trailTime: 3600 }
      });
      if (cameraMode === 'asteroid') {
        viewer.trackedEntity = asteroidEntity;
      } else {
        viewer.trackedEntity = undefined;
      }
      function onTick() {
        const asteroidPosition = asteroidEntity.position.getValue(viewer.clock.currentTime);
        if (asteroidPosition) {
          const distance = Cesium.Cartesian3.distance(asteroidPosition, impactCartesian);
          if (distance < Math.max(1000, asteroid_properties.size * 10)) {
            viewer.clock.shouldAnimate = false;
            viewer.clock.onTick.removeEventListener(onTick);
            viewer.trackedEntity = undefined;
            viewer.entities.remove(asteroidEntity);
            asteroidEntity = null;
            cameraMode = 'impact';
            document.getElementById('cameraToggleButton').textContent = 'Follow Asteroid';
            viewer.camera.flyTo({
              destination: Cesium.Cartesian3.fromDegrees(
                impact_location.longitude,
                impact_location.latitude,
                200000
              ),
              orientation: {
                heading: Cesium.Math.toRadians(0.0),
                pitch: Cesium.Math.toRadians(-90.0),
                roll: 0.0
              }
            });
            runImpactAnimation();
          }
        }
      }
      viewer.clock.onTick.addEventListener(onTick);
      viewer.clock.shouldAnimate = true;
    }

    // Impact animation sequence
    function runImpactAnimation() {
      cleanupAnimations();
      document.getElementById('toggleButton').style.display = 'none';
      const durations = {
        flash: 500,
        blast: 2000,
        debris: 2000,
        dust: 3000
      };
      const flash = viewer.entities.add({
        position: impactCartesian,
        ellipsoid: {
          radii: new Cesium.Cartesian3(1, 1, 1),
          material: Cesium.Color.WHITE
        }
      });
      {
        const debrisEntities = [];
        const debrisCount = 90;
        const debrisColors = [
          Cesium.Color.DARKGRAY,
          Cesium.Color.YELLOW.withAlpha(0.8),
          Cesium.Color.ORANGE.withAlpha(0.8),
          Cesium.Color.BURLYWOOD.withAlpha(0.8)
        ];
        for (let i = 0; i < debrisCount; i++) {
          const angle = (i / debrisCount) * Math.PI * 2;
          const speed = 700 + Math.random() * 900;
          const duration = 1000 + Math.random() * 400;
          const startTime = performance.now();
          const color = debrisColors[Math.floor(Math.random() * debrisColors.length)];
          const debris = viewer.entities.add({
            position: impactCartesian,
            point: { pixelSize: 16 + Math.random() * 16, color }
          });
          debrisEntities.push(debris);
          function animateDebris(now) {
            const elapsed = now - startTime;
            const frac = Math.min(elapsed / duration, 1);
            const dist = speed * frac;
            const lon = impact_location.longitude + Math.cos(angle) * dist / 111000;
            const lat = impact_location.latitude + Math.sin(angle) * dist / 111000;
            const alt = Math.max(0, 600 * (1 - frac));
            debris.position = Cesium.Cartesian3.fromDegrees(lon, lat, alt);
            if (frac < 1) requestAnimationFrame(animateDebris);
            else viewer.entities.remove(debris);
          }
          requestAnimationFrame(animateDebris);
        }
        const dust = viewer.entities.add({
          position: impactCartesian,
          ellipse: {
            semiMajorAxis: 600,
            semiMinorAxis: 600,
            material: new Cesium.ColorMaterialProperty(Cesium.Color.YELLOW.withAlpha(0.35)),
            height: 0
          }
        });
        let startDust = performance.now();
        function animateDust(now) {
          const elapsed = now - startDust;
          const frac = Math.min(elapsed / 1800, 1);
          const size = 600 + frac * impact_result.blast_radius * 1.2;
          dust.ellipse.semiMajorAxis = size;
          dust.ellipse.semiMinorAxis = size;
          let color;
          if (frac < 0.4) color = Cesium.Color.YELLOW.withAlpha(0.35 * (1 - frac));
          else if (frac < 0.8) color = Cesium.Color.ORANGE.withAlpha(0.25 * (1 - frac));
          else color = Cesium.Color.DARKGRAY.withAlpha(0.18 * (1 - frac));
          dust.ellipse.material = new Cesium.ColorMaterialProperty(color);
          if (frac < 1) requestAnimationFrame(animateDust);
          else viewer.entities.remove(dust);
        }
        requestAnimationFrame(animateDust);
      }
      setTimeout(() => {
        const wave = viewer.entities.add({
          position: impactCartesian,
          ellipsoid: {
            radii: new Cesium.Cartesian3(1, 1, 1),
            material: Cesium.Color.RED.withAlpha(0.3)
          }
        });
        let start = performance.now();
        function animateBlast(now) {
          const elapsed = now - start;
          const frac = Math.min(elapsed / durations.blast, 1);
          const size = impact_result.blast_radius * Math.pow(frac, 0.7);
          wave.ellipsoid.radii = new Cesium.Cartesian3(size, size, size * .2);
          wave.ellipsoid.material = Cesium.Color.RED.withAlpha(0.3 * (1 - frac));
          if (frac < 1) requestAnimationFrame(animateBlast);
          else viewer.entities.remove(wave);
        }
        requestAnimationFrame(animateBlast);
      }, durations.flash);
      setTimeout(() => {
        createDangerZones();
        state.isShowingCrater = false;
        document.getElementById('toggleButton').style.display = 'block';
        document.getElementById('toggleButton').textContent = 'Show Crater';
      }, 1800);
    }

    // Button event listeners
    document.getElementById('toggleButton').addEventListener('click', () => {
      if (state.isShowingCrater) {
        state.craterEntities.forEach(entity => viewer.entities.remove(entity));
        createDangerZones();
        document.getElementById('toggleButton').textContent = 'Show Crater';
      } else {
        state.visualizationEntities.forEach(entity => viewer.entities.remove(entity));
        createCrater();
        document.getElementById('toggleButton').textContent = 'Show Danger Zones';
      }
      state.isShowingCrater = !state.isShowingCrater;
    });
    document.getElementById('cameraToggleButton').addEventListener('click', () => {
      if (cameraMode === 'impact') {
        cameraMode = 'asteroid';
        document.getElementById('cameraToggleButton').textContent = 'Focus Impact';
        if (asteroidEntity) viewer.trackedEntity = asteroidEntity;
      } else {
        cameraMode = 'impact';
        document.getElementById('cameraToggleButton').textContent = 'Follow Asteroid';
        viewer.trackedEntity = undefined;
        viewer.camera.flyTo({
          destination: Cesium.Cartesian3.fromDegrees(
            impact_location.longitude,
            impact_location.latitude,
            200000
          ),
          orientation: {
            heading: Cesium.Math.toRadians(0.0),
            pitch: Cesium.Math.toRadians(-30.0),
          }
        });
      }
    });
    function resetSimulation() {
      console.log("resetSimulation called");
      applySimulationState();
      cleanupAnimations();
      viewer.entities.removeAll();
      state.visualizationEntities.clear();
      state.craterEntities.clear();
      state.neoEntities.clear();
      neoState.entities = [];
      state.isShowingCrater = false;
      document.getElementById('toggleButton').style.display = 'none';
      document.getElementById('toggleButton').textContent = 'Show Crater';

      if (neoState.visible && neoState.data.length) {
        renderNeoEntities();
        neoHelpers.ensureVisibility(true);
        const buttonText = neoState.data.length ? `Hide NEOs (${neoState.data.length})` : 'Hide NEOs';
        neoHelpers.setButtonState({ text: buttonText });
      }

      viewer.camera.flyTo({
        destination: Cesium.Cartesian3.fromDegrees(
          impact_location.longitude,
          impact_location.latitude,
          200000
        ),
        orientation: {
          heading: Cesium.Math.toRadians(0.0),
          pitch: Cesium.Math.toRadians(-30.0),
        },
        complete: function() {
          setTimeout(animateAsteroidAndImpact, 500);
        }
      });
    }
    window.startMeteorSimulation = () => {
      try {
        resetSimulation();
      } catch (simulationError) {
        console.error('Failed to restart Cesium simulation', simulationError);
      }
    };

    // document.getElementById('launchButton').addEventListener('click', resetSimulation);
    // Initial setup
    // resetSimulation(); // Remove this line so asteroid only launches on button click
  } catch (error) {
    console.error('Error creating Cesium viewer:', error);
    const container = document.getElementById(containerId);
    if (container) {
      container.innerHTML = '<div style="color: red; padding: 20px;">' +
        '<h1>Error Initializing Cesium</h1>' +
        '<p>There was an error while setting up the Cesium viewer. Please check the console for more details.</p>' +
        '<pre>' + error.toString() + '</pre>' +
        '</div>';
    }
  }
}

