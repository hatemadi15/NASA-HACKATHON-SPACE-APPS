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
  Cesium.Ion.defaultAccessToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiIyNDMzMTYwMy1hNDI2LTQ0NjAtOGM5MC02OGNhOGIwOGM0ODEiLCJpZCI6MzM4MzI2LCJpYXQiOjE3NTY5ODE5MDl9.MziOOEJHn4bXXuOm-RkxvZ8fD9YgqkOGyfbflKkxjaY';
  const viewer = new Cesium.Viewer(containerId, {
    terrain: Cesium.Terrain.fromWorldTerrain(),
  });

  // State
  const state = {
    activeAnimations: new Set(),
    visualizationEntities: new Set(),
    craterEntities: new Set(),
    isShowingCrater: false
  };

  // Get initial simulation data from user input
  let impact_location = { ...window.getImpactSettings() };
  let impact_result = {
    blast_radius: impact_location.blast_radius,
    crater_diameter: impact_location.crater_diameter,
    thermal_radius: impact_location.thermal_radius,
    fireball_radius: impact_location.fireball_radius,
    evacuation_radius: impact_location.evacuation_radius
  };
  let asteroid_properties = {
    size: impact_location.asteroid_size || 50,
    speed: impact_location.asteroid_speed || 20000,
    mass: impact_location.asteroid_mass || 1000000,
    density: impact_location.asteroid_density || 3000
  };
  let impactCartesian = Cesium.Cartesian3.fromDegrees(
    impact_location.longitude,
    impact_location.latitude,
    impact_location.elevation
  );

  // Listen for user input changes
  window.addEventListener('impactSettingsChanged', (e) => {
    impact_location = { ...e.detail };
    impact_result = {
      blast_radius: impact_location.blast_radius,
      crater_diameter: impact_location.crater_diameter,
      thermal_radius: impact_location.thermal_radius,
      fireball_radius: impact_location.fireball_radius,
      evacuation_radius: impact_location.evacuation_radius
    };
    asteroid_properties = {
      size: impact_location.asteroid_size || 50,
      speed: impact_location.asteroid_speed || 20000,
      mass: impact_location.asteroid_mass || 1000000,
      density: impact_location.asteroid_density || 3000
    };
    impactCartesian = Cesium.Cartesian3.fromDegrees(
      impact_location.longitude,
      impact_location.latitude,
      impact_location.elevation
    );
    resetSimulation();
  });

  // Animation cleanup function
  function cleanupAnimations() {
    state.activeAnimations.clear();
    viewer.entities.values.slice().forEach(entity => {
      if (!state.visualizationEntities.has(entity) && !state.craterEntities.has(entity)) {
        viewer.entities.remove(entity);
      }
    });
  }

  // Danger zones visualization
  function createDangerZones() {
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
  const startLon = impact_location.launch_longitude !== undefined ? impact_location.launch_longitude : (impact_location.longitude - 5);
  const startLat = impact_location.launch_latitude !== undefined ? impact_location.launch_latitude : (impact_location.latitude - 5);
  const startAlt = impact_location.launch_altitude !== undefined ? impact_location.launch_altitude : 100000;
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
        wave.ellipsoid.radii = new Cesium.Cartesian3(size, size, size * 0.2);
        wave.ellipsoid.material = Cesium.Color.RED.withAlpha(0.3 * (1 - frac));
        if (frac < 1) requestAnimationFrame(animateBlast);
        else viewer.entities.remove(wave);
      }
      requestAnimationFrame(animateBlast);
    }, durations.flash);
    setTimeout(() => {
      createCrater();
      state.isShowingCrater = true;
      document.getElementById('toggleButton').style.display = 'block';
      document.getElementById('toggleButton').textContent = 'Show Danger Zones';
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
    viewer.entities.removeAll();
    state.visualizationEntities.clear();
    state.craterEntities.clear();
    state.isShowingCrater = false;
    document.getElementById('toggleButton').style.display = 'none';
    document.getElementById('toggleButton').textContent = 'Show Crater';
    // Always use latest user input
    impact_location = { ...window.getImpactSettings() };
    impact_result = {
      blast_radius: impact_location.blast_radius,
      crater_diameter: impact_location.crater_diameter,
      thermal_radius: impact_location.thermal_radius,
      fireball_radius: impact_location.fireball_radius,
      evacuation_radius: impact_location.evacuation_radius
    };
    impactCartesian = Cesium.Cartesian3.fromDegrees(
      impact_location.longitude,
      impact_location.latitude,
      impact_location.elevation
    );
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
        setTimeout(animateAsteroidAndImpact, 1000);
      }
    });
  }
  document.getElementById('launchButton').addEventListener('click', resetSimulation);
  // Initial setup
  // resetSimulation(); // Remove this line so asteroid only launches on button click
}
