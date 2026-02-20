/**
 * SDARS Satellite Visualization - Frontend JavaScript
 * Interactive satellite analysis with multi-layer support
 */

// Global state
const satelliteState = {
    map: null,
    currentLayer: 'TRUE_COLOR',
    currentLat: 19.0760,
    currentLon: 72.8777,
    currentDate: new Date().toISOString().split('T')[0],
    imageOverlay: null,
    thermalMarkers: [],
    chart: null
};

/**
 * Initialize the application
 */
function initSatellite() {
    console.log('🛰️ Initializing Satellite Visualization...');

    // Initialize map
    initMap();

    // Load layer options
    loadLayerOptions();

    // Set today's date
    document.getElementById('dateInput').value = satelliteState.currentDate;

    // Update info overlay
    updateInfoOverlay();

    console.log('✅ Satellite system initialized');
}

/**
 * Initialize Leaflet map
 */
function initMap() {
    // Create map
    satelliteState.map = L.map('satelliteMap', {
        zoomControl: true,
        attributionControl: false
    }).setView([satelliteState.currentLat, satelliteState.currentLon], 10);

    // Add dark tile layer
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        maxZoom: 19,
        subdomains: 'abcd'
    }).addTo(satelliteState.map);

    // Add zoom control
    L.control.zoom({ position: 'bottomright' }).addTo(satelliteState.map);

    // Add scale
    L.control.scale({ position: 'bottomleft' }).addTo(satelliteState.map);

    console.log('🗺️ Map initialized');
}

/**
 * Load available layer options from API
 */
async function loadLayerOptions() {
    try {
        const response = await fetch('http://localhost:8000/api/satellite/layers');
        const data = await response.json();

        if (data.status === 'success') {
            const container = document.getElementById('layerOptions');
            container.innerHTML = '';

            data.layers.forEach(layer => {
                const btn = document.createElement('button');
                btn.className = 'layer-btn';
                if (layer.id === satelliteState.currentLayer) {
                    btn.classList.add('active');
                }

                btn.innerHTML = `
                    <span class="icon">${layer.icon}</span>
                    <div>
                        <strong>${layer.name}</strong><br>
                        <small style="opacity: 0.7">${layer.description}</small>
                    </div>
                `;

                btn.onclick = () => selectLayer(layer.id);
                container.appendChild(btn);
            });

            console.log(`📡 Loaded ${data.layers.length} layer options`);
        }

    } catch (error) {
        console.error('Error loading layers:', error);
        showError('Failed to load layer options');
    }
}

/**
 * Select a satellite layer
 */
function selectLayer(layerId) {
    satelliteState.currentLayer = layerId;

    // Update button states
    document.querySelectorAll('.layer-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.closest('.layer-btn').classList.add('active');

    // Update info overlay
    updateInfoOverlay();

    // Load imagery for new layer
    loadSatelliteImagery();
}

/**
 * Load satellite imagery from API
 */
async function loadSatelliteImagery() {
    showLoading(true);

    try {
        const lat = parseFloat(document.getElementById('latInput').value) || satelliteState.currentLat;
        const lon = parseFloat(document.getElementById('lonInput').value) || satelliteState.currentLon;
        const date = document.getElementById('dateInput').value || satelliteState.currentDate;

        satelliteState.currentLat = lat;
        satelliteState.currentLon = lon;
        satelliteState.currentDate = date;

        const response = await fetch('http://localhost:8000/api/satellite/imagery', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                lat: lat,
                lon: lon,
                date: date,
                layer_type: satelliteState.currentLayer,
                bbox_size: 0.1
            })
        });

        const data = await response.json();

        if (data.status === 'success') {
            displayImagery(data.data);

            // Update map center
            satelliteState.map.setView([lat, lon], 10);

            // Update info
            updateInfoOverlay();

            showSuccess(`Loaded ${satelliteState.currentLayer} imagery`);
        }

    } catch (error) {
        console.error('Error loading imagery:', error);
        showError('Failed to load satellite imagery');
    } finally {
        showLoading(false);
    }
}

/**
 * Display satellite imagery on map
 */
function displayImagery(imageData) {
    // Remove existing overlay
    if (satelliteState.imageOverlay) {
        satelliteState.map.removeLayer(satelliteState.imageOverlay);
    }

    // Calculate bounds from bbox
    const bbox = imageData.bbox;
    const bounds = [[bbox[1], bbox[0]], [bbox[3], bbox[2]]];

    // Add image overlay
    satelliteState.imageOverlay = L.imageOverlay(imageData.image_data, bounds, {
        opacity: 0.8
    }).addTo(satelliteState.map);

    // Fit map to bounds
    satelliteState.map.fitBounds(bounds);

    console.log('🖼️ Imagery displayed on map');
}

/**
 * Calculate and display NDVI
 */
async function calculateNDVI() {
    showLoading(true);

    try {
        const lat = parseFloat(document.getElementById('latInput').value) || satelliteState.currentLat;
        const lon = parseFloat(document.getElementById('lonInput').value) || satelliteState.currentLon;
        const date = document.getElementById('dateInput').value || satelliteState.currentDate;

        const response = await fetch('http://localhost:8000/api/satellite/ndvi', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ lat, lon, date })
        });

        const data = await response.json();

        if (data.status === 'success') {
            displayNDVIResult(data.data);
            showSuccess('NDVI calculated successfully');
        }

    } catch (error) {
        console.error('Error calculating NDVI:', error);
        showError('Failed to calculate NDVI');
    } finally {
        showLoading(false);
    }
}

/**
 * Display NDVI result
 */
function displayNDVIResult(ndviData) {
    const resultSection = document.getElementById('ndviResult');
    const display = document.getElementById('ndviDisplay');

    display.innerHTML = `
        <div style="background: ${ndviData.color}; padding: 20px; border-radius: 12px; text-align: center; margin-bottom: 16px;">
            <div style="font-size: 48px; font-weight: 800; color: white; text-shadow: 0 2px 4px rgba(0,0,0,0.3);">
                ${ndviData.ndvi_value}
            </div>
            <div style="font-size: 14px; color: white; opacity: 0.9; margin-top: 8px;">
                NDVI Value
            </div>
        </div>
        
        <div style="background: rgba(255,255,255,0.05); padding: 16px; border-radius: 10px; margin-bottom: 12px;">
            <div style="color: #8b949e; font-size: 12px; margin-bottom: 6px;">CLASSIFICATION</div>
            <div style="color: white; font-size: 16px; font-weight: 600;">${ndviData.classification}</div>
        </div>
        
        <div style="background: rgba(255,255,255,0.05); padding: 16px; border-radius: 10px; margin-bottom: 12px;">
            <div style="color: #8b949e; font-size: 12px; margin-bottom: 6px;">INTERPRETATION</div>
            <div style="color: white; font-size: 13px; line-height: 1.6;">${ndviData.interpretation}</div>
        </div>
        
        <div style="background: rgba(255,255,255,0.05); padding: 16px; border-radius: 10px;">
            <div style="color: #8b949e; font-size: 12px; margin-bottom: 6px;">LOCATION</div>
            <div style="color: white; font-size: 13px;">${ndviData.location.lat.toFixed(4)}, ${ndviData.location.lon.toFixed(4)}</div>
        </div>
    `;

    resultSection.style.display = 'block';

    // Add marker to map
    L.marker([ndviData.location.lat, ndviData.location.lon], {
        icon: L.divIcon({
            className: 'ndvi-marker',
            html: `<div style="background: ${ndviData.color}; width: 30px; height: 30px; border-radius: 50%; border: 3px solid white; box-shadow: 0 2px 8px rgba(0,0,0,0.3);"></div>`
        })
    }).addTo(satelliteState.map)
        .bindPopup(`<strong>NDVI: ${ndviData.ndvi_value}</strong><br>${ndviData.classification}`);
}

/**
 * Get and display thermal data
 */
async function getThermalData() {
    showLoading(true);

    try {
        const lat = parseFloat(document.getElementById('latInput').value) || satelliteState.currentLat;
        const lon = parseFloat(document.getElementById('lonInput').value) || satelliteState.currentLon;

        const response = await fetch('http://localhost:8000/api/satellite/thermal', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ lat, lon, radius_km: 50 })
        });

        const data = await response.json();

        if (data.status === 'success') {
            displayThermalData(data.data);
            showSuccess(`Found ${data.data.count} thermal hotspots`);
        }

    } catch (error) {
        console.error('Error getting thermal data:', error);
        showError('Failed to get thermal data');
    } finally {
        showLoading(false);
    }
}

/**
 * Display thermal hotspots on map
 */
function displayThermalData(thermalData) {
    // Clear existing markers
    satelliteState.thermalMarkers.forEach(marker => {
        satelliteState.map.removeLayer(marker);
    });
    satelliteState.thermalMarkers = [];

    // Display results
    const resultSection = document.getElementById('thermalResult');
    const display = document.getElementById('thermalDisplay');

    display.innerHTML = `
        <div style="background: rgba(239, 68, 68, 0.1); padding: 16px; border-radius: 10px; border: 1px solid rgba(239, 68, 68, 0.3); margin-bottom: 12px;">
            <div style="font-size: 32px; font-weight: 800; color: #ef4444;">${thermalData.count}</div>
            <div style="color: #8b949e; font-size: 12px; margin-top: 4px;">HOTSPOTS DETECTED</div>
        </div>
        
        ${thermalData.max_brightness > 0 ? `
        <div style="background: rgba(255,255,255,0.05); padding: 12px; border-radius: 8px; margin-bottom: 8px;">
            <div style="color: #8b949e; font-size: 11px;">MAX BRIGHTNESS</div>
            <div style="color: white; font-size: 16px; font-weight: 600;">${thermalData.max_brightness.toFixed(1)}K</div>
        </div>
        
        <div style="background: rgba(255,255,255,0.05); padding: 12px; border-radius: 8px;">
            <div style="color: #8b949e; font-size: 11px;">AVG BRIGHTNESS</div>
            <div style="color: white; font-size: 16px; font-weight: 600;">${thermalData.avg_brightness.toFixed(1)}K</div>
        </div>
        ` : '<div style="color: #8b949e; padding: 16px; text-align: center;">✓ No hotspots detected</div>'}
    `;

    resultSection.style.display = 'block';

    // Add markers to map
    thermalData.hotspots.forEach(hotspot => {
        const marker = L.circleMarker([hotspot.latitude, hotspot.longitude], {
            radius: 8,
            fillColor: '#ef4444',
            color: '#fff',
            weight: 2,
            opacity: 1,
            fillOpacity: 0.8
        }).addTo(satelliteState.map);

        marker.bindPopup(`
            <strong>🔥 Thermal Hotspot</strong><br>
            Brightness: ${hotspot.brightness.toFixed(1)}K<br>
            Confidence: ${hotspot.confidence}<br>
            FRP: ${hotspot.frp.toFixed(1)} MW
        `);

        satelliteState.thermalMarkers.push(marker);
    });
}

/**
 * Show time-series modal
 */
function showTimeSeriesModal() {
    const modal = document.getElementById('timeSeriesModal');
    modal.style.display = 'flex';

    // Set default dates (last 6 months)
    const endDate = new Date();
    const startDate = new Date();
    startDate.setMonth(startDate.getMonth() - 6);

    document.getElementById('tsStartDate').value = startDate.toISOString().split('T')[0];
    document.getElementById('tsEndDate').value = endDate.toISOString().split('T')[0];
}

/**
 * Load time-series data
 */
async function loadTimeSeries() {
    showLoading(true);

    try {
        const lat = parseFloat(document.getElementById('latInput').value) || satelliteState.currentLat;
        const lon = parseFloat(document.getElementById('lonInput').value) || satelliteState.currentLon;
        const startDate = document.getElementById('tsStartDate').value;
        const endDate = document.getElementById('tsEndDate').value;
        const metric = document.getElementById('tsMetric').value;

        const response = await fetch('http://localhost:8000/api/satellite/timeseries', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                lat, lon, start_date: startDate, end_date: endDate, metric
            })
        });

        const data = await response.json();

        if (data.status === 'success') {
            displayTimeSeriesChart(data.data);
            showSuccess('Time-series data loaded');
        }

    } catch (error) {
        console.error('Error loading time-series:', error);
        showError('Failed to load time-series data');
    } finally {
        showLoading(false);
    }
}

/**
 * Display time-series chart
 */
function displayTimeSeriesChart(tsData) {
    const chartContainer = document.getElementById('timeSeriesChart');
    chartContainer.style.display = 'block';

    // Destroy existing chart
    if (satelliteState.chart) {
        satelliteState.chart.destroy();
    }

    // Create chart
    const ctx = document.getElementById('tsCanvas').getContext('2d');
    satelliteState.chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: tsData.dates,
            datasets: [{
                label: tsData.metric,
                data: tsData.values,
                borderColor: '#667eea',
                backgroundColor: 'rgba(102, 126, 234, 0.1)',
                borderWidth: 2,
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    labels: { color: 'white' }
                }
            },
            scales: {
                x: {
                    ticks: { color: '#8b949e' },
                    grid: { color: 'rgba(255,255,255,0.05)' }
                },
                y: {
                    ticks: { color: '#8b949e' },
                    grid: { color: 'rgba(255,255,255,0.1)' }
                }
            }
        }
    });

    // Display statistics
    const statsDiv = document.getElementById('tsStats');
    statsDiv.innerHTML = `
        <div class="stat-item">
            <div class="label">Mean</div>
            <div class="value">${tsData.statistics.mean}</div>
        </div>
        <div class="stat-item">
            <div class="label">Max</div>
            <div class="value">${tsData.statistics.max}</div>
        </div>
        <div class="stat-item">
            <div class="label">Min</div>
            <div class="value">${tsData.statistics.min}</div>
        </div>
        <div class="stat-item">
            <div class="label">Std Dev</div>
            <div class="value">${tsData.statistics.std}</div>
        </div>
    `;
}

/**
 * Show comparison modal
 */
function showCompareModal() {
    const modal = document.getElementById('compareModal');
    modal.style.display = 'flex';

    // Set default dates (1 month apart)
    const date2 = new Date();
    const date1 = new Date();
    date1.setMonth(date1.getMonth() - 1);

    document.getElementById('compareDate1').value = date1.toISOString().split('T')[0];
    document.getElementById('compareDate2').value = date2.toISOString().split('T')[0];
}

/**
 * Load comparison data
 */
async function loadComparison() {
    showLoading(true);

    try {
        const lat = parseFloat(document.getElementById('latInput').value) || satelliteState.currentLat;
        const lon = parseFloat(document.getElementById('lonInput').value) || satelliteState.currentLon;
        const date1 = document.getElementById('compareDate1').value;
        const date2 = document.getElementById('compareDate2').value;

        const response = await fetch('http://localhost:8000/api/satellite/compare', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                lat, lon, date1, date2, layer_type: satelliteState.currentLayer
            })
        });

        const data = await response.json();

        if (data.status === 'success') {
            displayComparison(data.data);
            showSuccess('Comparison loaded');
        }

    } catch (error) {
        console.error('Error loading comparison:', error);
        showError('Failed to load comparison');
    } finally {
        showLoading(false);
    }
}

/**
 * Display comparison results
 */
function displayComparison(compData) {
    const resultDiv = document.getElementById('comparisonResult');
    resultDiv.style.display = 'block';

    // Display images
    document.getElementById('beforeImage').innerHTML = `
        <img src="${compData.before.image.image_data}" alt="Before" style="width: 100%; border-radius: 8px;">
    `;
    document.getElementById('beforeDate').innerHTML = `
        <div style="color: #8b949e; font-size: 12px; margin-top: 8px;">📅 ${compData.before.date}</div>
    `;

    document.getElementById('afterImage').innerHTML = `
        <img src="${compData.after.image.image_data}" alt="After" style="width: 100%; border-radius: 8px;">
    `;
    document.getElementById('afterDate').innerHTML = `
        <div style="color: #8b949e; font-size: 12px; margin-top: 8px;">📅 ${compData.after.date}</div>
    `;

    // Display change detection
    const changes = compData.changes;
    document.getElementById('changeDetection').innerHTML = `
        <h4 style="margin: 0 0 12px 0;">Change Detection Results</h4>
        <div style="background: rgba(255,255,255,0.1); padding: 12px; border-radius: 8px; margin-bottom: 8px;">
            <strong>Significant Change:</strong> ${changes.significant_change ? 'Yes' : 'No'}
        </div>
        <div style="background: rgba(255,255,255,0.1); padding: 12px; border-radius: 8px; margin-bottom: 8px;">
            <strong>Change Percentage:</strong> ${changes.change_percentage}%
        </div>
        <div style="background: rgba(255,255,255,0.1); padding: 12px; border-radius: 8px;">
            <strong>Type:</strong> ${changes.change_type.replace('_', ' ').toUpperCase()}
        </div>
    `;
}

/**
 * Use current location
 */
function useMyLocation() {
    if ('geolocation' in navigator) {
        showLoading(true);

        navigator.geolocation.getCurrentPosition(
            (position) => {
                const lat = position.coords.latitude;
                const lon = position.coords.longitude;

                document.getElementById('latInput').value = lat.toFixed(4);
                document.getElementById('lonInput').value = lon.toFixed(4);

                satelliteState.currentLat = lat;
                satelliteState.currentLon = lon;

                satelliteState.map.setView([lat, lon], 10);

                showSuccess('Location updated');
                showLoading(false);
            },
            (error) => {
                showError('Could not get your location');
                showLoading(false);
            }
        );
    } else {
        showError('Geolocation not supported');
    }
}

/**
 * Set date to today
 */
function setToday() {
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('dateInput').value = today;
    satelliteState.currentDate = today;
}

/**
 * Update info overlay
 */
function updateInfoOverlay() {
    document.getElementById('currentLayer').textContent = satelliteState.currentLayer;
    document.getElementById('currentDate').textContent = satelliteState.currentDate;
}

/**
 * Close modal
 */
function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}

/**
 * Show/hide loading overlay
 */
function showLoading(show) {
    document.getElementById('loadingOverlay').style.display = show ? 'flex' : 'none';
}

/**
 * Show success message
 */
function showSuccess(message) {
    // Simple console log for now
    console.log('✅ ' + message);
    // Could add toast notification here
}

/**
 * Show error message
 */
function showError(message) {
    console.error('❌ ' + message);
    alert(message);
}

// Initialize on page load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initSatellite);
} else {
    initSatellite();
}

// Close modals on background click
document.addEventListener('click', (e) => {
    if (e.target.classList.contains('modal')) {
        e.target.style.display = 'none';
    }
});
