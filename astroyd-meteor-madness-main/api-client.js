// API client for Meteor Madness backend
const API_BASE_URL = 'http://localhost:8000/api/v1';

class MeteorMadnessAPI {
    constructor() {
        this.baseURL = API_BASE_URL;
    }

    async simulateImpact(asteroidData, impactLocation, options = {}) {
        try {
            const requestData = {
                asteroid: {
                    diameter: asteroidData.diameter || asteroidData.size,
                    mass: asteroidData.mass,
                    velocity: asteroidData.velocity || asteroidData.speed,
                    density: asteroidData.density,
                    composition: asteroidData.composition || "iron"
                },
                impact_location: {
                    latitude: impactLocation.latitude,
                    longitude: impactLocation.longitude,
                    elevation: impactLocation.elevation || 0,
                    terrain_type: impactLocation.terrain_type || "land",
                    population_density: impactLocation.population_density || 0
                },
                use_nasa_data: options.useNasaData || false,
                use_ml: options.useML || false,
                dv_mps: options.dvMps || 0,
                deflection_method: options.deflectionMethod || "none"
            };

            const response = await fetch(`${this.baseURL}/simulation/simulate`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestData)
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Error calling simulation API:', error);
            throw error;
        }
    }

    async getNasaData(params = {}) {
        try {
            const queryParams = new URLSearchParams(params);
            const response = await fetch(`${this.baseURL}/nasa/neo?${queryParams}`);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Error fetching NASA data:', error);
            throw error;
        }
    }

    async getEarthImagery(params = {}) {
        try {
            const queryParams = new URLSearchParams(params);
            const response = await fetch(`${this.baseURL}/nasa/earth-imagery?${queryParams}`);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Error fetching Earth imagery:', error);
            throw error;
        }
    }

    async getSolutions() {
        try {
            const response = await fetch(`${this.baseURL}/simulation/solutions`);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Error fetching solutions:', error);
            throw error;
        }
    }

    async submitDeflectionScore(scoreData) {
        try {
            const response = await fetch(`${this.baseURL}/simulation/deflection-game/submit-score`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(scoreData)
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Error submitting deflection score:', error);
            throw error;
        }
    }

    async getDeflectionLeaderboard() {
        try {
            const response = await fetch(`${this.baseURL}/simulation/deflection-game/leaderboard`);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Error fetching leaderboard:', error);
            throw error;
        }
    }

    async getVersion() {
        try {
            const response = await fetch('http://localhost:8000/version');

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Error fetching version:', error);
            throw error;
        }
    }

    async login(username, password) {
        try {
            const response = await fetch(`${this.baseURL}/auth/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ username, password })
            });

            const data = await response.json().catch(() => ({}));

            if (!response.ok) {
                const message = data?.detail || `Login failed with status ${response.status}`;
                throw new Error(message);
            }

            return data;
        } catch (error) {
            console.error('Error logging in:', error);
            throw error;
        }
    }

    async getProfile(accessToken) {
        try {
            const response = await fetch(`${this.baseURL}/auth/me`, {
                headers: {
                    'Authorization': `Bearer ${accessToken}`
                }
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                const message = errorData?.detail || `Profile request failed with status ${response.status}`;
                throw new Error(message);
            }

            return await response.json();
        } catch (error) {
            console.error('Error fetching profile:', error);
            throw error;
        }
    }

    async logout(accessToken) {
        try {
            const response = await fetch(`${this.baseURL}/auth/logout`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${accessToken}`
                }
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                const message = errorData?.detail || `Logout failed with status ${response.status}`;
                throw new Error(message);
            }

            return await response.json();
        } catch (error) {
            console.error('Error logging out:', error);
            throw error;
        }
    }
}

// Create global API instance
window.meteorMadnessAPI = new MeteorMadnessAPI();

export { MeteorMadnessAPI };
