// Global constant
const API_BASE_URL = window.API_BASE_URL || 'http://localhost:8000/api';

// Global state
const zonesState = {
    map: null,
    drawnItems: null,
    currentZone: null,
    zones: [],
    userId: 'default_user',
    drawControl: null,
    editMode: false,
    deleteMode: false
};

/**
 * Initialize the zones page
 */
function initZonesPage() {
    console.log('🎯 Initializing Custom Alert Zones...');

    // Check for Leaflet
    if (typeof L === 'undefined') {
        console.error('Leaflet library not loaded.');
        showError('Map library failed to load. Please check your internet connection.');
        return;
    }

    // Initialize map
    try {
        initMap();
        // Load existing zones
        loadZones();
    } catch (e) {
        console.error("Map initialization failed:", e);
        showError("Map failed to initialize.");
    }


    console.log('✅ Zones page initialized');
}

/**
 * Initialize Leaflet map with drawing tools
 */
function initMap() {
    // Create map
    zonesState.map = L.map('map').setView([20.5937, 78.9629], 5);

    // Define all available terrain layers
    zonesState.terrainLayers = {
        dark: L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
            attribution: '©OpenStreetMap, ©CartoDB',
            subdomains: 'abcd',
            maxZoom: 19
        }),
        satellite: L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
            attribution: 'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EBP, and the GIS User Community'
        }),
        topo: L.tileLayer('https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png', {
            maxZoom: 17,
            attribution: 'Map style: &copy; <a href="https://opentopomap.org">OpenTopoMap</a>'
        }),
        streets: L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; OpenStreetMap'
        })
    };

    zonesState.currentLayerName = 'dark';
    zonesState.terrainLayers.dark.addTo(zonesState.map);

    // Initialize drawn items layer
    zonesState.drawnItems = new L.FeatureGroup();
    zonesState.map.addLayer(zonesState.drawnItems);

    // Initialize draw control
    const drawControl = new L.Control.Draw({
        edit: {
            featureGroup: zonesState.drawnItems,
            edit: false
        },
        draw: {
            polygon: {
                allowIntersection: false,
                shapeOptions: {
                    color: '#667eea',
                    fillColor: '#667eea',
                    fillOpacity: 0.2,
                    weight: 2
                }
            },
            polyline: false,
            rectangle: false,
            circle: false,
            marker: false,
            circlemarker: false
        }
    });

    zonesState.drawControl = drawControl;
    zonesState.map.addControl(drawControl);

    // Listen for zone creation
    zonesState.map.on(L.Draw.Event.CREATED, function (event) {
        const layer = event.layer;
        zonesState.drawnItems.addLayer(layer);
        zonesState.currentZone = layer;

        // Show zone form
        showZoneForm();
    });
}

/**
 * ⭐ Switch Terrain Function
 */
function setTerrain(type) {
    if (!zonesState.terrainLayers[type]) return;

    // Remove current layer
    zonesState.map.removeLayer(zonesState.terrainLayers[zonesState.currentLayerName]);

    // Add new layer
    zonesState.terrainLayers[type].addTo(zonesState.map);
    zonesState.currentLayerName = type;

    // Update UI buttons
    document.querySelectorAll('.terrain-btn').forEach(btn => btn.classList.remove('active'));
    const activeBtn = document.querySelector(`.terrain-btn[onclick*="${type}"]`);
    if (activeBtn) activeBtn.classList.add('active');

    if (typeof showSuccess === 'function') {
        showSuccess(`Changed monitoring view to ${type.toUpperCase()}`);
    }
}

/**
 * Start drawing mode
 */
function startDrawing() {
    // Activate draw button
    document.querySelectorAll('.tool-btn').forEach(btn => btn.classList.remove('active'));
    document.getElementById('drawPolygonBtn').classList.add('active');

    zonesState.editMode = false;
    zonesState.deleteMode = false;

    // Trigger new polygon
    new L.Draw.Polygon(zonesState.map, zonesState.drawControl.options.draw.polygon).enable();
}

/**
 * Toggle edit mode
 */
function toggleEdit() {
    document.querySelectorAll('.tool-btn').forEach(btn => btn.classList.remove('active'));
    document.getElementById('editZoneBtn').classList.add('active');

    zonesState.editMode = true;
    zonesState.deleteMode = false;

    showSuccess('Click on a zone to edit it');
}

/**
 * Toggle delete mode
 */
function toggleDelete() {
    document.querySelectorAll('.tool-btn').forEach(btn => btn.classList.remove('active'));
    document.getElementById('deleteZoneBtn').classList.add('active');

    zonesState.editMode = false;
    zonesState.deleteMode = true;

    showSuccess('Click on a zone to delete it');
}

/**
 * Show zone form
 */
function showZoneForm() {
    document.getElementById('zoneForm').style.display = 'block';
    document.getElementById('zoneName').focus();
}

/**
 * Save zone
 */
async function saveZone() {
    const name = document.getElementById('zoneName').value.trim();
    const saveBtn = document.querySelector('.btn-primary[onclick="saveZone()"]');

    if (!name) {
        showError('Please enter a zone name');
        return;
    }

    if (!zonesState.currentZone) {
        showError('No zone drawn. Please draw a zone first.');
        return;
    }

    // Disable button to prevent double-clicks during synchronous verification
    if (saveBtn) {
        saveBtn.disabled = true;
        saveBtn.innerHTML = '🛰️ Establishing Link...';
    }

    // Get coordinates
    const coordinates = zonesState.currentZone.getLatLngs()[0].map(latLng => [latLng.lat, latLng.lng]);

    // Get form values
    const severityThreshold = document.getElementById('severityThreshold').value;
    const channels = Array.from(document.querySelectorAll('.checkbox-group input:checked'))
        .map(input => input.value);

    // ⭐ Get custom emails
    const emailsRaw = document.getElementById('recipientEmails').value;
    const recipientEmails = emailsRaw ? emailsRaw.split(',').map(e => e.trim()).filter(e => e) : [];

    // Create zone object
    const zone = {
        name: name,
        coordinates: coordinates,
        severity_threshold: severityThreshold,
        notification_channels: channels,
        recipient_emails: recipientEmails,
        user_id: 'zone_creator'
    };

    try {
        // Save to Backend
        const response = await fetch(`${API_BASE_URL}/zones/create`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(zone)
        });

        if (!response.ok) throw new Error('Failed to save to database');

        const result = await response.json();
        const v = result.verification || {};

        // Re-load all zones to get the server-side ID and state
        await loadZones();

        // Detailed Feedback based on Active Verification
        if (v.status === 'success') {
            if (v.failure_count > 0) {
                showSuccess(`Zone established! 📡 ${v.success_count} emails verified. ⚠ ${v.failure_count} delivery failures detected.`);
            } else {
                showSuccess(`Tactical Zone "${name}" established and verified! 📡 All target recipients notified.`);
            }
        } else if (v.status === 'skipped') {
            showSuccess(`Tactical Zone "${name}" established! 📡 No verification emails were required.`);
        } else if (v.status === 'error') {
            showError(`Zone saved, but Verification System failed: ${v.message}`);
        } else {
            showSuccess(`Zone "${name}" saved (Monitoring Link Active).`);
        }

        // Clean up UI and drawing
        cancelZone();

        // Restore button
        if (saveBtn) {
            saveBtn.disabled = false;
            saveBtn.innerHTML = '💾 Save Zone';
        }

    } catch (error) {
        console.error('Error saving zone:', error);
        showError('Failed to establish tactical zone link: ' + error.message);

        // Re-enable button on error
        if (saveBtn) {
            saveBtn.disabled = false;
            saveBtn.innerHTML = '💾 Save Zone';
        }
    }
}

/**
 * Cancel zone creation
 */
function cancelZone() {
    if (zonesState.currentZone) {
        zonesState.drawnItems.removeLayer(zonesState.currentZone);
    }

    document.getElementById('zoneForm').style.display = 'none';
    document.getElementById('zoneName').value = '';
    document.getElementById('recipientEmails').value = ''; // ⭐ Added
    zonesState.currentZone = null;
}

/**
 * Load saved zones
 */
async function loadZones() {
    try {
        const response = await fetch(`${API_BASE_URL}/zones`);
        if (!response.ok) throw new Error('Failed to fetch zones');

        const result = await response.json();
        zonesState.zones = result.zones;

        // Clear existing layers to avoid duplicates
        if (zonesState.drawnItems) {
            zonesState.drawnItems.clearLayers();
        }

        // Draw zones on map
        zonesState.zones.forEach(zone => {
            const latLngs = zone.coordinates.map(coord => [coord[0], coord[1]]);
            const color = getSeverityColor(zone.severity_threshold);

            const polygon = L.polygon(latLngs, {
                color: color,
                fillColor: color,
                fillOpacity: 0.2,
                weight: 2
            });

            polygon.zoneData = zone;
            polygon.on('click', function () {
                if (zonesState.deleteMode) {
                    deleteZone(zone.zone_id);
                } else if (zonesState.editMode) {
                    editZone(zone.zone_id);
                } else {
                    showZoneDetails(zone);
                }
            });

            zonesState.drawnItems.addLayer(polygon);
        });

        displayZones();

    } catch (error) {
        console.error('Error loading zones:', error);
        // Load from local as secondary source
        const localZones = localStorage.getItem('sdars_zones');
        if (localZones) {
            zonesState.zones = JSON.parse(localZones);
            displayZones();
        }
    }
}

/**
 * Display zones list
 */
function displayZones() {
    const zonesList = document.getElementById('zonesList');
    const zoneCount = document.getElementById('zoneCount');

    zoneCount.textContent = zonesState.zones.length;

    if (zonesState.zones.length === 0) {
        zonesList.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">🗺️</div>
                <p>No zones created yet</p>
                <small>Draw a zone on the map to get started</small>
            </div>
        `;
        return;
    }

    zonesList.innerHTML = zonesState.zones.map(zone => {
        const emails = zone.recipient_emails && zone.recipient_emails.length > 0
            ? zone.recipient_emails.join(', ')
            : '<span style="color:#555">None set</span>';

        return `
        <div class="zone-item ${zone.severity_threshold.toLowerCase()}" data-zone-id="${zone.zone_id}">
            <div class="zone-item-header">
                <div class="zone-name">${zone.name}</div>
                <div class="zone-actions">
                    <button class="zone-action-btn" onclick="flyToZone('${zone.zone_id}')" title="Locate">📍</button>
                    <button class="zone-action-btn" onclick="deleteZone('${zone.zone_id}')" title="Delete">🗑️</button>
                    <a href="alerts.html?zone=${encodeURIComponent(zone.name)}&zoneId=${zone.zone_id}" class="zone-link-btn" title="View Alerts" style="text-decoration: none; font-size: 14px;">🚨</a>
                </div>
            </div>

            <div class="zone-meta">
                <span>⚡ ${zone.severity_threshold}</span>
            </div>

            <div class="zone-emails" style="font-size: 11px; color: #6b7a99; margin-top: 8px; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 6px;">
                📧 <strong style="color:#a8b3cf">Alert emails:</strong> ${emails}
            </div>
        </div>
    `}).join('');
}

/**
 * Fly to zone on map
 */
function flyToZone(zoneId) {
    const numericId = parseInt(zoneId);
    const zone = zonesState.zones.find(z => parseInt(z.zone_id) === numericId);
    if (!zone) return;

    // Calculate center of polygon
    const lats = zone.coordinates.map(coord => coord[0]);
    const lons = zone.coordinates.map(coord => coord[1]);
    const centerLat = lats.reduce((a, b) => a + b) / lats.length;
    const centerLon = lons.reduce((a, b) => a + b) / lons.length;

    zonesState.map.flyTo([centerLat, centerLon], 13);
}

/**
 * Edit zone
 */
function editZone(zoneId) {
    showSuccess('Zone editing coming soon!');
    // TODO: Implement zone editing
}

/**
 * Delete zone
 */
async function deleteZone(zoneId) {
    if (!confirm('Are you sure you want to delete this zone from the AI Monitor?')) {
        return;
    }

    // Convert to string for consistent comparison
    const targetId = String(zoneId);
    const isLocal = targetId.startsWith('local_');

    if (!isLocal) {
        try {
            const response = await fetch(`${API_BASE_URL}/zones/${targetId}`, {
                method: 'DELETE'
            });

            if (!response.ok) {
                // If 404, it's already gone, so just proceed to remove locally
                if (response.status !== 404) {
                    throw new Error('Delete failed');
                }
            }
            showSuccess('Zone decommissioned successfully');
        } catch (error) {
            console.error('Delete error:', error);
            showError('Database sync failed. Removing locally.');
        }
    } else {
        showSuccess('Local zone removed');
    }

    // Remove from array (String comparison to handle both int and string IDs)
    zonesState.zones = zonesState.zones.filter(z => String(z.zone_id) !== targetId);

    // Remove from map
    zonesState.drawnItems.eachLayer(layer => {
        if (layer.zoneData && String(layer.zoneData.zone_id) === targetId) {
            zonesState.drawnItems.removeLayer(layer);
        }
    });

    // Update display
    displayZones();
}


/**
 * Show zone details
 */
function showZoneDetails(zone) {
    const emails = zone.recipient_emails && zone.recipient_emails.length > 0
        ? zone.recipient_emails.join('\n  • ')
        : 'None — no alert emails set for this zone.';
    alert(`Zone: ${zone.name}\nSeverity Threshold: ${zone.severity_threshold}\nChannels: ${zone.notification_channels.join(', ')}\n\nAlert Emails:\n  • ${emails}`);
}

/**
 * Clear all drawings
 */
function clearAll() {
    if (confirm('Clear all drawings? (Saved zones will not be affected)')) {
        if (zonesState.currentZone && !zonesState.currentZone.zoneData) {
            zonesState.drawnItems.removeLayer(zonesState.currentZone);
            zonesState.currentZone = null;
        }
        document.getElementById('zoneForm').style.display = 'none';
    }
}

/**
 * Locate me
 */
function locateMe() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            position => {
                const { latitude, longitude } = position.coords;
                zonesState.map.flyTo([latitude, longitude], 13);

                L.marker([latitude, longitude])
                    .addTo(zonesState.map)
                    .bindPopup('📍 You are here')
                    .openPopup();
            },
            error => {
                showError('Unable to get your location');
            }
        );
    } else {
        showError('Geolocation is not supported by your browser');
    }
}

/**
 * Get severity color
 */
function getSeverityColor(severity) {
    const colors = {
        'LOW': '#3b82f6',
        'MEDIUM': '#f59e0b',
        'HIGH': '#ef4444',
        'CRITICAL': '#dc2626'
    };
    return colors[severity] || '#667eea';
}

/**
 * Show success message
 */
function showSuccess(message) {
    const toast = document.createElement('div');
    toast.className = 'toast-notification success';
    toast.innerHTML = `
        <div class="toast-icon">✅</div>
        <div class="toast-message">${message}</div>
    `;

    document.body.appendChild(toast);
    setTimeout(() => toast.classList.add('show'), 10);

    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

/**
 * Show error message
 */
function showError(message) {
    const toast = document.createElement('div');
    toast.className = 'toast-notification error';
    toast.innerHTML = `
        <div class="toast-icon">❌</div>
        <div class="toast-message">${message}</div>
    `;

    document.body.appendChild(toast);
    setTimeout(() => toast.classList.add('show'), 10);

    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

// Initialize on page load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initZonesPage);
} else {
    initZonesPage();
}

// Close modal on background click
document.addEventListener('click', (e) => {
    if (e.target.id === 'preferencesModal') {
        closePreferences();
    }
});
