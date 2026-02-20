// ================================================
// SDARS - Enhanced Interactive Map with Popups
// 3D Globe-like visualization with weather details
// ================================================

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
        dark: L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
            attribution: '©OpenStreetMap, ©CartoDB',
            subdomains: 'abcd',
            maxZoom: 19
        }),
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
        const response = await fetch('http://localhost:8000/api/predictions/history');
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

// ⭐ PREMIUM: High-Impact Tactical Popup Content
function createClickPopupContent(location, prediction) {
    const weather = prediction.current_weather || {};
    const riskLevel = (prediction.overall_risk_level || 'Safe').toUpperCase();
    const riskClass = (prediction.overall_risk_level || 'safe').toLowerCase();

    const risks = [
        { name: 'FIRE', val: prediction.fire?.confidence || 0, color: '#ff4d00' },
        { name: 'FLOOD', val: prediction.flood?.confidence || 0, color: '#2196f3' },
        { name: 'CYCLONE', val: prediction.cyclone?.confidence || 0, color: '#9c27b0' }
    ].sort((a, b) => b.val - a.val);

    return `
        <div class="location-popup clicked-location">
            <div class="popup-header">
                <div class="target-title">
                    <span style="font-size: 18px;">📍</span>
                    <h3>${location.name}</h3>
                </div>
                <div class="overall-badge ${riskClass}">${riskLevel}</div>
            </div>
            
            <div class="popup-telem">
                <span class="label">COORDS:</span>
                <span class="coords">${location.lat.toFixed(4)}, ${location.lon.toFixed(4)}</span>
            </div>

            <div class="popup-grid">
                <div class="grid-item">
                    <span class="item-label">TEMP</span>
                    <span class="item-val">${weather.temperature || '--'}°C</span>
                </div>
                <div class="grid-item">
                    <span class="item-label">HUMID</span>
                    <span class="item-val">${weather.humidity || '--'}%</span>
                </div>
                <div class="grid-item">
                    <span class="item-label">WIND</span>
                    <span class="item-val">${weather.wind_speed || '--'}k/h</span>
                </div>
                <div class="grid-item">
                    <span class="item-label">VISIB</span>
                    <span class="item-val">85%</span>
                </div>
            </div>

            <div class="risk-sector">
                <h4>PROBABILITY MATRIX</h4>
                ${risks.map(r => `
                    <div class="risk-row">
                        <div class="row-header">
                            <span>${r.name} THREAT</span>
                            <span>${Math.round(r.val * 100)}%</span>
                        </div>
                        <div class="row-bar-bg">
                            <div class="row-bar-fill" style="width: ${r.val * 100}%; background: ${r.color};"></div>
                        </div>
                    </div>
                `).join('')}
            </div>

            <div class="neural-logic-compact">
                <div class="logic-header">STRATEGIC REASONING</div>
                <div class="logic-content">
                    <span>> ANALYZING SPECTRAL ANOMALIES</span>
                    <span>> ${prediction.primary_threat?.toUpperCase() || 'NORMAL'} VECTOR DETECTED</span>
                </div>
            </div>

            <button onclick="viewDetailedAnalysis('${location.name.replace(/'/g, "\\'")}', ${location.lat}, ${location.lon})" 
                    class="btn-popup-detail btn-popup-primary" style="width: calc(100% - 30px); margin-left: 15px; margin-bottom: 20px;">
                VIEW STRATEGIC DASHBOARD
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

// Get maximum risk level
function getMaxRisk(prediction) {
    const risks = {
        fire: prediction.fire?.confidence || 0,
        flood: prediction.flood?.confidence || 0,
        cyclone: prediction.cyclone?.confidence || 0
    };

    const maxVal = Math.max(risks.fire, risks.flood, risks.cyclone);

    if (maxVal > 0.7) return 'high';
    if (maxVal > 0.4) return 'medium';
    if (maxVal > 0.1) return 'low';
    return 'safe';
}

// Get risk color
function getRiskColor(risk) {
    switch (risk) {
        case 'high': return '#ff5722';
        case 'medium': return '#ffc107';
        case 'low': return '#4caf50';
        case 'safe': return '#2196f3';
        default: return '#9e9e9e';
    }
}

// Get disaster icon
function getDisasterIcon(prediction) {
    if (prediction.primary_threat === 'fire') return '🔥';
    if (prediction.primary_threat === 'flood') return '🌊';
    if (prediction.primary_threat === 'cyclone') return '🌪️';
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

    .marker-pin.high { background: linear-gradient(135deg, #ff5722, #ff8a50); }
    .marker-pin.medium { background: linear-gradient(135deg, #ffc107, #ffeb3b); }
    .marker-pin.low { background: linear-gradient(135deg, #4caf50, #81c784); }
    .marker-pin.safe { background: linear-gradient(135deg, #2196f3, #64b5f6); }

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

// Update the statistics numbers below the map
function updateMapStatistics() {
    let total = 0;
    let high = 0;
    let medium = 0;
    let safe = 0;

    Object.values(markers).forEach(marker => {
        // Only count markers currently on the map
        if (map.hasLayer(marker)) {
            total++;
            const risk = marker.riskLevel?.toLowerCase();
            if (risk === 'high') high++;
            else if (risk === 'medium') medium++;
            else safe++;
        }
    });

    // Update UI elements if they exist
    const totalEl = document.getElementById('totalLocations');
    const highEl = document.getElementById('highRiskZones');
    const mediumEl = document.getElementById('mediumRiskZones');
    const safeEl = document.getElementById('safeZones');

    if (totalEl) totalEl.innerText = total;
    if (highEl) highEl.innerText = high;
    if (mediumEl) mediumEl.innerText = medium;
    if (safeEl) safeEl.innerText = safe;
}

document.head.appendChild(mapStyles);
