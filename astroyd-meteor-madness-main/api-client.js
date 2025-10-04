// API client for Meteor Madness backend
const API_BASE_URL = 'http://localhost:8000/api/v1';

class MeteorMadnessAPI {
    constructor() {
        this.baseURL = API_BASE_URL;
    }

    _getAuthToken() {
        try {
            return window.localStorage?.getItem('meteorMadnessToken');
        } catch (error) {
            console.warn('Unable to access localStorage for auth token:', error);
            return null;
        }
    }

    _getRefreshToken() {
        try {
            return window.localStorage?.getItem('meteorMadnessRefreshToken');
        } catch (error) {
            console.warn('Unable to access localStorage for refresh token:', error);
            return null;
        }
    }

    _setAuthToken(token) {
        try {
            if (token) {
                window.localStorage?.setItem('meteorMadnessToken', token);
            } else {
                window.localStorage?.removeItem('meteorMadnessToken');
            }
        } catch (error) {
            console.warn('Unable to persist auth token:', error);
        }
    }

    _setRefreshToken(token) {
        try {
            if (token) {
                window.localStorage?.setItem('meteorMadnessRefreshToken', token);
            } else {
                window.localStorage?.removeItem('meteorMadnessRefreshToken');
            }
        } catch (error) {
            console.warn('Unable to persist refresh token:', error);
        }
    }

    clearStoredTokens() {
        this._setAuthToken(null);
        this._setRefreshToken(null);
    }

    _buildHeaders(base = {}) {
        const headers = { ...base };
        const token = this._getAuthToken();
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }
        return headers;
    }

    async simulateImpact(asteroidData, impactLocation, options = {}) {
        try {
            const requestData = {
                asteroid: {
                    diameter: asteroidData.diameter || asteroidData.size,
                    mass: asteroidData.mass,
                    velocity: asteroidData.velocity || asteroidData.speed,
                    impact_angle: asteroidData.impact_angle || asteroidData.impactAngle || 45,
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

            if (typeof options.calculateTrajectory === 'boolean') {
                requestData.calculate_trajectory = options.calculateTrajectory;
            }
            if (typeof options.includeZones === 'boolean') {
                requestData.include_zones = options.includeZones;
            }

            const response = await fetch(`${this.baseURL}/simulation/simulate`, {
                method: 'POST',
                headers: this._buildHeaders({
                    'Content-Type': 'application/json',
                }),
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

    async registerUser(userData) {
        try {
            const response = await fetch(`${this.baseURL}/auth/register`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(userData)
            });

            if (!response.ok) {
                const detail = await response.json().catch(() => ({}));
                throw new Error(detail.detail || `Registration failed: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Error registering user:', error);
            throw error;
        }
    }

    async loginUser(credentials) {
        try {
            const response = await fetch(`${this.baseURL}/auth/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(credentials)
            });

            if (!response.ok) {
                const detail = await response.json().catch(() => ({}));
                throw new Error(detail.detail || `Login failed: ${response.status}`);
            }

            const tokens = await response.json();
            this._setAuthToken(tokens.access_token);
            this._setRefreshToken(tokens.refresh_token);
            return tokens;
        } catch (error) {
            console.error('Error logging in:', error);
            throw error;
        }
    }

    async refreshAccessToken() {
        const refreshToken = this._getRefreshToken();
        if (!refreshToken) {
            throw new Error('No refresh token available');
        }

        const response = await fetch(`${this.baseURL}/auth/refresh`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ refresh_token: refreshToken })
        });

        if (!response.ok) {
            this.clearStoredTokens();
            throw new Error(`Refresh failed: ${response.status}`);
        }

        const tokens = await response.json();
        this._setAuthToken(tokens.access_token);
        this._setRefreshToken(tokens.refresh_token);
        return tokens;
    }

    async getProfile() {
        try {
            const response = await fetch(`${this.baseURL}/auth/me`, {
                headers: this._buildHeaders({ 'Accept': 'application/json' })
            });

            if (response.status === 401) {
                this.clearStoredTokens();
                throw new Error('Authentication required');
            }

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Error fetching profile:', error);
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
            const response = await fetch(`${this.baseURL}/simulation/solutions`, {
                headers: this._buildHeaders(),
            });

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
                headers: this._buildHeaders({
                    'Content-Type': 'application/json',
                }),
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
            const response = await fetch(`${this.baseURL}/simulation/deflection-game/leaderboard`, {
                headers: this._buildHeaders(),
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Error fetching leaderboard:', error);
            throw error;
        }
    }

    async getSimulationHistory(params = {}) {
        try {
            const queryParams = new URLSearchParams(params);
            const response = await fetch(`${this.baseURL}/simulation/history?${queryParams.toString()}`, {
                headers: this._buildHeaders(),
            });

            if (response.status === 401) {
                this.clearStoredTokens();
                throw new Error('Authentication required');
            }

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Error fetching simulation history:', error);
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
}

// Create global API instance
window.meteorMadnessAPI = new MeteorMadnessAPI();

export { MeteorMadnessAPI };
