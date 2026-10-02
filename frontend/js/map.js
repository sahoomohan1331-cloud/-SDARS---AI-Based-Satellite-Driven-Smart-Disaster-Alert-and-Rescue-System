// ================================================
// SDARS - Enhanced Interactive Map with Popups
// 3D Globe-like visualization with weather details
// ================================================

const API_BASE_URL = window.API_BASE_URL || ((window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') ? 'http://127.0.0.1:8000/api' : '/api');

let map;
let markers = {};
let currentInfoWindow = null;
let terrainLayers = {};
let currentLayerName = 'dark';

// Global monitored locations (diverse worldwide coverage)
const monitoredLocations = [
    // Asia
    { name: 'Tokyo, JP', lat: 35.6762, lon: 139.6503, region: 'Asia' },
    { name: 'Mumbai, IN', lat: 19.0760, lon: 72.8777, region: 'Asia' },
    { name: 'Singapore, SG', lat: 1.3521, lon: 103.8198, region: 'Asia' },
    { name: 'Seoul, KR', lat: 37.5665, lon: 126.9780, region: 'Asia' },
    { name: 'Bangkok, TH', lat: 13.7563, lon: 100.5018, region: 'Asia' },
    // Europe
    { name: 'London, UK', lat: 51.5074, lon: -0.1278, region: 'Europe' },
    { name: 'Paris, FR', lat: 48.8566, lon: 2.3522, region: 'Europe' },
    { name: 'Berlin, DE', lat: 52.5200, lon: 13.4050, region: 'Europe' },
    { name: 'Madrid, ES', lat: 40.4168, lon: -3.7038, region: 'Europe' },
    // Americas
    { name: 'New York, US', lat: 40.7128, lon: -74.0060, region: 'Americas' },
    { name: 'Los Angeles, US', lat: 34.0522, lon: -118.2437, region: 'Americas' },
    { name: 'São Paulo, BR', lat: -23.5505, lon: -46.6333, region: 'Americas' },
    { name: 'Toronto, CA', lat: 43.6532, lon: -79.3832, region: 'Americas' },
    // Africa & Middle East
    { name: 'Cairo, EG', lat: 30.0444, lon: 31.2357, region: 'Africa' },
    { name: 'Lagos, NG', lat: 6.5244, lon: 3.3792, region: 'Africa' },
    { name: 'Dubai, AE', lat: 25.2048, lon: 55.2708, region: 'Middle East' },
    // Oceania
    { name: 'Sydney, AU', lat: -33.8688, lon: 151.2093, region: 'Oceania' }
];

// Initialize map on page load
document.addEventListener('DOMContentLoaded', () => {
    initializeMap();
    loadAllLocations();

    // Auto-refresh every 5 minutes
    setInterval(refreshMap, 300000);
});

// Initialize Leaflet map
function initializeMap() {
    // Create map with custom styling - WORLD VIEW
    map = L.map('map', {
        center: [20, 0], // World center
        zoom: 2,         // Zoomed out to show world
        zoomControl: true,
        maxBounds: [[-90, -180], [90, 180]],
        worldCopyJump: true
    });

    // Define all available terrain layers
    terrainLayers = {
        dark: L.layerGroup([
            L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}', {
                attribution: 'Tiles &copy; Esri',
                maxZoom: 16
            }),
            L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Reference/MapServer/tile/{z}/{y}/{x}', {
                maxZoom: 16
            })
        ]),
        satellite: L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
            attribution: 'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EBP, and the GIS User Community'
        }),
        terrain: L.tileLayer('https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png', {
            maxZoom: 17,
            attribution: 'Map data: &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, <a href="http://viewfinderpanoramas.org">SRTM</a> | Map style: &copy; <a href="https://opentopomap.org">OpenTopoMap</a> (<a href="https://creativecommons.org/licenses/by-sa/3.0/">CC-BY-SA</a>)'
        }),
        streets: L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        })
    };

    // Add initial dark tactical layer
    terrainLayers.dark.addTo(map);

    // Add scale
    L.control.scale({
        position: 'bottomleft',
        imperial: false
    }).addTo(map);

    // Click anywhere on map to get weather data
    map.on('click', async function (e) {
        const lat = e.latlng.lat;
        const lon = e.latlng.lng;
        if (typeof notificationSystem !== 'undefined') {
            notificationSystem.info('Fetching weather data...', 2000);
        }
        await showWeatherForLocation(lat, lon, e.latlng);
    });
}

// ⭐ NEW: Switch Terrain Function
function setTerrain(type) {
    if (!terrainLayers[type]) return;

    // Remove current layer
    map.removeLayer(terrainLayers[currentLayerName]);

    // Add new layer
    terrainLayers[type].addTo(map);
    currentLayerName = type;

    // Update UI buttons
    document.querySelectorAll('.terrain-btn').forEach(btn => btn.classList.remove('active'));
    const activeBtn = document.querySelector(`.terrain-btn[onclick*="${type}"]`);
    if (activeBtn) activeBtn.classList.add('active');

    if (typeof notificationSystem !== 'undefined') {
        notificationSystem.info(`Switched to ${type.toUpperCase()} mode`, 2000);
    }
}

// Load all monitored and historical locations
async function loadAllLocations() {
    // 1. Parallel load all primary strategic monitored locations
    console.log("📡 Map: Parallel intelligence gathering for global monitored locations...");

    // Create an array of promises for monitored locations
    const monitoredPromises = monitoredLocations.map(location => addLocationMarker(location));

    // Wait for all monitored locations to at least start/finish loading
    await Promise.allSettled(monitoredPromises);

    // 2. ⭐ NEW: Fetch ALL historical predictions from the database
    try {
        const response = await fetch('${API_BASE_URL}/predictions/history');
        if (response.ok) {
            const history = await response.json();

            history.forEach(record => {
                // Skip if it's already in monitoredLocations (based on name)
                if (monitoredLocations.some(m => m.name === record.name)) return;

                // 🛑 CLEANUP: Skip generic waypoints/sectors from the main map history
                if (record.name.includes('Route Waypoint') || record.name.includes('Sector')) {
                    return;
                }

                const historyLoc = {
                    name: record.name,
                    lat: record.lat,
                    lon: record.lon,
                    isHistory: true
                };

                if (historyLoc.lat == null || historyLoc.lon == null) return;

                const pseudoPrediction = {
                    overall_risk_level: record.overall_risk,
                    primary_threat: record.primary_threat,
                    timestamp: record.timestamp,
                    fire: { confidence: record.risk_scores.fire, risk_level: record.overall_risk, reasons: ["Archived Prediction Record"] },
                    flood: { confidence: record.risk_scores.flood, risk_level: record.overall_risk, reasons: [] },
                    cyclone: { confidence: record.risk_scores.cyclone, risk_level: record.overall_risk, reasons: [] },
                    current_weather: record.weather || {
                        temperature: 25,
                        humidity: 60,
                        pressure: 1013,
                        wind_speed: 10,
                        weather_condition: "Snapshot Incomplete"
                    }
                };

                addLocationMarker(historyLoc, pseudoPrediction);
            });
        }
    } catch (err) {
        console.error("Failed to load historical sensor data:", err);
    }
}

// ⭐ ENHANCED: Faster popups with parallel data fetching and progressive loading
async function showWeatherForLocation(lat, lon, latlng) {
    try {
        // 1. Create loading popup immediately
        const loadingPopup = L.popup({
            className: 'custom-popup tact-popup',
            maxWidth: 400,
            closeButton: false
        })
            .setLatLng(latlng)
            .setContent(`
                <div class="popup-loading-state">
                    <div class="tactical-loader">
                        <div class="loader-ring"></div>
                        <div class="loader-core">🛰️</div>
                    </div>
                    <div class="loading-info">
                        <h3>INITIALIZING SENSOR FUSION</h3>
                        <p class="scanning-text">Target: ${lat.toFixed(4)}, ${lon.toFixed(4)}</p>
                        <div class="scan-bar"><div class="scan-progress"></div></div>
                    </div>
                </div>
            `)
            .openOn(map);

        // 2. Parallel data fetching
        const locationPromise = getLocationName(lat, lon);
        const prediction = await fetchPrediction(lat, lon, `Sector [${lat.toFixed(2)}, ${lon.toFixed(2)}]`);

        if (!prediction) {
            loadingPopup.setContent(`
                <div class="popup-error">
                    <div class="error-icon">⚠️</div>
                    <h3>SATELLITE LINK FAILURE</h3>
                    <p>Unable to establish secure connection to predictive engine.</p>
                    <button onclick="map.closePopup()" class="btn-retry">Close</button>
                </div>
            `);
            return;
        }

        // 3. Render content immediately with coordinates as fallback name
        let displayName = `${lat.toFixed(4)}°, ${lon.toFixed(4)}°`;
        const popupContent = createClickPopupContent({
            name: displayName,
            lat: lat,
            lon: lon
        }, prediction);

        loadingPopup.setContent(popupContent);

        // 4. Update name asynchronously (Fixed selector bug)
        locationPromise.then(realName => {
            if (realName) {
                // Try multiple possible class combinations to ensure update
                const titleTargets = [
                    '.target-title h3',
                    '.popup-header h3',
                    '.location-popup .popup-header h3'
                ];

                let updated = false;
                titleTargets.forEach(selector => {
                    const el = document.querySelector(`.leaflet-popup-content ${selector}`);
                    if (el && !updated) {
                        el.innerText = realName;
                        el.style.color = '#00f2ff'; // Strategic cyan highlight
                        updated = true;
                    }
                });

                if (typeof notificationSystem !== 'undefined') {
                    notificationSystem.success(`Target identified: ${realName}`, 2000);
                }
            }
        });

        // 5. Temporary tactical marker
        const maxRisk = getMaxRisk(prediction);
        const tempMarker = L.circleMarker(latlng, {
            radius: 12,
            fillColor: getRiskColor(maxRisk),
            color: '#fff',
            weight: 3,
            opacity: 1,
            fillOpacity: 0.8,
            className: 'pulse-marker'
        }).addTo(map);

        loadingPopup.on('remove', () => map.removeLayer(tempMarker));

    } catch (error) {
        console.error('CRITICAL MAP ERROR:', error);
        notificationSystem?.error('Map Signal Lost');
    }
}

// Get location name from coordinates (detailed reverse geocoding)
async function getLocationName(lat, lon) {
    try {
        const response = await fetch(
            `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lon}&zoom=14`,
            { headers: { 'Accept-Language': 'en', 'User-Agent': 'SDARS-System/1.0' } }
        );

        if (response.ok) {
            const data = await response.json();
            const addr = data.address;

            if (!addr) return data.display_name || `${lat.toFixed(3)}°, ${lon.toFixed(3)}°`;

            // Build premium area name
            const parts = [];
            if (addr.suburb) parts.push(addr.suburb);
            else if (addr.neighbourhood) parts.push(addr.neighbourhood);

            const city = addr.city || addr.town || addr.village;
            if (city) parts.push(city);

            const state = addr.state;
            if (state && parts.length < 2) parts.push(state);

            if (parts.length === 0) return addr.country || `${lat.toFixed(3)}°, ${lon.toFixed(3)}°`;
            return parts.join(', ');
        }
    } catch (error) {
        console.warn('Geocoding blocked:', error);
    }
    return `${lat.toFixed(3)}°, ${lon.toFixed(3)}°`;
}

// ⭐ PREMIUM: High-Impact Tactical Popup Content (Impact-Based: Hazard x Exposure x Vulnerability)
function createClickPopupContent(location, prediction) {
    const weather = prediction.current_weather || {};
    const riskLevel = (prediction.overall_risk_level || 'Safe').toUpperCase();
    const riskClass = (prediction.overall_risk_level || 'safe').toLowerCase();

    // Support all 7 hazard types
    const allHazards = [
        { name: 'FIRE', val: prediction.fire?.confidence || 0, color: '#f97316', icon: '🔥' },
        { name: 'FLOOD', val: prediction.flood?.confidence || 0, color: '#38bdf8', icon: '🌊' },
        { name: 'CYCLONE', val: prediction.cyclone?.confidence || 0, color: '#a855f7', icon: '🌪️' },
        { name: 'HEATWAVE', val: prediction.heatwave?.confidence || 0, color: '#ef4444', icon: '🌡️' },
        { name: 'DROUGHT', val: prediction.drought?.confidence || 0, color: '#eab308', icon: '☀️' },
        { name: 'LANDSLIDE', val: prediction.landslide?.confidence || 0, color: '#854d0e', icon: '⛰️' },
        { name: 'STORM SURGE', val: prediction.storm_surge?.confidence || 0, color: '#06b6d4', icon: '🌊' },
        { name: 'LIGHTNING', val: prediction.lightning?.confidence || 0, color: '#eab308', icon: '⚡' }
    ].filter(h => h.val > 0.05).sort((a, b) => b.val - a.val);

    const displayHazards = allHazards.length > 0 ? allHazards.slice(0, 4) : [
        { name: 'BASELINE STABLE', val: 0.05, color: '#10b981', icon: '✅' }
    ];

    // Exposure & Vulnerability
    const exp = prediction.exposure || {};
    const vuln = prediction.vulnerability || {};
    const popDensity = exp.population_density ? exp.population_density.toLocaleString() + ' /km²' : 'Moderate Urban';
    const vulnScore = vuln.vulnerability_index != null ? Math.round(vuln.vulnerability_index * 100) + '%' : '35%';

    return `
        <div class="location-popup clicked-location">
            <div class="popup-header">
                <div class="target-title">
                    <span style="font-size: 18px;">📍</span>
                    <h3>${location.name}</h3>
                </div>
                <div class="overall-badge ${riskClass}" style="background: ${getRiskColor(riskClass)}; color: #fff; font-weight: 700; padding: 3px 8px; border-radius: 4px; font-size: 11px;">
                    ${riskLevel}
                </div>
            </div>
            
            <div class="popup-telem" style="display: flex; justify-content: space-between; font-size: 11px; color: #94a3b8; margin-bottom: 8px;">
                <span>COORDS: ${location.lat.toFixed(4)}, ${location.lon.toFixed(4)}</span>
                <span style="color: #38bdf8;">IMPACT-BASED AI</span>
            </div>

            <!-- Impact Matrix: Exposure & Vulnerability -->
            <div style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: 8px; padding: 8px 10px; margin-bottom: 10px; font-size: 11px;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                    <span style="color: #94a3b8;">👥 Population Exposure:</span>
                    <strong style="color: #38bdf8;">${popDensity}</strong>
                </div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                    <span style="color: #94a3b8;">🛡️ Fragility Index:</span>
                    <strong style="color: #fbbf24;">${vulnScore}</strong>
                </div>
                <div style="display: flex; justify-content: space-between; border-top: 1px dashed rgba(255,255,255,0.1); padding-top: 4px; margin-top: 4px;">
                    <span style="color: #94a3b8;">Model Formulation:</span>
                    <span style="color: #e2e8f0; font-family: monospace; font-size: 10px;">Hazard × Exposure × Vulnerability</span>
                </div>
            </div>

            <div class="popup-grid" style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 4px; margin-bottom: 8px;">
                <div class="grid-item" style="padding: 4px 6px;">
                    <span class="item-label" style="font-size: 8px;">TEMP</span>
                    <span class="item-val" style="font-size: 11px;">${weather.temperature != null ? weather.temperature : '--'}°C</span>
                </div>
                <div class="grid-item" style="padding: 4px 6px;">
                    <span class="item-label" style="font-size: 8px;">HUMID</span>
                    <span class="item-val" style="font-size: 11px;">${weather.humidity != null ? weather.humidity : '--'}%</span>
                </div>
                <div class="grid-item" style="padding: 4px 6px;">
                    <span class="item-label" style="font-size: 8px;">GUSTS</span>
                    <span class="item-val" style="font-size: 11px;">${weather.wind_gusts != null ? Math.round(weather.wind_gusts) : weather.wind_speed || '--'}k/h</span>
                </div>
                <div class="grid-item" style="padding: 4px 6px;">
                    <span class="item-label" style="font-size: 8px;">PRESSURE</span>
                    <span class="item-val" style="font-size: 11px;">${weather.pressure || 1013}hPa</span>
                </div>
                <div class="grid-item" style="padding: 4px 6px;">
                    <span class="item-label" style="font-size: 8px;">SOIL H₂O</span>
                    <span class="item-val" style="font-size: 11px; color: #38bdf8;">${weather.soil_moisture != null ? weather.soil_moisture.toFixed(2) : '0.25'}</span>
                </div>
                <div class="grid-item" style="padding: 4px 6px;">
                    <span class="item-label" style="font-size: 8px;">ELEV</span>
                    <span class="item-val" style="font-size: 11px; color: #a78bfa;">${weather.elevation != null ? Math.round(weather.elevation) + 'm' : '50m'}</span>
                </div>
                <div class="grid-item" style="padding: 4px 6px;">
                    <span class="item-label" style="font-size: 8px;">DEW PT</span>
                    <span class="item-val" style="font-size: 11px; color: #fbbf24;">${weather.dew_point != null ? weather.dew_point.toFixed(1) + '°' : '--'}</span>
                </div>
                <div class="grid-item" style="padding: 4px 6px;">
                    <span class="item-label" style="font-size: 8px;">24H RAIN</span>
                    <span class="item-val" style="font-size: 11px; color: #34d399;">${weather.forecast_rain_24h != null ? weather.forecast_rain_24h + 'mm' : '0mm'}</span>
                </div>
            </div>

            <div class="risk-sector" style="margin-top: 10px;">
                <h4 style="font-size: 11px; color: #a8b3cf; margin-bottom: 6px; letter-spacing: 0.5px;">MULTI-HAZARD VECTOR MATRIX</h4>
                ${displayHazards.map(r => `
                    <div class="risk-row" style="margin-bottom: 5px;">
                        <div class="row-header" style="display: flex; justify-content: space-between; font-size: 11px; margin-bottom: 2px;">
                            <span>${r.icon} ${r.name}</span>
                            <span style="font-weight: 700; color: ${r.color};">${Math.round(r.val * 100)}%</span>
                        </div>
                        <div class="row-bar-bg" style="height: 4px; background: rgba(255,255,255,0.1); border-radius: 2px; overflow: hidden;">
                            <div class="row-bar-fill" style="width: ${Math.min(100, Math.round(r.val * 100))}%; background: ${r.color}; height: 100%;"></div>
                        </div>
                    </div>
                `).join('')}
            </div>

            <div class="neural-logic-compact" style="margin-top: 8px; font-size: 11px; color: #94a3b8; background: rgba(0,0,0,0.2); padding: 6px; border-radius: 4px;">
                <div>> PRIMARY THREAT: <strong style="color: #fff;">${prediction.primary_threat?.toUpperCase() || 'LOW RISK'}</strong></div>
                <div>> AI REASONING: ${prediction.reasons && prediction.reasons[0] ? prediction.reasons[0] : 'Atmospheric & satellite sensors nominal'}</div>
            </div>

            <button onclick="viewDetailedAnalysis('${location.name.replace(/'/g, "\\'")}', ${location.lat}, ${location.lon})" 
                    class="btn-popup-detail btn-popup-primary" style="width: 100%; margin-top: 10px; margin-bottom: 5px; padding: 8px; font-size: 12px;">
                VIEW FULL STRATEGIC INTELLIGENCE
            </button>
        </div>
    `;
}

// Add marker with custom popup
async function addLocationMarker(location, existingPrediction = null) {
    try {
        let prediction = existingPrediction;
        if (!prediction) {
            prediction = await fetchPrediction(location.lat, location.lon, location.name);
        }

        if (!prediction) {
            addFallbackMarker(location);
            return;
        }

        const maxRisk = getMaxRisk(prediction);
        const markerColor = getRiskColor(maxRisk);

        // Create custom icon
        const icon = L.divIcon({
            className: 'custom-marker',
            html: `
                <div class="marker-pin ${maxRisk} ${location.isHistory ? 'history-pin' : ''}" style="background: ${markerColor}; ${location.isHistory ? 'transform: scale(0.7); opacity: 0.8;' : ''}">
                    <div class="marker-icon">${getDisasterIcon(prediction)}</div>
                </div>
                <div class="marker-label">${location.name} ${location.isHistory ? '<br><small style="font-size: 8px;">(Archived)</small>' : ''}</div>
            `,
            iconSize: [40, 50],
            iconAnchor: [20, 50],
            popupAnchor: [0, -50]
        });

        const marker = L.marker([location.lat, location.lon], { icon }).addTo(map);
        marker.isHistory = location.isHistory || false;
        marker.riskLevel = maxRisk;

        const popupContent = createPopupContent(location, prediction);
        marker.bindPopup(popupContent, {
            maxWidth: 400,
            className: 'custom-popup tact-popup'
        });

        marker.on('click', () => {
            showLocationDetails(location, prediction);
        });

        markers[location.name] = marker;
        updateMapStatistics();

    } catch (error) {
        console.error(`Error loading ${location.name}:`, error);
        addFallbackMarker(location);
    }
}

// Unified popup content for strategic nodes
function createPopupContent(location, prediction) {
    return createClickPopupContent(location, prediction);
}

// Get maximum risk level (4-Tier: CRITICAL, HIGH, MODERATE, LOW)
function getMaxRisk(prediction) {
    if (prediction.overall_risk_level) {
        const lvl = prediction.overall_risk_level.toLowerCase();
        if (['critical', 'high', 'moderate', 'medium', 'low', 'safe'].includes(lvl)) {
            return lvl === 'medium' ? 'moderate' : lvl;
        }
    }

    const confidences = [
        prediction.fire?.confidence || 0,
        prediction.flood?.confidence || 0,
        prediction.cyclone?.confidence || 0,
        prediction.heatwave?.confidence || 0,
        prediction.drought?.confidence || 0,
        prediction.landslide?.confidence || 0,
        prediction.storm_surge?.confidence || 0,
        prediction.lightning?.confidence || 0
    ];

    const maxVal = Math.max(...confidences);
    if (maxVal > 0.85) return 'critical';
    if (maxVal > 0.60) return 'high';
    if (maxVal > 0.30) return 'moderate';
    if (maxVal > 0.10) return 'low';
    return 'safe';
}

// Get risk color (4-tier standard)
function getRiskColor(risk) {
    switch (risk?.toLowerCase()) {
        case 'critical': return '#ef4444';
        case 'high': return '#f97316';
        case 'moderate':
        case 'medium': return '#eab308';
        case 'low': return '#10b981';
        case 'safe': return '#06b6d4';
        default: return '#94a3b8';
    }
}

// Get disaster icon for all 7 hazard types
function getDisasterIcon(prediction) {
    const threat = (prediction.primary_threat || '').toLowerCase();
    if (threat === 'fire') return '🔥';
    if (threat === 'flood') return '🌊';
    if (threat === 'cyclone') return '🌪️';
    if (threat === 'heatwave') return '🌡️';
    if (threat === 'drought') return '☀️';
    if (threat === 'landslide') return '⛰️';
    if (threat === 'storm_surge') return '🌊';
    if (threat === 'lightning') return '⚡';
    return '✅';
}

// Fallback marker (when API fails)
function addFallbackMarker(location) {
    if (location.lat == null || location.lon == null) {
        console.warn(`Cannot add fallback marker for ${location.name}: coordinates missing`);
        return;
    }

    const icon = L.divIcon({
        className: 'custom-marker',
        html: `
            <div class="marker-pin low">
                <div class="marker-icon">📍</div>
            </div>
            <div class="marker-label">${location.name}</div>
        `,
        iconSize: [40, 50],
        iconAnchor: [20, 50]
    });

    const marker = L.marker([location.lat, location.lon], { icon }).addTo(map);
    marker.bindPopup(`<strong>${location.name}</strong><br>Data loading...`);
    markers[location.name] = marker;
}

// Show location details in side panel
function showLocationDetails(location, prediction) {
    const infoPanel = document.getElementById('locationInfo');
    const title = document.getElementById('infoTitle');
    const content = document.getElementById('infoContent');

    title.textContent = `${location.name} - Detailed View`;

    content.innerHTML = `
        <div class="detail-section">
            <h4>Primary Threat</h4>
            <div class="threat-badge ${prediction.overall_risk_level.toLowerCase()}">
                ${getDisasterIcon(prediction)} ${prediction.primary_threat.toUpperCase()}
                <span class="threat-level">${prediction.overall_risk_level}</span>
            </div>
        </div>

        <div class="detail-section">
            <h4>Current Conditions</h4>
            <div class="conditions-grid">
                ${Object.entries(prediction.current_weather || {}).map(([key, value]) => `
                    <div class="condition-item">
                        <span class="key">${key.replace('_', ' ')}:</span>
                        <span class="value">${value}</span>
                    </div>
                `).join('')}
            </div>
        </div>

        <div class="detail-section">
            <h4>Risk Breakdown</h4>
            ${createRiskBreakdown(prediction)}
        </div>
    `;

    infoPanel.classList.remove('hidden');
    currentInfoWindow = location.name;
}

// Create risk breakdown
function createRiskBreakdown(prediction) {
    const risks = ['fire', 'flood', 'cyclone'];
    return risks.map(risk => {
        const data = prediction[risk] || {};
        return `
            <div class="risk-detail">
                <div class="risk-detail-header">
                    <span class="risk-name">${getDisasterIcon({ primary_threat: risk })} ${risk.toUpperCase()}</span>
                    <span class="risk-confidence">${Math.round((data.confidence || 0) * 100)}%</span>
                </div>
                <div class="risk-reasons">
                    ${(data.reasons || []).map(reason => `<li>${reason}</li>`).join('')}
                </div>
            </div>
        `;
    }).join('');
}

// Close location info panel
function closeLocationInfo() {
    document.getElementById('locationInfo').classList.add('hidden');
    currentInfoWindow = null;
}

// Toggle layer visibility
function toggleLayer(layer) {
    const checkbox = document.getElementById(`show${layer.charAt(0).toUpperCase() + layer.slice(1)}`);
    // Filter markers based on layer
    // Implementation depends on how you want to filter
    console.log(`Toggle ${layer}: ${checkbox.checked}`);
}

// Refresh map data
async function refreshMap() {
    showSuccess('Refreshing map data...');

    // Clear existing markers
    Object.values(markers).forEach(marker => map.removeLayer(marker));
    markers = {};

    // Reload locations
    await loadAllLocations();

    showSuccess('Map data refreshed!');
}

// View detailed analysis in the Dashboard/Prediction page
function viewDetailedAnalysis(name, lat, lon) {
    const targetName = name || 'Coordinate Scan';
    window.location.href = `prediction.html?lat=${lat}&lon=${lon}&name=${encodeURIComponent(targetName)}`;
}

// Add CSS for custom markers and popups
const mapStyles = document.createElement('style');
mapStyles.textContent = `
    .custom-marker {
        position: relative;
    }

    .marker-pin {
        width: 30px;
        height: 30px;
        border-radius: 50% 50% 50% 0;
        background: #4caf50;
        position: absolute;
        transform: rotate(-45deg);
        left: 50%;
        top: 50%;
        margin: -20px 0 0 -15px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.4);
    }

    .marker-pin.critical { background: linear-gradient(135deg, #ef4444, #991b1b); box-shadow: 0 0 16px rgba(239,68,68,0.9); animation: pulseCritical 1.5s infinite; }
    .marker-pin.high { background: linear-gradient(135deg, #f97316, #c2410c); }
    .marker-pin.moderate { background: linear-gradient(135deg, #eab308, #a16207); }
    .marker-pin.medium { background: linear-gradient(135deg, #eab308, #a16207); }
    .marker-pin.low { background: linear-gradient(135deg, #10b981, #047857); }
    .marker-pin.safe { background: linear-gradient(135deg, #06b6d4, #0369a1); }
    .marker-pin.gauge-pin { background: linear-gradient(135deg, #38bdf8, #0284c7); border: 2px solid #fff; }
    .marker-pin.crowd-pin { background: linear-gradient(135deg, #f43f5e, #be123c); border: 2px solid #fff; }
    .marker-pin.resource-pin { background: linear-gradient(135deg, #a78bfa, #7c3aed); border: 2px solid #fff; }
    .marker-pin.road-pin { background: linear-gradient(135deg, #fbbf24, #d97706); border: 2px solid #fff; }

    @keyframes pulseCritical {
        0% { transform: rotate(-45deg) scale(1); }
        50% { transform: rotate(-45deg) scale(1.15); box-shadow: 0 0 25px rgba(239,68,68,1); }
        100% { transform: rotate(-45deg) scale(1); }
    }

    .marker-pin::after {
        content: '';
        width: 10px;
        height: 10px;
        margin: 10px 0 0 10px;
        background: #fff;
        position: absolute;
        border-radius: 50%;
    }

    .marker-icon {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%) rotate(45deg);
        font-size: 16px;
        filter: drop-shadow(0 0 2px rgba(0,0,0,0.5));
    }

    .marker-label {
        position: absolute;
        top: 35px;
        left: 50%;
        transform: translateX(-50%);
        background: rgba(0, 0, 0, 0.8);
        color: white;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: 600;
        white-space: nowrap;
        pointer-events: none;
    }

    @keyframes bounce {
        0%, 100% { transform: rotate(-45deg) translateY(0); }
        50% { transform: rotate(-45deg) translateY(-10px); }
    }

    .custom-popup .leaflet-popup-content-wrapper {
        background: rgba(19, 24, 37, 0.95);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 0;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
    }

    .custom-popup .leaflet-popup-content {
        margin: 0;
        min-width: 300px;
    }

    .location-popup {
        padding: 16px;
        color: #fff;
    }

    .popup-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 16px;
        padding-bottom: 12px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    }

    .popup-header h3 {
        margin: 0;
        font-size: 18px;
        font-weight: 700;
    }

    .popup-weather h4,
    .popup-risks h4 {
        font-size: 14px;
        margin: 12px 0 8px 0;
        color: #a8b3cf;
    }

    .weather-grid-popup {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 8px;
        margin-bottom: 12px;
    }

    .weather-item-popup {
        background: rgba(255, 255, 255, 0.05);
        padding: 8px;
        border-radius: 8px;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    .weather-item-popup .icon {
        font-size: 20px;
    }

    .weather-item-popup .value {
        font-size: 14px;
        font-weight: 600;
        color: #ffffff; /* Ensure visible white text */
    }

    .risk-bars {
        display: flex;
        flex-direction: column;
        gap: 8px;
    }

    .risk-bar-item {
        font-size: 13px;
    }

    .risk-bar-header {
        display: flex;
        justify-content: space-between;
        margin-bottom: 4px;
    }

    .risk-bar-track {
        height: 6px;
        background: rgba(255, 255, 255, 0.1);
        border-radius: 3px;
        overflow: hidden;
    }

    .risk-bar-fill {
        height: 100%;
        transition: width 1s ease;
    }

    .risk-bar-fill.fire { background: linear-gradient(90deg, #ff5722, #ff8a50); }
    .risk-bar-fill.flood { background: linear-gradient(90deg, #2196f3, #64b5f6); }
    .risk-bar-fill.cyclone { background: linear-gradient(90deg, #9c27b0, #ba68c8); }

    /* Simplified Popup Styles */
    .weather-brief {
        display: flex;
        justify-content: space-around;
        padding: 10px;
        background: rgba(255, 255, 255, 0.05);
        border-radius: 8px;
        margin-bottom: 15px;
        font-size: 14px;
    }

    .badge {
        font-size: 10px;
        padding: 2px 8px;
        border-radius: 10px;
        text-transform: uppercase;
        font-weight: 700;
    }
    .badge.high { background: #ff5722; color: white; }
    .badge.medium { background: #ffc107; color: black; }
    .badge.low { background: #4caf50; color: white; }

    .popup-actions {
        margin-top: 16px;
    }

    .btn-popup-detail {
        width: 100%;
        padding: 10px;
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s ease;
    }

    .btn-popup-detail:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
    }

    .popup-footer {
        margin-top: 12px;
        padding-top: 12px;
        border-top: 1px solid rgba(255, 255, 255, 0.1);
        text-align: center;
    }

    .popup-footer small {
        color: #6b7a99;
        font-size: 11px;
    }
`;

// ═══════════════════════════════════════════════════════════════════
// SPRINT 3, 4, 5: TELEMETRY LAYERS (GAUGES, CROWD, RESOURCES, ROADS)
// ═══════════════════════════════════════════════════════════════════

let gaugeMarkers = [];
let crowdMarkers = [];
let resourceMarkers = [];
let roadMarkers = [];

// Load River Telemetry
async function loadRiverGauges() {
    try {
        const res = await fetch('${API_BASE_URL}/gauges');
        if (!res.ok) return;
        const data = await res.json();
        
        gaugeMarkers.forEach(m => map.removeLayer(m));
        gaugeMarkers = [];

        data.gauges.forEach(g => {
            const statusColor = g.status === 'DANGER' ? '#ef4444' : g.status === 'ALERT' ? '#eab308' : '#38bdf8';
            const icon = L.divIcon({
                className: 'custom-marker',
                html: `
                    <div class="marker-pin gauge-pin" style="background: ${statusColor};">
                        <div class="marker-icon">💧</div>
                    </div>
                    <div class="marker-label" style="border-left: 2px solid ${statusColor};">${g.station_name}</div>
                `,
                iconSize: [40, 50],
                iconAnchor: [20, 50]
            });

            const marker = L.marker([g.latitude, g.longitude], { icon }).addTo(map);
            marker.bindPopup(`
                <div style="font-family: 'Inter', sans-serif; padding: 12px; min-width: 250px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <h4 style="margin: 0; color: #38bdf8;">💧 RIVER TELEMETRY</h4>
                        <span style="background: ${statusColor}; color: #000; font-weight: 700; font-size: 10px; padding: 2px 6px; border-radius: 4px;">${g.status}</span>
                    </div>
                    <strong style="color: #fff; font-size: 13px;">${g.station_name}</strong>
                    <div style="margin-top: 10px; font-size: 12px; color: #cbd5e1; display: grid; grid-template-columns: 1fr 1fr; gap: 6px;">
                        <div>Current Level: <strong style="color: #fff;">${g.water_level_m} m</strong></div>
                        <div>Danger Mark: <strong style="color: #ef4444;">${g.danger_level_m} m</strong></div>
                        <div>Flow Discharge: <strong style="color: #fff;">${g.flow_rate_cumecs} m³/s</strong></div>
                        <div>Headroom: <strong style="color: #10b981;">${g.headroom_m} m</strong></div>
                    </div>
                </div>
            `);
            gaugeMarkers.push(marker);
        });
    } catch (e) {
        console.warn('Failed to load river gauges:', e);
    }
}

// Load Citizen Ground-Truth Reports
async function loadCrowdReports() {
    try {
        const res = await fetch('${API_BASE_URL}/crowd/reports');
        if (!res.ok) return;
        const data = await res.json();

        crowdMarkers.forEach(m => map.removeLayer(m));
        crowdMarkers = [];

        data.reports.forEach(r => {
            const sevColor = getRiskColor(r.severity);
            const verifiedBadge = r.is_verified === 1 ? '✅ Verified' : '⏳ Pending Review';
            const icon = L.divIcon({
                className: 'custom-marker',
                html: `
                    <div class="marker-pin crowd-pin" style="background: ${sevColor};">
                        <div class="marker-icon">📢</div>
                    </div>
                    <div class="marker-label" style="border-left: 2px solid ${sevColor};">Ground: ${r.report_type}</div>
                `,
                iconSize: [40, 50],
                iconAnchor: [20, 50]
            });

            const marker = L.marker([r.latitude, r.longitude], { icon }).addTo(map);
            marker.bindPopup(`
                <div style="font-family: 'Inter', sans-serif; padding: 12px; min-width: 250px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                        <h4 style="margin: 0; color: #f43f5e;">📢 CITIZEN OBSERVATION</h4>
                        <span style="font-size: 10px; color: ${r.is_verified === 1 ? '#10b981' : '#eab308'}; font-weight: 700;">${verifiedBadge}</span>
                    </div>
                    <div style="font-size: 12px; color: #94a3b8; margin-bottom: 6px;">${r.location_name} • <span style="color: ${sevColor}; font-weight: 700;">${r.severity}</span></div>
                    <p style="color: #fff; font-size: 12px; margin: 6px 0; background: rgba(255,255,255,0.05); padding: 8px; border-radius: 6px;">${r.description}</p>
                    <small style="color: #64748b; font-size: 10px;">Submitted: ${r.timestamp ? new Date(r.timestamp).toLocaleTimeString() : 'Just now'} by ${r.reporter_id || 'Citizen'}</small>
                </div>
            `);
            crowdMarkers.push(marker);
        });
    } catch (e) {
        console.warn('Failed to load crowd reports:', e);
    }
}

// Load Emergency Resources & Deployed Fleet
async function loadEmergencyResources() {
    try {
        const [resResp, vehResp] = await Promise.all([
            fetch('${API_BASE_URL}/resources'),
            fetch('${API_BASE_URL}/vehicles/live')
        ]);

        resourceMarkers.forEach(m => map.removeLayer(m));
        resourceMarkers = [];

        if (resResp.ok) {
            const data = await resResp.json();
            data.resources.forEach(r => {
                const typeIcon = r.type === 'shelter' ? '🏕️' : r.type === 'hospital' ? '🏥' : '🚒';
                const icon = L.divIcon({
                    className: 'custom-marker',
                    html: `
                        <div class="marker-pin resource-pin">
                            <div class="marker-icon">${typeIcon}</div>
                        </div>
                        <div class="marker-label">${r.name}</div>
                    `,
                    iconSize: [40, 50],
                    iconAnchor: [20, 50]
                });

                const marker = L.marker([r.latitude, r.longitude], { icon }).addTo(map);
                marker.bindPopup(`
                    <div style="font-family: 'Inter', sans-serif; padding: 12px;">
                        <h4 style="margin: 0 0 6px 0; color: #a78bfa;">${typeIcon} ${r.type.toUpperCase()}: ${r.name}</h4>
                        <div style="font-size: 12px; color: #cbd5e1;">Available Capacity: <strong style="color: #10b981;">${r.available_capacity} / ${r.capacity}</strong></div>
                        <div style="font-size: 12px; color: #cbd5e1;">Status: <strong style="color: #38bdf8;">${r.status}</strong></div>
                        <div style="font-size: 11px; color: #94a3b8; margin-top: 6px;">Hotline: ${r.contact_info || 'Local EOC Dispatch'}</div>
                    </div>
                `);
                resourceMarkers.push(marker);
            });
        }

        if (vehResp.ok) {
            const data = await vehResp.json();
            data.vehicles.forEach(v => {
                const icon = L.divIcon({
                    className: 'custom-marker',
                    html: `
                        <div class="marker-pin resource-pin" style="background: linear-gradient(135deg, #06b6d4, #0284c7);">
                            <div class="marker-icon">🚑</div>
                        </div>
                        <div class="marker-label">${v.vehicle_id} (${v.speed_kmh} km/h)</div>
                    `,
                    iconSize: [40, 50],
                    iconAnchor: [20, 50]
                });

                const marker = L.marker([v.latitude, v.longitude], { icon }).addTo(map);
                marker.bindPopup(`
                    <div style="font-family: 'Inter', sans-serif; padding: 12px;">
                        <h4 style="margin: 0 0 6px 0; color: #38bdf8;">🚑 LIVE GPS RESCUE TELEMETRY</h4>
                        <strong style="color: #fff; font-size: 13px;">${v.team} [${v.vehicle_id}]</strong>
                        <div style="font-size: 12px; color: #cbd5e1; margin-top: 6px;">Mission: ${v.mission}</div>
                        <div style="font-size: 12px; color: #38bdf8; margin-top: 4px;">Velocity: ${v.speed_kmh} km/h • Status: ${v.status}</div>
                    </div>
                `);
                resourceMarkers.push(marker);
            });
        }
    } catch (e) {
        console.warn('Failed to load emergency resources:', e);
    }
}

// Load Road Status & Hazard Blockages
async function loadRoadStatuses() {
    try {
        const res = await fetch('${API_BASE_URL}/roads/status');
        if (!res.ok) return;
        const data = await res.json();

        roadMarkers.forEach(m => map.removeLayer(m));
        roadMarkers = [];

        data.roads.forEach(rd => {
            if (rd.status === 'OPEN') return; // Only display alerts for obstacles/blockages
            const icon = L.divIcon({
                className: 'custom-marker',
                html: `
                    <div class="marker-pin road-pin">
                        <div class="marker-icon">⛔</div>
                    </div>
                    <div class="marker-label">${rd.name}</div>
                `,
                iconSize: [40, 50],
                iconAnchor: [20, 50]
            });

            const marker = L.marker([rd.latitude, rd.longitude], { icon }).addTo(map);
            marker.bindPopup(`
                <div style="font-family: 'Inter', sans-serif; padding: 12px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                        <h4 style="margin: 0; color: #fbbf24;">⛔ ROAD OBSTRUCTION</h4>
                        <span style="background: #ef4444; color: #fff; font-size: 10px; font-weight: 700; padding: 2px 6px; border-radius: 4px;">${rd.status}</span>
                    </div>
                    <strong style="color: #fff; font-size: 13px;">${rd.name}</strong>
                    <div style="font-size: 12px; color: #ef4444; margin-top: 4px;">${rd.reason}</div>
                    <div style="font-size: 11px; color: #38bdf8; margin-top: 6px; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 6px;">
                        🔄 Advised Detour: ${rd.detour || 'None available'}
                    </div>
                </div>
            `);
            roadMarkers.push(marker);
        });
    } catch (e) {
        console.warn('Failed to load road statuses:', e);
    }
}

// Layer Toggle Handlers
function toggleGaugesLayer() {
    const show = document.getElementById('showGauges')?.checked ?? true;
    gaugeMarkers.forEach(m => show ? m.addTo(map) : map.removeLayer(m));
}

function toggleCrowdLayer() {
    const show = document.getElementById('showCrowdReports')?.checked ?? true;
    crowdMarkers.forEach(m => show ? m.addTo(map) : map.removeLayer(m));
}

function toggleResourcesLayer() {
    const show = document.getElementById('showResources')?.checked ?? true;
    resourceMarkers.forEach(m => show ? m.addTo(map) : map.removeLayer(m));
}

function toggleRoadsLayer() {
    const show = document.getElementById('showRoads')?.checked ?? true;
    roadMarkers.forEach(m => show ? m.addTo(map) : map.removeLayer(m));
}

// ═══════════════════════════════════════════════════════════════════
// CITIZEN INCIDENT REPORT MODAL
// ═══════════════════════════════════════════════════════════════════

function openCrowdReportModal() {
    const modal = document.getElementById('crowdReportModal');
    if (modal) modal.style.display = 'flex';
}

function closeCrowdReportModal() {
    const modal = document.getElementById('crowdReportModal');
    if (modal) modal.style.display = 'none';
}

function autoFillCurrentCoords() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(pos => {
            document.getElementById('crLat').value = pos.coords.latitude.toFixed(4);
            document.getElementById('crLon').value = pos.coords.longitude.toFixed(4);
            document.getElementById('crLocationName').value = `GPS Incident Pin [${pos.coords.latitude.toFixed(2)}, ${pos.coords.longitude.toFixed(2)}]`;
            if (typeof notificationSystem !== 'undefined') {
                notificationSystem.info('Acquired live GPS coordinates');
            }
        }, err => {
            // Default to Delhi or Mumbai coordinates
            document.getElementById('crLat').value = '28.6650';
            document.getElementById('crLon').value = '77.2490';
            document.getElementById('crLocationName').value = 'Yamuna Basin Sector';
        });
    }
}

async function submitCrowdReportForm(e) {
    e.preventDefault();
    const btn = document.getElementById('crSubmitBtn');
    btn.disabled = true;
    btn.innerText = 'TRANSMITTING TELEMETRY...';

    const payload = {
        location_name: document.getElementById('crLocationName').value,
        latitude: parseFloat(document.getElementById('crLat').value),
        longitude: parseFloat(document.getElementById('crLon').value),
        report_type: document.getElementById('crType').value,
        severity: document.getElementById('crSeverity').value,
        description: document.getElementById('crDescription').value,
        reporter_id: 'Citizen Field Telemetry'
    };

    try {
        const res = await fetch('${API_BASE_URL}/crowd/report', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (res.ok) {
            closeCrowdReportModal();
            if (typeof notificationSystem !== 'undefined') {
                notificationSystem.success('Citizen observation transmitted and added to live map!', 4000);
            }
            await loadCrowdReports();
            document.getElementById('crowdReportForm').reset();
        } else {
            alert('Failed to submit ground observation.');
        }
    } catch (err) {
        console.error(err);
        alert('Server unreachable for ground observation submission.');
    } finally {
        btn.disabled = false;
        btn.innerText = 'TRANSMIT GROUND-TRUTH REPORT';
    }
}

// Toggle history markers
function toggleHistoryLayer() {
    const showHistory = document.getElementById('showHistory').checked;
    Object.values(markers).forEach(marker => {
        if (marker.isHistory) {
            if (showHistory) {
                marker.addTo(map);
            } else {
                map.removeLayer(marker);
            }
        }
    });
    updateMapStatistics();
}

// Update the 4-tier statistics numbers below the map
function updateMapStatistics() {
    let total = 0;
    let critical = 0;
    let high = 0;
    let moderate = 0;
    let safe = 0;

    Object.values(markers).forEach(marker => {
        if (map.hasLayer(marker)) {
            total++;
            const risk = marker.riskLevel?.toLowerCase();
            if (risk === 'critical') critical++;
            else if (risk === 'high') high++;
            else if (risk === 'moderate' || risk === 'medium') moderate++;
            else safe++;
        }
    });

    const totalEl = document.getElementById('totalLocations');
    const criticalEl = document.getElementById('criticalRiskZones');
    const highEl = document.getElementById('highRiskZones');
    const mediumEl = document.getElementById('mediumRiskZones');
    const safeEl = document.getElementById('safeZones');

    if (totalEl) totalEl.innerText = total;
    if (criticalEl) criticalEl.innerText = critical;
    if (highEl) highEl.innerText = high;
    if (mediumEl) mediumEl.innerText = moderate;
    if (safeEl) safeEl.innerText = safe;
}

// Hook all new telemetry layers into map startup
const oldInit = window.onload;
window.addEventListener('load', () => {
    loadRiverGauges();
    loadCrowdReports();
    loadEmergencyResources();
    loadRoadStatuses();
    setInterval(loadEmergencyResources, 15000); // Live vehicle movement updates
});

document.head.appendChild(mapStyles);
