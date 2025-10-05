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
    const DEG2RAD = Math.PI / 180;
    const TWO_PI = Math.PI * 2;
    const AU_IN_METERS = 149597870700;
    const SOLAR_GM = 1.32712440018e20; // m^3/s^2
    const SECONDS_PER_DAY = 86400;
    const EARTH_RADIUS_METERS = 6378137;
    const EARTH_OBLIQUITY = Cesium.Math.toRadians(23.439281);

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

    const clone = (value) => {
      if (typeof structuredClone === 'function') {
        try {
          return structuredClone(value);
        } catch (error) {
          console.warn('Failed to structuredClone value, falling back to JSON clone', error);
        }
      }
      if (value === null || value === undefined) {
        return value;
      }
      try {
        return JSON.parse(JSON.stringify(value));
      } catch (jsonError) {
        console.warn('Failed to JSON clone value', jsonError);
        return value;
      }
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

    const state = {
      activeAnimations: new Set(),
      visualizationEntities: new Set(),
      craterEntities: new Set(),
      neoEntities: new Set(),
      defenseEntities: new Set(),
      isShowingCrater: false
    };

    let currentSimulation = normalizeSimulationPayload(window.getImpactSettings ? window.getImpactSettings() : null);

    let latestDefensePlan = window.__latestDefensePlan || null;
    let latestDefenseOutcome = null;
    let hasFocusedOnDefensePlan = false;
    let cameraMode = 'impact';
    let asteroidEntity = null;
    let pendingDefenseAutoFollow = false;
    let defenseOverlayEnabled = Boolean(window.defenseOverlayEnabled);
    let latestImpactSelectionId = 0;

    const defenseColors = {
      lasers: Cesium.Color.fromCssColorString('#7b1fa2'),
      kinetics: Cesium.Color.fromCssColorString('#f97316'),
      craft: Cesium.Color.fromCssColorString('#0ea5e9'),
      shields: Cesium.Color.fromCssColorString('#22c55e')
    };

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

    const IMPACT_MARKER_ID = 'impact-location-marker';
    let impactMarkerEntity = viewer.entities.add({
      id: IMPACT_MARKER_ID,
      position: impactCartesian,
      point: {
        pixelSize: 18,
        color: Cesium.Color.RED,
        outlineColor: Cesium.Color.WHITE,
        outlineWidth: 2,
        heightReference: Cesium.HeightReference.CLAMP_TO_GROUND,
        disableDepthTestDistance: Number.POSITIVE_INFINITY
      },
      description: 'Selected Impact Location'
    });
    state.visualizationEntities.add(impactMarkerEntity);

    const updateImpactMarker = (position) => {
      if (!position) {
        return;
      }
      let marker = viewer.entities.getById(IMPACT_MARKER_ID);
      if (!marker) {
        marker = viewer.entities.add({
          id: IMPACT_MARKER_ID,
          position,
          point: {
            pixelSize: 18,
            color: Cesium.Color.RED,
            outlineColor: Cesium.Color.WHITE,
            outlineWidth: 2,
            heightReference: Cesium.HeightReference.CLAMP_TO_GROUND,
            disableDepthTestDistance: Number.POSITIVE_INFINITY
          },
          description: 'Selected Impact Location'
        });
      } else {
        marker.position = position;
      }
      impactMarkerEntity = marker;
      state.visualizationEntities.add(marker);
    };

    const pickGlobePosition = (clickPosition) => {
      if (!clickPosition) {
        return null;
      }
      const scene = viewer.scene;
      if (!scene) {
        return null;
      }
      let pickedPosition = null;
      try {
        pickedPosition = scene.pickPosition(clickPosition);
      } catch (error) {
        console.warn('pickPosition failed, attempting ray pick', error);
      }
      if (!Cesium.defined(pickedPosition)) {
        const ray = viewer.camera.getPickRay(clickPosition);
        if (!ray) {
          return null;
        }
        pickedPosition = scene.globe.pick(ray, scene);
      }
      return Cesium.defined(pickedPosition) ? pickedPosition : null;
    };

    const applyManualImpactSelection = async (cartographic) => {
      if (!cartographic) {
        return;
      }
      latestImpactSelectionId += 1;
      const selectionId = latestImpactSelectionId;
      const latitude = Cesium.Math.toDegrees(cartographic.latitude);
      const longitude = Cesium.Math.toDegrees(cartographic.longitude);
      const elevation = cartographic.height ?? 0;

      if (!Number.isFinite(latitude) || !Number.isFinite(longitude) || !Number.isFinite(elevation)) {
        return;
      }

      let populationDensity = 0;

      impact_location = {
        ...impact_location,
        latitude,
        longitude,
        elevation,
        population_density: populationDensity
      };

      impactCartesian = Cesium.Cartesian3.fromDegrees(longitude, latitude, elevation);
      updateImpactMarker(impactCartesian);

      const latitudeInput = document.getElementById('latitude');
      if (latitudeInput) {
        latitudeInput.value = latitude.toFixed(6);
      }
      const longitudeInput = document.getElementById('longitude');
      if (longitudeInput) {
        longitudeInput.value = longitude.toFixed(6);
      }
      const elevationInput = document.getElementById('elevation');
      if (elevationInput) {
        elevationInput.value = elevation.toFixed(2);
      }
      const populationDensityInput = document.getElementById('population_density');
      if (populationDensityInput) {
        populationDensityInput.value = '';
      }
      try {
        if (window?.meteorMadnessAPI?.getPopulationDensity) {
          const fetchedDensity = await window.meteorMadnessAPI.getPopulationDensity(latitude, longitude);
          if (typeof fetchedDensity === 'number' && Number.isFinite(fetchedDensity)) {
            populationDensity = fetchedDensity;
          }
        }
      } catch (error) {
        console.warn('Failed to fetch population density for selected impact location', error);
      }
       if (selectionId !== latestImpactSelectionId) {
        return;
      }


      impact_location = {
        ...impact_location,
        population_density: populationDensity
      };

      if (populationDensityInput) {
        populationDensityInput.value = String(Math.round(populationDensity * 100) / 100);
      }


      const updatedSimulation = {
        ...currentSimulation,
        location: {
          ...currentSimulation.location,
          latitude,
          longitude,
          elevation,
          population_density: populationDensity
        }
      };

      currentSimulation = updatedSimulation;

      window.dispatchEvent(new CustomEvent('impactSettingsChanged', {
        detail: clone(updatedSimulation)
      }));
    };

    const screenSpaceHandler = viewer.screenSpaceEventHandler
      || new Cesium.ScreenSpaceEventHandler(viewer.scene.canvas);

    screenSpaceHandler.setInputAction((movement) => {
      if (defenseOverlayEnabled) {
        return;
      }
      const cartesian = pickGlobePosition(movement?.position);
      if (!cartesian) {
        return;
      }
      const cartographic = Cesium.Ellipsoid.WGS84.cartesianToCartographic(cartesian);
      if (!cartographic) {
        return;
      }
      applyManualImpactSelection(cartographic);
    }, Cesium.ScreenSpaceEventType.LEFT_CLICK);

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

    window.addEventListener('advancedImpactCalculated', (event) => {
      const detail = event?.detail;
      if (detail?.settingsDispatched) {
        return;
      }
      if (detail?.simulation) {
        applySimulationState(detail.simulation);
      } else {
        applySimulationState(window.getImpactSettings ? window.getImpactSettings() : null);
      }
      createDangerZones();
    });

    window.addEventListener('defenseOverlayPreferenceChanged', (event) => {
      defenseOverlayEnabled = Boolean(event?.detail?.enabled);
      if (!defenseOverlayEnabled) {
        clearDefenseEntities();
        hasFocusedOnDefensePlan = false;
        pendingDefenseAutoFollow = false;
        return;
      }
      if (latestDefensePlan && Array.isArray(latestDefensePlan.loadout) && latestDefensePlan.loadout.length) {
        renderDefensePlan(latestDefensePlan, { flyTo: false });
      }
    });

    window.addEventListener('defenseStrategyUpdated', (event) => {
      const detail = event?.detail ?? {};
      const plan = detail?.plan ?? detail ?? null;
      if (!plan || !Array.isArray(plan.loadout) || plan.loadout.length === 0) {
        latestDefensePlan = null;
        clearDefenseEntities();
        hasFocusedOnDefensePlan = false;
        pendingDefenseAutoFollow = false;
        return;
      }

      latestDefensePlan = plan;

      const meta = detail.meta ?? {};
      const metaSource = meta.source ?? detail.source ?? null;
      const autoFollowSources = ['storage', 'bootstrap', 'defense-planner'];
      const shouldAutoFollow = meta.autoFollow === true
        || (metaSource ? autoFollowSources.includes(metaSource) : false);
      const shouldFlyTo = shouldAutoFollow || meta.flyTo === true;
      const forceVisualization = meta.forceVisualization === true;
      const shouldRenderDefense = (defenseOverlayEnabled || forceVisualization)
        && Array.isArray(plan.loadout)
        && plan.loadout.length > 0;

      if (!shouldRenderDefense) {
        clearDefenseEntities();
        hasFocusedOnDefensePlan = false;
        pendingDefenseAutoFollow = false;
        return;
      }

      renderDefensePlan(plan, { flyTo: shouldFlyTo });

      if (shouldAutoFollow || forceVisualization) {
        pendingDefenseAutoFollow = true;
      }

      if (pendingDefenseAutoFollow) {
        pendingDefenseAutoFollow = false;
        cameraMode = 'asteroid';
        const cameraToggleButton = document.getElementById('cameraToggleButton');
        if (cameraToggleButton) {
          cameraToggleButton.textContent = 'Focus Impact';
        }
        try {
          resetSimulation({
            forceDefenseVisualization: forceVisualization && !defenseOverlayEnabled
          });
        } catch (error) {
          console.warn('Failed to auto-launch defense visualization', error);
        }
      }
    });

    const neoToggleButton = document.getElementById('neoToggleButton');
    const neoListContainer = document.getElementById('neoListContainer');
    const neoList = document.getElementById('neoList');

    const clamp = (value, min, max) => Math.min(Math.max(value, min), max);

    const normalizeAngle = (angle) => {
      if (!Number.isFinite(angle)) {
        return 0;
      }
      const wrapped = angle % TWO_PI;
      return wrapped < 0 ? wrapped + TWO_PI : wrapped;
    };

    const toJulianDay = (date) => {
      const julian = Cesium.JulianDate.fromDate(date);
      return julian.dayNumber + julian.secondsOfDay / SECONDS_PER_DAY;
    };

    const solveKepler = (meanAnomaly, eccentricity) => {
      if (!Number.isFinite(meanAnomaly) || !Number.isFinite(eccentricity)) {
        return null;
      }
      let eccentricAnomaly = eccentricity < 0.8 ? meanAnomaly : Math.PI;
      for (let i = 0; i < 15; i++) {
        const delta = (eccentricAnomaly - eccentricity * Math.sin(eccentricAnomaly) - meanAnomaly)
          / (1 - eccentricity * Math.cos(eccentricAnomaly));
        eccentricAnomaly -= delta;
        if (Math.abs(delta) < 1e-10) {
          break;
        }
      }
      return eccentricAnomaly;
    };

    const eclipticToEquatorial = ({ x, y, z }) => {
      const cosObliquity = Math.cos(EARTH_OBLIQUITY);
      const sinObliquity = Math.sin(EARTH_OBLIQUITY);
      return {
        x,
        y: y * cosObliquity - z * sinObliquity,
        z: y * sinObliquity + z * cosObliquity
      };
    };

    const computeGmst = (date) => {
      const jd = toJulianDay(date);
      const T = (jd - 2451545.0) / 36525;
      let gmst = 280.46061837 + 360.98564736629 * (jd - 2451545.0)
        + 0.000387933 * T * T - (T * T * T) / 38710000;
      gmst = ((gmst % 360) + 360) % 360;
      return gmst * DEG2RAD;
    };

    const eciToEcef = (vector, date) => {
      if (!vector) {
        return null;
      }
      const theta = computeGmst(date);
      const cosTheta = Math.cos(theta);
      const sinTheta = Math.sin(theta);
      return {
        x: vector.x * cosTheta + vector.y * sinTheta,
        y: -vector.x * sinTheta + vector.y * cosTheta,
        z: vector.z
      };
    };

    const ensureSafeAltitude = (vector) => {
      if (!vector) {
        return null;
      }
      const { x, y, z } = vector;
      const distance = Math.sqrt(x * x + y * y + z * z);
      if (!Number.isFinite(distance) || distance === 0) {
        return null;
      }
      const minimumDistance = EARTH_RADIUS_METERS + 150000;
      if (distance < minimumDistance) {
        const scale = minimumDistance / distance;
        return {
          x: x * scale,
          y: y * scale,
          z: z * scale
        };
      }
      return vector;
    };

    const computeEarthEquatorialPosition = (date) => {
      const jd = toJulianDay(date);
      const T = (jd - 2451545.0) / 36525;
      const meanLongitude = normalizeAngle((100.46457166 + 35999.37244981 * T) * DEG2RAD);
      const longitudeOfPerihelion = normalizeAngle((102.93768193 + 0.32327364 * T) * DEG2RAD);
      const meanAnomaly = normalizeAngle(meanLongitude - longitudeOfPerihelion);
      const eccentricity = clamp(0.016708634 - 0.000042037 * T - 0.0000001267 * T * T, 0, 0.2);
      const eccentricAnomaly = solveKepler(meanAnomaly, eccentricity);
      if (!Number.isFinite(eccentricAnomaly)) {
        return null;
      }
      const cosE = Math.cos(eccentricAnomaly);
      const sinE = Math.sin(eccentricAnomaly);
      const sqrtOneMinusESq = Math.sqrt(Math.max(0, 1 - eccentricity * eccentricity));
      const xv = cosE - eccentricity;
      const yv = sqrtOneMinusESq * sinE;
      const trueAnomaly = Math.atan2(yv, xv);
      const radiusAu = Math.sqrt(xv * xv + yv * yv);
      const heliocentricLongitude = trueAnomaly + longitudeOfPerihelion;
      const xEcliptic = radiusAu * Math.cos(heliocentricLongitude) * AU_IN_METERS;
      const yEcliptic = radiusAu * Math.sin(heliocentricLongitude) * AU_IN_METERS;
      const zEcliptic = 0;
      return eclipticToEquatorial({ x: xEcliptic, y: yEcliptic, z: zEcliptic });
    };

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
      computeFallbackPlacement(neo, index) {
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
      createFallbackPositionProperty(placement) {
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
      },
      extractOrbitElements(neo) {
        const orbit = neo?.orbital_data;
        if (!orbit) {
          return null;
        }
        const semiMajorAxisAu = Number(orbit.semi_major_axis);
        const eccentricity = Number(orbit.eccentricity);
        const inclination = Number(orbit.inclination);
        const ascendingNode = Number(orbit.ascending_node_longitude);
        const argumentOfPeriapsis = Number(orbit.perihelion_argument);
        const meanAnomaly = Number(orbit.mean_anomaly);
        let meanMotion = Number(orbit.mean_motion);
        const epochJulian = Number(orbit.epoch_osculation);
        if (!Number.isFinite(semiMajorAxisAu)
          || !Number.isFinite(eccentricity)
          || !Number.isFinite(inclination)
          || !Number.isFinite(ascendingNode)
          || !Number.isFinite(argumentOfPeriapsis)
          || !Number.isFinite(meanAnomaly)
          || !Number.isFinite(epochJulian)) {
          return null;
        }
        const semiMajorAxisMeters = semiMajorAxisAu * AU_IN_METERS;
        const eccentricityClamped = clamp(eccentricity, 0, 0.99);
        let meanMotionRadPerDay;
        if (Number.isFinite(meanMotion)) {
          meanMotionRadPerDay = meanMotion * DEG2RAD;
        } else {
          meanMotionRadPerDay = Math.sqrt(SOLAR_GM / Math.pow(semiMajorAxisMeters, 3)) * SECONDS_PER_DAY;
        }
        if (!Number.isFinite(meanMotionRadPerDay)) {
          return null;
        }
        return {
          semiMajorAxisMeters,
          eccentricity: eccentricityClamped,
          inclinationRad: inclination * DEG2RAD,
          ascendingNodeRad: ascendingNode * DEG2RAD,
          argumentOfPeriapsisRad: argumentOfPeriapsis * DEG2RAD,
          meanAnomalyRad: normalizeAngle(meanAnomaly * DEG2RAD),
          meanMotionRadPerDay,
          epochJulian
        };
      },
      computeNeoEcefPosition(orbit, date) {
        if (!orbit) {
          return null;
        }
        const earthEquatorial = computeEarthEquatorialPosition(date);
        if (!earthEquatorial) {
          return null;
        }
        const julianDay = toJulianDay(date);
        if (!Number.isFinite(julianDay)) {
          return null;
        }
        const deltaDays = julianDay - orbit.epochJulian;
        if (!Number.isFinite(deltaDays)) {
          return null;
        }
        const meanAnomaly = normalizeAngle(orbit.meanAnomalyRad + orbit.meanMotionRadPerDay * deltaDays);
        const eccentricAnomaly = solveKepler(meanAnomaly, orbit.eccentricity);
        if (!Number.isFinite(eccentricAnomaly)) {
          return null;
        }
        const cosE = Math.cos(eccentricAnomaly);
        const sinE = Math.sin(eccentricAnomaly);
        const sqrtOneMinusESq = Math.sqrt(Math.max(0, 1 - orbit.eccentricity * orbit.eccentricity));
        const radius = orbit.semiMajorAxisMeters * (1 - orbit.eccentricity * cosE);
        const trueAnomaly = Math.atan2(sqrtOneMinusESq * sinE, cosE - orbit.eccentricity);
        const cosOmega = Math.cos(orbit.ascendingNodeRad);
        const sinOmega = Math.sin(orbit.ascendingNodeRad);
        const cosI = Math.cos(orbit.inclinationRad);
        const sinI = Math.sin(orbit.inclinationRad);
        const argPlusTrue = orbit.argumentOfPeriapsisRad + trueAnomaly;
        const cosArg = Math.cos(argPlusTrue);
        const sinArg = Math.sin(argPlusTrue);
        const xEcliptic = radius * (cosOmega * cosArg - sinOmega * sinArg * cosI);
        const yEcliptic = radius * (sinOmega * cosArg + cosOmega * sinArg * cosI);
        const zEcliptic = radius * (sinI * sinArg);
        const asteroidEquatorial = eclipticToEquatorial({ x: xEcliptic, y: yEcliptic, z: zEcliptic });
        const relativeEci = {
          x: asteroidEquatorial.x - earthEquatorial.x,
          y: asteroidEquatorial.y - earthEquatorial.y,
          z: asteroidEquatorial.z - earthEquatorial.z
        };
        const ecef = eciToEcef(relativeEci, date);
        return ensureSafeAltitude(ecef);
      },
      createLabelTextProperty(neo) {
        if (!neo.orbit) {
          return neo.name;
        }
        return new Cesium.CallbackProperty((time) => {
          const nowDate = Cesium.JulianDate.toDate(time);
          const ecef = neoHelpers.computeNeoEcefPosition(neo.orbit, nowDate);
          if (!ecef) {
            return neo.name;
          }
          const distanceMeters = Math.sqrt(ecef.x * ecef.x + ecef.y * ecef.y + ecef.z * ecef.z);
          if (!Number.isFinite(distanceMeters)) {
            return neo.name;
          }
          const distanceKm = Math.max(distanceMeters / 1000, 0);
          const formatted = distanceKm.toLocaleString(undefined, { maximumFractionDigits: 0 });
          return `${neo.name} (${formatted} km)`;
        }, false);
      },
      createPositionProperty(neo, fallbackPlacement, fallbackProperty) {
        const fallback = fallbackProperty || neoHelpers.createFallbackPositionProperty(fallbackPlacement);
        if (!neo.orbit) {
          return fallback;
        }
        return new Cesium.CallbackProperty((time, result) => {
          const nowDate = Cesium.JulianDate.toDate(time);
          const ecef = neoHelpers.computeNeoEcefPosition(neo.orbit, nowDate);
          if (!ecef) {
            return fallback.getValue(time, result);
          }
          if (!result) {
            return new Cesium.Cartesian3(ecef.x, ecef.y, ecef.z);
          }
          result.x = ecef.x;
          result.y = ecef.y;
          result.z = ecef.z;
          return result;
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
          let estimatedDiameterKm = null;
          const diameterRange = neo.estimated_diameter?.kilometers;
          if (diameterRange) {
            const min = Number(diameterRange.estimated_diameter_min);
            const max = Number(diameterRange.estimated_diameter_max);
            if (Number.isFinite(min) && Number.isFinite(max)) {
              estimatedDiameterKm = (min + max) / 2;
            }
          }
          results.push({
            id: neo.id,
            name: neo.name,
            approachDate,
            missDistanceKm,
            relativeVelocityKps,
            magnitude: Number(neo.absolute_magnitude_h),
            isPotentiallyHazardous: Boolean(neo.is_potentially_hazardous_asteroid),
            orbit: neoHelpers.extractOrbitElements(neo),
            estimatedDiameterKm
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
        const fallbackPlacement = neoHelpers.computeFallbackPlacement(neo, i);
        const fallbackPosition = neoHelpers.createFallbackPositionProperty(fallbackPlacement);
        const position = neoHelpers.createPositionProperty(neo, fallbackPlacement, fallbackPosition);
        const currentDistanceKm = (() => {
          if (!neo.orbit) {
            return null;
          }
          const now = new Date();
          const ecef = neoHelpers.computeNeoEcefPosition(neo.orbit, now);
          if (!ecef) {
            return null;
          }
          const distanceMeters = Math.sqrt(ecef.x * ecef.x + ecef.y * ecef.y + ecef.z * ecef.z);
          return Number.isFinite(distanceMeters) ? distanceMeters / 1000 : null;
        })();
        const entity = viewer.entities.add({
          id: neo.id,
          position,
          point: {
            pixelSize: 12,
            color: neo.isPotentiallyHazardous ? Cesium.Color.RED : Cesium.Color.CYAN,
            outlineWidth: 2,
            outlineColor: Cesium.Color.BLACK
          },
          label: {
            text: neoHelpers.createLabelTextProperty(neo),
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
              ${Number.isFinite(neo.estimatedDiameterKm) ? `<p><strong>Estimated Diameter:</strong> ${neo.estimatedDiameterKm.toFixed(2)} km</p>` : ''}
              ${Number.isFinite(currentDistanceKm) ? `<p><strong>Current Distance:</strong> ${currentDistanceKm.toLocaleString(undefined, { maximumFractionDigits: 0 })} km</p>` : ''}
              <p><strong>Potentially Hazardous:</strong> ${neo.isPotentiallyHazardous ? 'Yes' : 'No'}</p>
              ${neo.orbit ? '<p style="font-size:12px;color:#ccc;">Position updates with NASA orbital elements in real time.</p>' : ''}
            </div>
          `
        });
        entity.show = neoState.visible;
        state.neoEntities.add(entity);
        neoState.entities.push(entity);
      }
    }

    function renderNeoList(neos) {
      neoList.innerHTML = '';
      if (!neos || !neos.length) {
        neoListContainer.style.display = 'none';
        return;
      }

      const fragment = document.createDocumentFragment();
      neos.forEach(neo => {
        const li = document.createElement('li');
        li.textContent = `${neo.name} (${neo.missDistanceKm.toFixed(0)} km)`;
        li.style.padding = '8px';
        li.style.cursor = 'pointer';
        li.dataset.neoId = neo.id;
        li.addEventListener('mouseenter', () => li.style.backgroundColor = '#f0f0f0');
        li.addEventListener('mouseleave', () => li.style.backgroundColor = 'transparent');
        fragment.appendChild(li);
      });
      neoList.appendChild(fragment);
      neoListContainer.style.display = 'block';
    }

    function populateAsteroidDropdown(neos) {
      const dropdown = document.getElementById('asteroid-focus');
      dropdown.innerHTML = '<option value="earth">Earth</option>'; // Reset and add Earth option
      if (!neos || !neos.length) {
        return;
      }
      neos.forEach(neo => {
        const option = document.createElement('option');
        option.value = neo.id;
        option.textContent = neo.name;
        dropdown.appendChild(option);
      });
    }

    document.getElementById('asteroid-focus').addEventListener('change', (event) => {
      const selectedId = event.target.value;
      if (selectedId === 'earth') {
        viewer.trackedEntity = undefined;
        viewer.camera.flyHome(0);
      } else {
        const selectedEntity = neoState.entities.find(entity => {
          console.log(`Comparing entity.id: ${entity.id} with selectedId: ${selectedId}`);
          return entity.id === selectedId;
        });
        if (selectedEntity) {
          viewer.zoomTo(selectedEntity);
          viewer.trackedEntity = selectedEntity;
        }
      }
    });

    neoList.addEventListener('click', (event) => {
      if (event.target.tagName === 'LI') {
        const neoId = event.target.dataset.neoId;
        const selectedNeo = neoState.data.find(neo => neo.id === neoId);
        if (selectedNeo) {
          document.getElementById('asteroid_size').value = (selectedNeo.estimatedDiameterKm * 1000).toFixed(0);
          document.getElementById('asteroid_speed').value = (selectedNeo.relativeVelocityKps * 1000).toFixed(0);
          // Close the list after selection
          neoListContainer.style.display = 'none';
        }
      }
    });

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
        neoListContainer.style.display = 'none';
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
          populateAsteroidDropdown(neoState.data);
          neoState.fetchedAt = Date.now();
        }
        renderNeoEntities();
        renderNeoList(neoState.data);
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
          !state.defenseEntities.has(entity) &&
          entity !== asteroidEntity
        ) {
          viewer.entities.remove(entity);
        }
      });
    }

    function clearDefenseEntities() {
      state.defenseEntities.forEach(entity => viewer.entities.remove(entity));
      state.defenseEntities.clear();
      latestDefenseOutcome = null;
      pendingDefenseAutoFollow = false;
    }

    function renderDefensePlan(plan, { flyTo = false } = {}) {
      clearDefenseEntities();

      if (!plan || !Array.isArray(plan.loadout) || plan.loadout.length === 0) {
        if (!plan) {
          latestDefensePlan = null;
        }
        latestDefenseOutcome = null;
        hasFocusedOnDefensePlan = false;
        return;
      }

      latestDefensePlan = plan;
      latestDefenseOutcome = plan.engagement || null;

      const locationSource = plan.level?.impactLocation || plan.level?.location || plan.level || {};
      const baseLat = toNumber(locationSource.latitude, impact_location.latitude);
      const baseLon = toNumber(locationSource.longitude, impact_location.longitude);
      const baseElevation = toNumber(locationSource.elevation, impact_location.elevation);

      impact_location.latitude = baseLat;
      impact_location.longitude = baseLon;
      impact_location.elevation = baseElevation;
      impactCartesian = Cesium.Cartesian3.fromDegrees(baseLon, baseLat, Math.max(baseElevation, 0));
      updateImpactMarker(impactCartesian);
      currentSimulation = {
        ...currentSimulation,
        location: {
          ...currentSimulation.location,
          latitude: baseLat,
          longitude: baseLon,
          elevation: baseElevation
        }
      };
      const engagement = plan.engagement || {};

      if (engagement.approachPoint) {
        impact_location.launch_longitude = toNumber(engagement.approachPoint.longitude, impact_location.launch_longitude);
        impact_location.launch_latitude = toNumber(engagement.approachPoint.latitude, impact_location.launch_latitude);
        impact_location.launch_altitude = toNumber(engagement.approachPoint.altitude, impact_location.launch_altitude);
      }

      if (engagement.interceptPoint) {
        impact_location.intercept_longitude = toNumber(engagement.interceptPoint.longitude, impact_location.longitude);
        impact_location.intercept_latitude = toNumber(engagement.interceptPoint.latitude, impact_location.latitude);
        impact_location.intercept_altitude = toNumber(engagement.interceptPoint.altitude, impact_location.launch_altitude);
      } else {
        delete impact_location.intercept_longitude;
        delete impact_location.intercept_latitude;
        delete impact_location.intercept_altitude;
      }

      const anchorPosition = Cesium.Cartesian3.fromDegrees(baseLon, baseLat, Math.max(baseElevation + 1000, 1000));
      const accuracySuffix = Number.isFinite(engagement.accuracy) ? ` (${Math.round(engagement.accuracy)}% accuracy)` : '';
      const anchorLabel = plan.level?.name
        ? `${plan.level.name} Defense${accuracySuffix}`
        : `Defense Target${accuracySuffix}`;
      const anchorDescription = engagement?.summary
        || (engagement && Number.isFinite(engagement.accuracy)
          ? (engagement.success
            ? `Intercept corridor secured with ${Math.round(engagement.accuracy)}% projected accuracy.`
            : `Defense response staged · Accuracy ${Math.round(engagement.accuracy)}%.`)
          : (plan.level?.name
            ? `Coordinated defense response for ${plan.level.name}.`
            : 'Coordinated defense response.'));

      const anchor = viewer.entities.add({
        position: anchorPosition,
        point: {
          pixelSize: 12,
          color: Cesium.Color.CYAN.withAlpha(0.85),
          outlineColor: Cesium.Color.WHITE,
          outlineWidth: 1.5
        },
        label: {
          text: anchorLabel,
          font: '15px "Roboto", sans-serif',
          fillColor: Cesium.Color.CYAN,
          outlineColor: Cesium.Color.BLACK,
          outlineWidth: 2,
          style: Cesium.LabelStyle.FILL_AND_OUTLINE,
          verticalOrigin: Cesium.VerticalOrigin.BOTTOM,
          pixelOffset: new Cesium.Cartesian2(0, -16),
          translucencyByDistance: new Cesium.NearFarScalar(75000, 0.0, 2500000, 1.0),
          disableDepthTestDistance: Number.POSITIVE_INFINITY
        },
        description: anchorDescription
      });
      state.defenseEntities.add(anchor);

      const lonScale = Math.max(Math.cos(Cesium.Math.toRadians(baseLat)), 0.3);
      const baseRadiusKm = Math.max(plan.totals?.power ?? 0, 1) * 1.6;
      let referenceLaunch = null;
      const assetPositions = [];

      plan.loadout.forEach((item, index) => {
        const angle = (index / plan.loadout.length) * TWO_PI;
        const ringKm = baseRadiusKm + (index % 4) * 45;
        const latOffset = (ringKm / 110.574) * Math.sin(angle);
        const lonOffset = (ringKm / (111.32 * lonScale)) * Math.cos(angle);
        const assetLat = clamp(baseLat + latOffset, -85, 85);
        const assetLon = baseLon + lonOffset;
        const altitude = item.categoryId === 'lasers'
          ? 750000
          : item.categoryId === 'kinetics'
            ? 460000
            : item.categoryId === 'craft'
              ? 320000
              : item.categoryId === 'shields'
                ? 160000
                : 220000;
        const position = Cesium.Cartesian3.fromDegrees(assetLon, assetLat, altitude);
        const color = (item.categoryId && defenseColors[item.categoryId]) || Cesium.Color.SKYBLUE;

        const defenseNode = viewer.entities.add({
          position,
          point: {
            pixelSize: 14,
            color: color.withAlpha(0.95),
            outlineColor: Cesium.Color.WHITE,
            outlineWidth: 1.5
          },
          label: {
            text: item.name || item.id,
            font: '13px "Roboto", sans-serif',
            fillColor: color,
            outlineColor: Cesium.Color.BLACK,
            outlineWidth: 2,
            style: Cesium.LabelStyle.FILL_AND_OUTLINE,
            verticalOrigin: Cesium.VerticalOrigin.BOTTOM,
            pixelOffset: new Cesium.Cartesian2(0, -18),
            translucencyByDistance: new Cesium.NearFarScalar(150000, 0.0, 3000000, 1.0),
            disableDepthTestDistance: Number.POSITIVE_INFINITY
          },
          description: `Category: ${item.categoryName || item.categoryId || 'Unknown'}<br>`
            + `Power: ${item.power ?? '—'}`
        });
        state.defenseEntities.add(defenseNode);

        const connection = viewer.entities.add({
          polyline: {
            positions: [position, anchorPosition],
            width: 2.2,
            material: new Cesium.ColorMaterialProperty(color.withAlpha(0.6))
          }
        });
        state.defenseEntities.add(connection);

        assetPositions.push({ position, color });

        if (!referenceLaunch) {
          referenceLaunch = { lon: assetLon, lat: assetLat, alt: altitude };
        }
      });

      if (referenceLaunch) {
        impact_location.launch_longitude = referenceLaunch.lon;
        impact_location.launch_latitude = referenceLaunch.lat;
        impact_location.launch_altitude = referenceLaunch.alt;
      }

      const interceptPoint = engagement?.interceptPoint;
      let interceptPosition = null;
      if (interceptPoint && Number.isFinite(interceptPoint.longitude) && Number.isFinite(interceptPoint.latitude)) {
        interceptPosition = Cesium.Cartesian3.fromDegrees(
          interceptPoint.longitude,
          interceptPoint.latitude,
          Math.max(toNumber(interceptPoint.altitude, 0), 50000)
        );
        const successColor = engagement?.success ? Cesium.Color.LIME : Cesium.Color.CRIMSON;
        const interceptLabel = engagement?.success ? 'Intercept Window' : 'Missed Intercept';
        const interceptNode = viewer.entities.add({
          position: interceptPosition,
          point: {
            pixelSize: 16,
            color: successColor.withAlpha(0.92),
            outlineColor: Cesium.Color.WHITE,
            outlineWidth: 2
          },
          label: {
            text: interceptLabel,
            font: '14px "Roboto", sans-serif',
            fillColor: successColor,
            outlineColor: Cesium.Color.BLACK,
            outlineWidth: 1.5,
            style: Cesium.LabelStyle.FILL_AND_OUTLINE,
            pixelOffset: new Cesium.Cartesian2(0, -18),
            translucencyByDistance: new Cesium.NearFarScalar(200000, 0.0, 4500000, 1.0),
            disableDepthTestDistance: Number.POSITIVE_INFINITY
          }
        });
        state.defenseEntities.add(interceptNode);

        assetPositions.forEach(({ position, color }) => {
          const interceptConnector = viewer.entities.add({
            polyline: {
              positions: [position, interceptPosition],
              width: 2.6,
              material: new Cesium.PolylineArrowMaterialProperty(
                (engagement?.success ? color : Cesium.Color.CRIMSON).withAlpha(0.65)
              )
            }
          });
          state.defenseEntities.add(interceptConnector);
        });

        if (engagement?.success && engagement.deflectionPoint) {
          const deflectionCartesian = Cesium.Cartesian3.fromDegrees(
            engagement.deflectionPoint.longitude,
            engagement.deflectionPoint.latitude,
            Math.max(toNumber(engagement.deflectionPoint.altitude, 0), 80000)
          );
          const deflectionTrail = viewer.entities.add({
            polyline: {
              positions: [interceptPosition, deflectionCartesian],
              width: 3.2,
              material: new Cesium.PolylineGlowMaterialProperty({
                glowPower: 0.25,
                taperPower: 0.4,
                color: Cesium.Color.LIME.withAlpha(0.8)
              })
            }
          });
          state.defenseEntities.add(deflectionTrail);
          const deflectedMarker = viewer.entities.add({
            position: deflectionCartesian,
            point: {
              pixelSize: 10,
              color: Cesium.Color.AQUA.withAlpha(0.9),
              outlineColor: Cesium.Color.WHITE,
              outlineWidth: 1.2
            },
            label: {
              text: 'Asteroid Deflected',
              font: '13px "Roboto", sans-serif',
              fillColor: Cesium.Color.AQUA,
              outlineColor: Cesium.Color.BLACK,
              outlineWidth: 1,
              pixelOffset: new Cesium.Cartesian2(0, -14),
              disableDepthTestDistance: Number.POSITIVE_INFINITY
            }
          });
          state.defenseEntities.add(deflectedMarker);
        } else if (!engagement?.success && engagement?.missPoint) {
          const missCartesian = Cesium.Cartesian3.fromDegrees(
            engagement.missPoint.longitude,
            engagement.missPoint.latitude,
            Math.max(toNumber(engagement.missPoint.altitude, 0), 30000)
          );
          const missPath = viewer.entities.add({
            polyline: {
              positions: [interceptPosition, missCartesian, anchorPosition],
              width: 3.4,
              material: new Cesium.PolylineGlowMaterialProperty({
                color: Cesium.Color.RED.withAlpha(0.75),
                glowPower: 0.2
              })
            }
          });
          state.defenseEntities.add(missPath);
        }
      }

      if (!hasFocusedOnDefensePlan || flyTo) {
        viewer.flyTo(Array.from(state.defenseEntities), {
          duration: 2.6,
          offset: new Cesium.HeadingPitchRange(
            0,
            Cesium.Math.toRadians(-35),
            1200000
          )
        }).catch((error) => {
          console.warn('Failed to focus defense plan', error);
        });
        hasFocusedOnDefensePlan = true;
      }
    }
    // Danger zones visualization
    function createDangerZones() {
      console.log("createDangerZones called");
       const preservedEntities = [];
      state.visualizationEntities.forEach((entity) => {
        if (!entity) {
          return;
        }
        if (entity.id === IMPACT_MARKER_ID) {
          preservedEntities.push(entity);
          return;
        }
        viewer.entities.remove(entity);
      });
      state.visualizationEntities.clear();
       impactMarkerEntity = viewer.entities.getById(IMPACT_MARKER_ID) || impactMarkerEntity;
      if (impactMarkerEntity) {
        impactMarkerEntity.position = impactCartesian;
        state.visualizationEntities.add(impactMarkerEntity);
      } else {
        updateImpactMarker(impactCartesian);
      }
      const rings = [
        { radius: impact_result.blast_radius, color: Cesium.Color.RED.withAlpha(0.3), name: 'Blast Radius' },
        { radius: impact_result.thermal_radius, color: Cesium.Color.ORANGE.withAlpha(0.2), name: 'Thermal Radius' },
        { radius: impact_result.fireball_radius, color: Cesium.Color.YELLOW.withAlpha(0.2), name: 'Fireball Radius' },
        { radius: impact_result.evacuation_radius, color: Cesium.Color.BLUE.withAlpha(0.1), name: 'Evacuation Radius' }
      ];
     preservedEntities.forEach((entity) => {
        if (entity && entity.id === IMPACT_MARKER_ID) {
          state.visualizationEntities.add(entity);
        }
      });
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

    if (latestDefensePlan && state.defenseEntities.size === 0) {
      renderDefensePlan(latestDefensePlan, { flyTo: true });
    }

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
    function animateAsteroidAndImpact() {
      // Use asteroid speed to affect animation duration and clock multiplier
      // Use asteroid size to affect visual size
      // Use mass/density for future enhancements
      // Use user input for initial launch position
      const engagement = latestDefenseOutcome || {};
      const approach = engagement.approachPoint || null;
      const interceptTarget = (engagement && engagement.success && engagement.interceptPoint)
        ? engagement.interceptPoint
        : null;

      const startLon = approach && isFiniteNumber(approach.longitude)
        ? approach.longitude
        : (isFiniteNumber(impact_location.launch_longitude)
          ? impact_location.launch_longitude
          : (impact_location.longitude - 5));
      const startLat = approach && isFiniteNumber(approach.latitude)
        ? approach.latitude
        : (isFiniteNumber(impact_location.launch_latitude)
          ? impact_location.launch_latitude
          : (impact_location.latitude - 5));
      const startAlt = approach && isFiniteNumber(approach.altitude)
        ? approach.altitude
        : (isFiniteNumber(impact_location.launch_altitude)
          ? impact_location.launch_altitude
          : DEFAULT_LOCATION.launch_altitude);

      const endLon = interceptTarget && isFiniteNumber(interceptTarget.longitude)
        ? interceptTarget.longitude
        : impact_location.longitude;
      const endLat = interceptTarget && isFiniteNumber(interceptTarget.latitude)
        ? interceptTarget.latitude
        : impact_location.latitude;
      const endAlt = interceptTarget && isFiniteNumber(interceptTarget.altitude)
        ? Math.max(interceptTarget.altitude, 1000)
        : impact_location.elevation;

      const targetCartesian = interceptTarget
        ? Cesium.Cartesian3.fromDegrees(endLon, endLat, endAlt)
        : impactCartesian;

      const horizontalDistance = Math.sqrt(Math.pow(endLon - startLon, 2) + Math.pow(endLat - startLat, 2)) * 111000;
      const verticalDistance = Math.abs(startAlt - endAlt);
      const totalDistance = Math.sqrt(Math.pow(horizontalDistance, 2) + Math.pow(verticalDistance, 2));
      const durationSeconds = Math.max(1, totalDistance / Math.max(asteroid_properties.speed, 1));
      const now = new Date();
      const startTimeIso = new Date(now.getTime()).toISOString();
      const stopTimeIso = new Date(now.getTime() + durationSeconds * 1000).toISOString();
      const midLon = (startLon + endLon) / 2;
      const midLat = (startLat + endLat) / 2;
      const midAlt = interceptTarget
        ? Math.max(startAlt, endAlt) * 0.7
        : startAlt / 2;
      const trajectory = [
        { lon: startLon, lat: startLat, alt: startAlt, time: startTimeIso },
        { lon: midLon, lat: midLat, alt: midAlt, time: new Date(now.getTime() + durationSeconds * 500).toISOString() },
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
          const distance = Cesium.Cartesian3.distance(asteroidPosition, targetCartesian);
          if (distance < Math.max(1500, asteroid_properties.size * 10)) {
            viewer.clock.shouldAnimate = false;
            viewer.clock.onTick.removeEventListener(onTick);
            viewer.trackedEntity = undefined;
            viewer.entities.remove(asteroidEntity);
            asteroidEntity = null;
            cameraMode = 'impact';
            document.getElementById('cameraToggleButton').textContent = 'Follow Asteroid';
            const flyDestination = interceptTarget
              ? Cesium.Cartesian3.fromDegrees(
                  endLon,
                  endLat,
                  Math.max(endAlt + 150000, 150000)
                )
              : Cesium.Cartesian3.fromDegrees(
                  impact_location.longitude,
                  impact_location.latitude,
                  200000
                );
            const flyOrientation = interceptTarget
              ? {
                  heading: Cesium.Math.toRadians(0.0),
                  pitch: Cesium.Math.toRadians(-35.0),
                  roll: 0.0
                }
              : {
                  heading: Cesium.Math.toRadians(0.0),
                  pitch: Cesium.Math.toRadians(-90.0),
                  roll: 0.0
                };
            viewer.camera.flyTo({
              destination: flyDestination,
              orientation: flyOrientation
            });
            if (interceptTarget) {
              runDefenseInterceptAnimation(engagement);
            } else {
              runImpactAnimation();
            }
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

    function runDefenseInterceptAnimation(outcome = null) {
      cleanupAnimations();
      document.getElementById('toggleButton').style.display = 'none';
      state.visualizationEntities.forEach(entity => viewer.entities.remove(entity));
      state.visualizationEntities.clear();

      if (!outcome || !outcome.success || !outcome.interceptPoint) {
        runImpactAnimation();
        return;
      }

      const interceptLon = toNumber(outcome.interceptPoint.longitude, impact_location.longitude);
      const interceptLat = toNumber(outcome.interceptPoint.latitude, impact_location.latitude);
      const interceptAlt = Math.max(toNumber(outcome.interceptPoint.altitude, 0), 50000);
      const interceptCartesian = Cesium.Cartesian3.fromDegrees(interceptLon, interceptLat, interceptAlt);
      const successColor = Cesium.Color.LIME;

      const flash = viewer.entities.add({
        position: interceptCartesian,
        ellipsoid: {
          radii: new Cesium.Cartesian3(9000, 9000, 9000),
          material: successColor.withAlpha(0.85)
        }
      });
      state.visualizationEntities.add(flash);

      const pulse = viewer.entities.add({
        position: interceptCartesian,
        ellipsoid: {
          radii: new Cesium.Cartesian3(4000, 4000, 4000),
          material: successColor.withAlpha(0.35)
        }
      });
      state.visualizationEntities.add(pulse);
      const pulseStart = performance.now();
      function animatePulse(now) {
        const elapsed = now - pulseStart;
        const frac = Math.min(elapsed / 1600, 1);
        const size = 4000 + frac * 95000;
        pulse.ellipsoid.radii = new Cesium.Cartesian3(size, size, size * 0.32);
        pulse.ellipsoid.material = successColor.withAlpha(0.35 * (1 - frac));
        if (frac < 1) {
          requestAnimationFrame(animatePulse);
        } else {
          viewer.entities.remove(pulse);
          state.visualizationEntities.delete(pulse);
        }
      }
      requestAnimationFrame(animatePulse);

      if (outcome.deflectionPoint) {
        const deflectionLon = toNumber(outcome.deflectionPoint.longitude, interceptLon + 4);
        const deflectionLat = toNumber(outcome.deflectionPoint.latitude, interceptLat + 3);
        const deflectionAlt = Math.max(toNumber(outcome.deflectionPoint.altitude, interceptAlt + 120000), 60000);
        const deflectionCartesian = Cesium.Cartesian3.fromDegrees(deflectionLon, deflectionLat, deflectionAlt);
        const deflectionTrail = viewer.entities.add({
          polyline: {
            positions: [interceptCartesian, deflectionCartesian],
            width: 3.6,
            material: new Cesium.PolylineGlowMaterialProperty({
              glowPower: 0.3,
              taperPower: 0.4,
              color: successColor.withAlpha(0.85)
            })
          }
        });
        state.visualizationEntities.add(deflectionTrail);
        const deflectedMarker = viewer.entities.add({
          position: deflectionCartesian,
          point: {
            pixelSize: 9,
            color: Cesium.Color.AQUA.withAlpha(0.95),
            outlineColor: Cesium.Color.WHITE,
            outlineWidth: 1.4
          },
          label: {
            text: 'Asteroid Diverted',
            font: '13px "Roboto", sans-serif',
            fillColor: Cesium.Color.AQUA,
            outlineColor: Cesium.Color.BLACK,
            outlineWidth: 1,
            pixelOffset: new Cesium.Cartesian2(0, -12),
            disableDepthTestDistance: Number.POSITIVE_INFINITY
          }
        });
        state.visualizationEntities.add(deflectedMarker);
      }

      const safeRadius = Math.max(toNumber(impact_result.evacuation_radius, 60000) * 0.55, 30000);
      const safetyRing = viewer.entities.add({
        position: impactCartesian,
        ellipse: {
          semiMajorAxis: safeRadius,
          semiMinorAxis: safeRadius,
          material: successColor.withAlpha(0.12),
          outline: true,
          outlineColor: successColor.withAlpha(0.45),
          height: 0
        },
        description: 'Deflection shielded population center'
      });
      state.visualizationEntities.add(safetyRing);

      const labelText = outcome?.summary
        ? outcome.summary
        : 'Trajectory Diverted — Region Safe';
      const safetyLabel = viewer.entities.add({
        position: Cesium.Cartesian3.fromDegrees(
          impact_location.longitude,
          impact_location.latitude,
          Math.max(impact_location.elevation + 1800, 1800)
        ),
        label: {
          text: labelText,
          font: '15px "Roboto", sans-serif',
          fillColor: Cesium.Color.LIME,
          outlineColor: Cesium.Color.BLACK,
          outlineWidth: 2,
          pixelOffset: new Cesium.Cartesian2(0, -18),
          disableDepthTestDistance: Number.POSITIVE_INFINITY
        }
      });
      state.visualizationEntities.add(safetyLabel);

      state.isShowingCrater = false;
    }

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
    function resetSimulation({ forceDefenseVisualization = false } = {}) {
      console.log("resetSimulation called");
      applySimulationState();
      cleanupAnimations();
      viewer.entities.removeAll();
      state.visualizationEntities.clear();
      state.craterEntities.clear();
      state.neoEntities.clear();
      state.defenseEntities.clear();
      neoState.entities = [];
      state.isShowingCrater = false;
      document.getElementById('toggleButton').style.display = 'none';
      document.getElementById('toggleButton').textContent = 'Show Crater';

      const shouldRenderDefense = (forceDefenseVisualization || defenseOverlayEnabled)
        && latestDefensePlan
        && Array.isArray(latestDefensePlan.loadout)
        && latestDefensePlan.loadout.length > 0;

      if (shouldRenderDefense) {
        renderDefensePlan(latestDefensePlan, { flyTo: false });
      } else {
        clearDefenseEntities();
      }

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

    window.replayDefenseVisualization = () => {
      if (!latestDefensePlan || !Array.isArray(latestDefensePlan.loadout) || latestDefensePlan.loadout.length === 0) {
        return;
      }
      try {
        renderDefensePlan(latestDefensePlan, { flyTo: true });
        cameraMode = 'asteroid';
        const cameraToggleButton = document.getElementById('cameraToggleButton');
        if (cameraToggleButton) {
          cameraToggleButton.textContent = 'Focus Impact';
        }
        resetSimulation({ forceDefenseVisualization: !defenseOverlayEnabled });
      } catch (error) {
        console.error('Failed to replay defense visualization', error);
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
