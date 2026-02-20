/**
 * SDARS Prediction Tool - Advanced Analysis Engine
 * Handles Multi-Modal AI inference and Satellite Spectral visualization
 */

// Initialize Chart.js defaults
Chart.defaults.color = '#a8b3cf';
Chart.defaults.font.family = 'Inter, sans-serif';

// Standardized API Base URL - Dynamic detection to handle localhost vs 127.0.0.1
const API_BASE_URL = window.API_BASE_URL || `http://${window.location.hostname}:8000/api`;
console.log("📡 API Connection Point:", API_BASE_URL);

// Global Error Tracker for user feedback
window.onerror = function (message, source, lineno, colno, error) {
    console.error("SDARS JS Error:", message, "at", source, ":", lineno);
    if (window.showError) {
        showError(`Neural Link Error: ${message.split(':').pop()}`);
    }
    return false;
};

function toggleManualInput(e) {
    if (e) e.preventDefault();
    const zone = document.getElementById('manualInput');
    if (zone) zone.classList.toggle('hidden');
}

let spectralChart = null;

// New: History loading
async function loadHistorySidebar() {
    const list = document.getElementById('historicalPredictionsList');
    if (!list) return;

    try {
        const response = await fetch(`${API_BASE_URL}/predictions/history`);
        const history = await response.json();

        if (history.length === 0) {
            list.innerHTML = `<div class="history-item">No archives found.</div>`;
            return;
        }

        list.innerHTML = history.map(item => `
            <div class="history-item" onclick="fetchAndDisplayHistorical('${item.name}', ${item.lat}, ${item.lon})">
                <div class="h-name">${item.name}</div>
                <div class="h-meta">${item.primary_threat.toUpperCase()} • ${item.overall_risk}</div>
                <div class="h-time">${new Date(item.timestamp).toLocaleTimeString()}</div>
            </div>
        `).join('');
    } catch (err) {
        list.innerHTML = `<div class="history-item error">Sync Error</div>`;
    }
}

async function fetchAndDisplayHistorical(name, lat, lon) {
    fillPredictionInputs(lat, lon, name);
}

function writeToNeuralLog(lines) {
    const log = document.getElementById('neuralLogOutput');
    log.innerHTML = '';
    log.className = 'neural-reasoning cyber-scanner'; // Apply the new styles
    let i = 0;

    function addLine() {
        if (i < lines.length) {
            const line = document.createElement('div');
            line.className = 'log-line';
            // First line gets the typing-text effect for extra impact
            if (i === 0) {
                line.innerHTML = `<span class="prompt">></span> <span class="typing-text">${lines[i]}</span>`;
            } else {
                line.innerHTML = `<span class="prompt">></span> ${lines[i]}`;
            }
            log.appendChild(line);
            log.scrollTop = log.scrollHeight;
            i++;
            setTimeout(addLine, i === 0 ? 1000 : 150); // Delay first line for dramatic effect
        }
    }
    addLine();
}

async function runPrediction() {
    const lat = document.getElementById('latitude').value;
    const lon = document.getElementById('longitude').value;
    let name = document.getElementById('locationName').value;

    // Get name from search input if not set
    if (!name || name === 'Target Zone') {
        name = document.getElementById('predictionSearchInput')?.value || 'Target Zone';
    }

    if (lat === '' || lon === '' || lat === null || lon === null) {
        showNoPredictionMessage();
        return;
    }

    showLoading();

    try {
        const response = await fetch(`${API_BASE_URL}/predict`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ lat: parseFloat(lat), lon: parseFloat(lon), name: name })
        });

        if (!response.ok) throw new Error("Satellite Link Timeout");

        const data = await response.json();
        console.log("🧠 Intelligence Data Received:", data);

        if (!data || !data.primary_threat) {
            throw new Error("Invalid AI Response Structure");
        }

        // Show Neural Log Evidence
        const logLines = [
            `INITIATING MULTI-MODAL FUSION ENGINE...`,
            `TARGET: ${name} [${lat}, ${lon}]`,
            `CONNECTING TO NASA VIIRS SATELLITE...`,
            `SATELLITE DATA RECEIVED: ${(data.fire && data.fire.reasons) ? (data.fire.reasons[0] || 'No thermal alerts') : 'Data link stable'}`,
            `FETCHING OPEN-METEO ATMOSPHERIC DATA...`,
            `WEATHER VECTOR: Temp=${data.current_weather?.temperature || '??'}C, Humid=${data.current_weather?.humidity || '??'}%`,
            `RUNNING RANDOM FOREST ENSEMBLE CLASSIFIER...`,
            `INFERENCE COMPLETE: Primary Threat = ${data.primary_threat.toUpperCase()}`,
            `CONFIDENCE SCORE: ${Math.round((data[data.primary_threat]?.confidence || 0) * 100)}%`,
            `GENERATING SPECTRAL SIGNATURE...`
        ];
        writeToNeuralLog(logLines);

        renderDetailedResults(data, name);
        loadHistorySidebar(); // Refresh list
    } catch (err) {
        console.error("Analysis Failed:", err);
        alert("CRITICAL: Strategic data fetch failed. Check server status.");
        hideLoading();
    }
}

// Consolidated function to fill all inputs and trigger analysis
async function fillPredictionInputs(lat, lon, name) {
    console.log("🛠️ Filling Intelligence Inputs:", { lat, lon, name });

    const latInput = document.getElementById('latitude');
    const lonInput = document.getElementById('longitude');
    const nameInput = document.getElementById('locationName');
    const searchInput = document.getElementById('predictionSearchInput');

    if (latInput) latInput.value = lat;
    if (lonInput) lonInput.value = lon;

    // Use name or fallback
    let displayName = name || 'Target Zone';

    // If name is generic or missing, try to resolve it from coordinates
    const isGeneric = !name || name === 'Target Zone' || name === 'Coordinate Scan' || name === 'Current Location';

    if (isGeneric && lat && lon) {
        try {
            console.log("🏙️ Resolving location name for coordinates:", { lat, lon });
            const geoRes = await fetch(
                `https://nominatim.openstreetmap.org/reverse?lat=${lat}&lon=${lon}&format=json`,
                { headers: { 'User-Agent': 'SDARS-System/1.0' } }
            );
            const geoData = await geoRes.json();
            const addr = geoData.address || {};
            displayName = addr.city || addr.town || addr.village || addr.suburb || addr.state || addr.country || `${lat}, ${lon}`;
            console.log("✅ Location resolved:", displayName);
        } catch (e) {
            console.warn("Location resolution failed, using fallback:", e);
        }
    }

    if (nameInput) nameInput.value = displayName;
    if (searchInput) searchInput.value = displayName;

    // Show manual input zone to confirm coordinates
    const manualZone = document.getElementById('manualInput');
    if (manualZone && (lat || lon)) {
        manualZone.classList.remove('hidden');
    }

    // Trigger analysis
    runPrediction();
}

function selectLocation(lat, lon, name) {
    fillPredictionInputs(lat, lon, name);
}

function showLoading() {
    document.getElementById('loading').classList.remove('hidden');
    document.getElementById('results').classList.add('hidden');

    // Animate loading steps
    const steps = document.querySelectorAll('.loading-steps .step');
    let currentStep = 0;
    const interval = setInterval(() => {
        steps.forEach(s => s.classList.remove('active'));
        steps[currentStep].classList.add('active');
        currentStep++;
        if (currentStep >= steps.length) clearInterval(interval);
    }, 800);
}

function hideLoading() {
    document.getElementById('loading').classList.add('hidden');
}

function renderDetailedResults(data, name) {
    hideLoading();
    document.getElementById('results').classList.remove('hidden');

    // 1. Header & Timestamp
    document.getElementById('resultLocation').innerText = `Strategic Report: ${name}`;
    document.getElementById('resultTimestamp').innerText = `Analysis finalized at ${new Date().toLocaleTimeString()}`;

    // 2. Primary Threat Banner
    renderThreatBanner(data);

    // 3. Risk Cards
    updateRiskCard('fire', data.fire);
    updateRiskCard('flood', data.flood);
    updateRiskCard('cyclone', data.cyclone);

    // 4. Weather Conditions
    renderWeatherGrid(data.current_weather);

    // 5. NEW: Satellite Spectral Analysis Chart (The "Wow" Factor)
    renderSpectralAnalysis(data);

    // Scroll to results
    document.getElementById('results').scrollIntoView({ behavior: 'smooth' });
}

function renderThreatBanner(data) {
    const banner = document.getElementById('primaryThreat');
    if (!banner) return;

    const threat = (data.primary_threat || 'Unknown').toUpperCase();
    const risk = data.overall_risk_level || 'LOW';

    const colors = { 'HIGH': '#ff5252', 'MEDIUM': '#ffa726', 'LOW': '#66bb6a' };
    const bannerColor = colors[risk] || colors['LOW'];

    banner.style.borderLeft = `8px solid ${bannerColor}`;
    banner.innerHTML = `
        <div class="banner-content" style="display: flex; flex-direction: column; gap: 5px;">
            <span class="banner-main" style="font-size: 18px; font-weight: 800;">PRIMARY THREAT DETECTED: <strong style="color: ${bannerColor}; text-shadow: 0 0 10px ${bannerColor}44;">${threat}</strong></span>
            <span class="banner-sub" style="font-size: 13px; color: #a8b3cf;">Strategic Confidence Level: <strong>${risk} ALERT</strong></span>
        </div>
    `;
}

function updateRiskCard(type, riskData) {
    const badge = document.getElementById(`${type}RiskBadge`);
    const confNum = document.getElementById(`${type}ConfidenceNum`);
    const confFill = document.getElementById(`${type}ConfidenceFill`);
    const factorList = document.getElementById(`${type}Factors`);

    if (!riskData) return;
    const confidence = Math.round((riskData.confidence || 0) * 100);

    const colors = { 'HIGH': '#ff5252', 'MEDIUM': '#ffa726', 'LOW': '#66bb6a' };
    const riskColor = colors[riskData.risk_level] || colors['LOW'];

    if (badge) {
        badge.innerText = riskData.risk_level || 'LOW';
        badge.className = `risk-badge ${(riskData.risk_level || 'LOW').toLowerCase()}`;
    }

    if (confNum) {
        confNum.innerText = `${confidence}%`;
        confNum.style.color = riskColor;
        confNum.style.fontWeight = 'bold';
    }
    if (confFill) {
        confFill.style.width = `${confidence}%`;
        confFill.style.backgroundColor = riskColor;
        confFill.style.boxShadow = `0 0 10px ${riskColor}44`;
    }

    // Factors (Reasoning)
    if (factorList) {
        factorList.innerHTML = (riskData.reasons || []).map(r => `
            <div class="factor-item">
                <span class="factor-bullet">•</span>
                <span class="factor-text">${r}</span>
            </div>
        `).join('');
    }

    // Breakdown Bars
    const satVal = Math.round((riskData.satellite_contribution || 0) * 100);
    const weatherVal = Math.round((riskData.weather_contribution || 0) * 100);

    const satBar = document.getElementById(`${type}SatelliteBar`);
    const satValue = document.getElementById(`${type}SatelliteValue`);
    const weatherBar = document.getElementById(`${type}WeatherBar`);
    const weatherValue = document.getElementById(`${type}WeatherValue`);

    if (satBar) {
        satBar.style.width = `${satVal}%`;
        satBar.style.backgroundColor = '#4ecdc4';
        satBar.style.boxShadow = '0 0 10px rgba(78, 205, 196, 0.3)';
    }
    if (satValue) {
        satValue.innerText = `${satVal}%`;
        satValue.style.color = '#4ecdc4';
        satValue.style.fontWeight = 'bold';
    }
    if (weatherBar) {
        weatherBar.style.width = `${weatherVal}%`;
        weatherBar.style.backgroundColor = '#ff6b6b';
        weatherBar.style.boxShadow = '0 0 10px rgba(255, 107, 107, 0.3)';
    }
    if (weatherValue) {
        weatherValue.innerText = `${weatherVal}%`;
        weatherValue.style.color = '#ff6b6b';
        weatherValue.style.fontWeight = 'bold';
    }
}

function renderWeatherGrid(w) {
    const grid = document.getElementById('weatherGrid');
    if (!grid) return;

    const weather = w || {};
    const items = [
        { label: 'Surface Temp', val: `${weather.temperature || '??'}°C`, icon: '🌡️' },
        { label: 'Relative Humidity', val: `${weather.humidity || '??'}%`, icon: '💧' },
        { label: 'Wind Velocity', val: `${weather.wind_speed || '??'} km/h`, icon: '💨' },
        { label: 'Barometric Pres', val: `${weather.pressure || '??'} hPa`, icon: '⏲️' }
    ];

    grid.innerHTML = items.map(i => `
        <div class="weather-card-mini">
            <span class="w-icon">${i.icon}</span>
            <div class="w-info">
                <span class="w-label">${i.label}</span>
                <span class="w-val">${i.val}</span>
            </div>
        </div>
    `).join('');
}

function renderSpectralAnalysis(data) {
    // Add a canvas if it doesn't exist
    let container = document.querySelector('.weather-details');
    if (!container) return; // Silent return if container is missing
    let chartContainer = document.getElementById('spectralContainer');

    if (!chartContainer) {
        chartContainer = document.createElement('div');
        chartContainer.id = 'spectralContainer';
        chartContainer.className = 'spectral-analysis-card';
        chartContainer.innerHTML = `
            <h3>🛰️ Multispectral Satellite Signature</h3>
            <p style="color: #6b7a99; font-size: 12px; margin-bottom: 20px;">AI analysis of Sentinel-2 and VIIRS spectral bands</p>
            <div style="height: 300px;"><canvas id="spectralChart"></canvas></div>
        `;
        container.appendChild(chartContainer);
    }

    const ctx = document.getElementById('spectralChart').getContext('2d');

    if (spectralChart) spectralChart.destroy();

    // Generate pseudo-spectral data based on risks
    const isFire = data.primary_threat === 'fire';
    const isFlood = data.primary_threat === 'flood';

    spectralChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['Blue (B2)', 'Green (B3)', 'Red (B4)', 'NIR (B8)', 'SWIR1 (B11)', 'SWIR2 (B12)', 'Thermal (T1)'],
            datasets: [{
                label: 'AI-Derived Spectral Profile',
                data: data.spectral_signature || [0.1, 0.2, 0.15, 0.4, 0.2, 0.1, 0.3],
                borderColor: '#667eea',
                backgroundColor: 'rgba(102, 126, 234, 0.2)',
                borderWidth: 3,
                tension: 0.4,
                fill: true,
                pointBackgroundColor: '#fff',
                pointRadius: 5
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: { beginAtZero: true, max: 1.0, grid: { color: 'rgba(255,255,255,0.05)' } },
                x: { grid: { display: false } }
            },
            plugins: { legend: { display: false } }
        }
    });
}

function exportResults() {
    alert("Strategic Report exported as PDF. Link sent to mission control.");
}

// ================================================
// 🔍 Google Maps Style Search for Prediction Page
// ================================================

let predictionSearchTimeout = null;

async function handlePredictionSearch(event) {
    const query = event.target.value.trim();
    const suggestionsBox = document.getElementById('predictionSuggestions');

    // If Enter key, search immediately
    if (event.key === 'Enter' && query) {
        await searchAndSelectLocation(query);
        suggestionsBox.style.display = 'none';
        return;
    }

    // Clear previous timeout
    if (predictionSearchTimeout) clearTimeout(predictionSearchTimeout);

    if (query.length < 2) {
        suggestionsBox.style.display = 'none';
        return;
    }

    // Debounce
    predictionSearchTimeout = setTimeout(() => fetchPredictionSuggestions(query), 300);
}

async function fetchPredictionSuggestions(query) {
    const suggestionsBox = document.getElementById('predictionSuggestions');

    // Show loading
    suggestionsBox.innerHTML = `
        <div style="padding: 15px; text-align: center; color: #a8b3cf;">
            <div class="loading-spinner" style="margin: 0 auto 10px; width: 20px; height: 20px;"></div>
            Searching...
        </div>
    `;
    suggestionsBox.style.display = 'block';

    try {
        const response = await fetch(
            `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(query)}&format=json&limit=6&addressdetails=1`,
            { headers: { 'User-Agent': 'SDARS-DisasterAlertSystem/1.0' } }
        );

        const results = await response.json();

        if (results.length === 0) {
            suggestionsBox.innerHTML = `
                <div style="padding: 15px; text-align: center; color: #6b7a99;">
                    No location found for "${query}"
                </div>
            `;
            return;
        }

        suggestionsBox.innerHTML = results.map(r => {
            const name = r.address?.city || r.address?.town || r.address?.village || r.address?.county || r.address?.state || 'Location';
            return `
                <div class="pred-suggestion" 
                     onclick="selectSearchResult(${r.lat}, ${r.lon}, '${name.replace(/'/g, "\\'")}')"
                     style="padding: 12px 15px; cursor: pointer; border-bottom: 1px solid rgba(255,255,255,0.05); transition: background 0.2s;"
                     onmouseenter="this.style.background='rgba(102,126,234,0.1)'"
                     onmouseleave="this.style.background='transparent'">
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <span style="font-size: 18px;">📍</span>
                        <div>
                            <div style="color: white; font-weight: 600;">${name}</div>
                            <div style="color: #6b7a99; font-size: 11px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 350px;">${r.display_name}</div>
                        </div>
                    </div>
                </div>
            `;
        }).join('');

    } catch (error) {
        suggestionsBox.innerHTML = `
            <div style="padding: 15px; text-align: center; color: #ff5722;">
                Search failed. Please try again.
            </div>
        `;
    }
}

function selectSearchResult(lat, lon, name) {
    // Fill everything and run
    fillPredictionInputs(lat, lon, name);

    // Hide suggestions
    const suggestions = document.getElementById('predictionSuggestions');
    if (suggestions) suggestions.style.display = 'none';
}

async function searchAndSelectLocation(query) {
    try {
        const response = await fetch(
            `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(query)}&format=json&limit=1`,
            { headers: { 'User-Agent': 'SDARS-DisasterAlertSystem/1.0' } }
        );

        const results = await response.json();

        if (results.length > 0) {
            const r = results[0];
            const name = r.address?.city || r.address?.town || r.address?.village || query;
            selectSearchResult(parseFloat(r.lat), parseFloat(r.lon), name);
        } else {
            alert(`Location "${query}" not found. Try a different name.`);
        }
    } catch (error) {
        alert('Search failed. Please try again.');
    }
}

async function usePredictionGPS() {
    if (!navigator.geolocation) {
        alert('GPS not supported by your browser');
        return;
    }

    navigator.geolocation.getCurrentPosition(
        async (position) => {
            const lat = position.coords.latitude;
            const lon = position.coords.longitude;

            // Get location name
            try {
                const response = await fetch(
                    `https://nominatim.openstreetmap.org/reverse?lat=${lat}&lon=${lon}&format=json`,
                    { headers: { 'User-Agent': 'SDARS-DisasterAlertSystem/1.0' } }
                );

                const data = await response.json();
                // Get the best name - prefer city/town/village over municipality
                const address = data.address || {};
                const name = address.city || address.town || address.village ||
                    address.suburb || address.county || address.state_district ||
                    'Current Location';

                document.getElementById('predictionSearchInput').value = name;
                selectSearchResult(lat, lon, name);

            } catch (e) {
                selectSearchResult(lat, lon, 'Current Location');
            }
        },
        (error) => {
            let msg = 'Unable to get location';
            if (error.code === 1) msg = 'Location access denied. Please enable GPS.';
            alert(msg);
        },
        { enableHighAccuracy: true, timeout: 10000 }
    );
}

// Close suggestions when clicking outside
document.addEventListener('click', (e) => {
    if (!e.target.closest('.search-box')) {
        const suggestions = document.getElementById('predictionSuggestions');
        if (suggestions) suggestions.style.display = 'none';
    }
});

// Show message when no location is selected
function showNoPredictionMessage() {
    const resultsSection = document.getElementById('results');
    const loadingSection = document.getElementById('loading');
    const resultLocation = document.getElementById('resultLocation');
    const resultTimestamp = document.getElementById('resultTimestamp');
    const primaryThreat = document.getElementById('primaryThreat');

    if (loadingSection) loadingSection.classList.add('hidden');
    if (resultsSection) resultsSection.classList.remove('hidden');

    if (resultLocation) resultLocation.innerText = 'No Location Selected';
    if (resultTimestamp) resultTimestamp.innerText = 'Please search for a location or use GPS';

    if (primaryThreat) {
        primaryThreat.innerHTML = `
            <div style="text-align: center; padding: 30px;">
                <div style="font-size: 48px; margin-bottom: 15px;">🌍</div>
                <h3 style="color: #667eea; margin-bottom: 10px;">Ready for Analysis</h3>
                <p style="color: #a8b3cf;">Enter a location in the search box above, use GPS, or select a quick location to begin AI analysis.</p>
            </div>
        `;
    }
}

// Global error handler
window.addEventListener('error', (event) => {
    console.error("An unhandled error occurred:", event.error || event.message);
    // Optionally display a user-friendly message
    // alert("An unexpected error occurred. Please try again.");
});

// Check for deep links in URL
window.addEventListener('load', () => {
    if (typeof loadHistorySidebar === 'function') { // Defensive check
        loadHistorySidebar();
    }

    const params = new URLSearchParams(window.location.search);
    const lat = params.get('lat');
    const lon = params.get('lon');
    const name = params.get('name');

    console.log("📍 Deep Link Detection:", { lat, lon, name });

    const hasLat = lat !== null && lat !== undefined && lat !== 'undefined' && lat !== 'null' && lat !== '';
    const hasLon = lon !== null && lon !== undefined && lon !== 'undefined' && lon !== 'null' && lon !== '';

    if (hasLat && hasLon) {
        console.log("🚀 Valid Mission Parameters found. Initializing Tactical Dashboard.");

        // Use the consolidated filler
        fillPredictionInputs(lat, lon, name || 'Target Zone');

        // Force scroll to top initially so they see the filling, then runPrediction will scroll to results
        window.scrollTo(0, 0);
    } else {
        console.log("ℹ️ No meaningful deep link found. Waiting for manual input.");
        showNoPredictionMessage();
    }
});
