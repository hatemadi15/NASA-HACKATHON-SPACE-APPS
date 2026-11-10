// API client for Meteor Madness backend
const API_BASE_URL = 'http://localhost:8000/api/v1';

class MeteorMadnessAPI {
    constructor() {
        this.baseURL = API_BASE_URL;
        this.token = null;
    }

    setToken(token) {
        this.token = token;
    }

    async _fetch(url, options = {}) {
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers,
        };

        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }

        const response = await fetch(url, {
            ...options,
            headers,
        });

        if (!response.ok) {
            console.log('Raw error response:', response);
            const rawBody = await response.text();
            console.log('Raw error body:', rawBody);
            try {
                const errorData = JSON.parse(rawBody);
                throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
            } catch (e) {
                throw new Error(rawBody || `HTTP error! status: ${response.status}`);
            }
        }

        return await response.json();
    }

    async login(username, password) {
        return this._fetch(`${this.baseURL}/auth/login`, {
            method: 'POST',
            body: JSON.stringify({ username, password }),
        });
    }

    async register(username, email, password, fullName) {
        return this._fetch(`${this.baseURL}/auth/register`, {
            method: 'POST',
            body: JSON.stringify({ username, email, password, full_name: fullName }),
        });
    }

    async logout() {
        // Logout doesn't require a response body, so we handle it separately
        const headers = {};
        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }
        await fetch(`${this.baseURL}/auth/logout`, {
            method: 'POST',
            headers,
        });
    }

    async getMe() {
        return this._fetch(`${this.baseURL}/auth/me`);
    }

    async getSimulationHistory() {
        return this._fetch(`${this.baseURL}/simulation/history`);
    }

    async simulateImpact(asteroidData, impactLocation, options = {}) {
        const requestData = {
            asteroid: {
                diameter: asteroidData.diameter || asteroidData.size,
                mass: asteroidData.mass,
                velocity: asteroidData.velocity || asteroidData.speed,
                density: asteroidData.density,
                impact_angle: asteroidData.impact_angle,
                composition: asteroidData.composition || "iron"
            },
            impact_location: {
                latitude: impactLocation.latitude,
                longitude: impactLocation.longitude,
                elevation: impactLocation.elevation || 0,
                terrain_type: impactLocation.terrain_type || "land",
                population_density: impactLocation.population_density || 0,
                infrastructure_density: impactLocation.infrastructure_density || 0,
                water_depth: impactLocation.water_depth || null
            },
            use_nasa_data: options.useNasaData || false,
            use_ml: options.useML || false,
            dv_mps: options.dvMps || 0,
            deflection_method: options.deflectionMethod || "none"
        };

        return this._fetch(`${this.baseURL}/simulation/simulate`, {
            method: 'POST',
            body: JSON.stringify(requestData)
        });
    }

    async calculateAdvancedImpact(asteroidData, impactLocation, calculationOptions = {}) {
        const requestData = {
            asteroid: {
                diameter: asteroidData.diameter || asteroidData.size,
                mass: asteroidData.mass,
                velocity: asteroidData.velocity || asteroidData.speed,
                density: asteroidData.density,
                impact_angle: asteroidData.impact_angle,
                composition: asteroidData.composition || "iron"
            },
            impact_location: {
                latitude: impactLocation.latitude,
                longitude: impactLocation.longitude,
                elevation: impactLocation.elevation || 0,
                terrain_type: impactLocation.terrain_type || "land",
                population_density: impactLocation.population_density || 0,
                infrastructure_density: impactLocation.infrastructure_density || 0,
                water_depth: impactLocation.water_depth || null
            },
            options: {
                calculate_human_casualties: calculationOptions.calculateHumanCasualties !== undefined ? calculationOptions.calculateHumanCasualties : true,
                calculate_infrastructure_damage: calculationOptions.calculateInfrastructureDamage !== undefined ? calculationOptions.calculateInfrastructureDamage : true,
                calculate_environmental_impact: calculationOptions.calculateEnvironmentalImpact !== undefined ? calculationOptions.calculateEnvironmentalImpact : true,
                calculate_economic_impact: calculationOptions.calculateEconomicImpact !== undefined ? calculationOptions.calculateEconomicImpact : true,
                calculate_damage_assessment: calculationOptions.calculateDamageAssessment !== undefined ? calculationOptions.calculateDamageAssessment : true,
                calculate_kinetic_energy: calculationOptions.calculateKineticEnergy !== undefined ? calculationOptions.calculateKineticEnergy : true,
                calculate_atmospheric_entry: calculationOptions.calculateAtmosphericEntry !== undefined ? calculationOptions.calculateAtmosphericEntry : true,
                calculate_crater_formation: calculationOptions.calculateCraterFormation !== undefined ? calculationOptions.calculateCraterFormation : true,
                calculate_blast_effects: calculationOptions.calculateBlastEffects !== undefined ? calculationOptions.calculateBlastEffects : true,
                calculate_tsunami_effects: calculationOptions.calculateTsunamiEffects !== undefined ? calculationOptions.calculateTsunamiEffects : true,
                recalculate_evacuation_radius: calculationOptions.recalculateEvacuationRadius !== undefined ? calculationOptions.recalculateEvacuationRadius : true,
                calculate_impact_result: calculationOptions.calculateImpactResult !== undefined ? calculationOptions.calculateImpactResult : true,
                use_ml_enhancer: calculationOptions.useMlEnhancer || false
            }
        };

        return this._fetch(`${this.baseURL}/simulation/calculate/advanced`, {
            method: 'POST',
            body: JSON.stringify(requestData)
        });
    }
    async getDeflectionLeaderboard() {
        return this._fetch(`${this.baseURL}/simulation/deflection-game/leaderboard`);
    }

    async getVersion() {
        return this._fetch('http://localhost:8000/version');
    }
}

// Create global API instance
window.meteorMadnessAPI = new MeteorMadnessAPI();

export { MeteorMadnessAPI };
