/**
 * SDARS Unified Navigation System
 * Advanced routing with disaster-aware probing and strategic recovery hubs
 */

let map;
let routingControl;
let geocoder;
let markers = [];
let userCoords = null;
let allRoutes = [];
let activeRouteIndex = 0;
let routeLayers = [];
let terrainLayers = {};
let currentLayerName = 'dark';
let shelterMarkers = [];
let hazardMarkers = [];
let roadMarkers = [];

document.addEventListener('DOMContentLoaded', () => {
    initMap();
    setupGeocoders();
    toggleRoadStatuses(true);
});

function initMap() {
    map = L.map('map', { zoomControl: false, attributionControl: false }).setView([20.5937, 78.9629], 5);
    terrainLayers = {
        dark: L.layerGroup([
            L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}', { maxZoom: 16 }),
            L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Reference/MapServer/tile/{z}/{y}/{x}', { maxZoom: 16 })
        ]),
        satellite: L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'),
        terrain: L.tileLayer('https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png', { maxZoom: 17 }),
        streets: L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png')
    };
    terrainLayers.dark.addTo(map);
    L.control.zoom({ position: 'bottomright' }).addTo(map);
}

function setTerrain(type) {
    if (!terrainLayers[type]) return;
    map.removeLayer(terrainLayers[currentLayerName]);
    terrainLayers[type].addTo(map);
    currentLayerName = type;
    document.querySelectorAll('.terrain-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelector(`.terrain-btn[onclick*="${type}"]`)?.classList.add('active');
    if (window.showSuccess) showSuccess(`Terrain: ${type.toUpperCase()}`);
}

function setupGeocoders() { geocoder = L.Control.Geocoder.nominatim(); }

async function calculateSafeRoute() {
    const startText = document.getElementById('startInput').value;
    const endText = document.getElementById('endInput').value;
    const navBtn = document.querySelector('.btn-primary');

    if (!startText || !endText) return alert("Please enter both starting point and destination.");

    navBtn.disabled = true;
    navBtn.innerHTML = `⌛ Searching...`;
    document.getElementById('emptyState').style.display = 'none';

    try {
        const [startPoint, endPoint] = await Promise.all([resolveLocation(startText), resolveLocation(endText)]);
        if (!startPoint || !endPoint) {
            navBtn.disabled = false;
            navBtn.innerHTML = `🚀 Start Navigation`;
            return alert("Location not found.");
        }

        if (routingControl) map.removeControl(routingControl);

        // Clear previous state
        routeLayers.forEach(l => map.removeLayer(l));
        routeLayers = [];
        clearMarkers('route-location');
        clearShelterMarkers();
        clearHazardMarkers();

        // Add markers
        addMarker(startPoint, 'A', '#10b981', 'Start Point', startText);
        addMarker(endPoint, 'B', '#ef4444', 'Destination', endText);

        routingControl = L.Routing.control({
            waypoints: [L.latLng(startPoint.lat, startPoint.lng), L.latLng(endPoint.lat, endPoint.lng)],
            routeWhileDragging: false,
            addWaypoints: false,
            show: false,
            createMarker: () => null,
            router: L.Routing.osrmv1({
                serviceUrl: 'https://routing.openstreetmap.de/routed-car/route/v1',
                alternatives: 3,
                steps: true,
                overview: 'full'
            }),
            lineOptions: { styles: [{ color: '#6366f1', opacity: 0, weight: 0 }] }
        }).addTo(map);

        routingControl.on('routesfound', async function (e) {
            navBtn.disabled = false;
            navBtn.innerHTML = `🚀 Start Navigation`;
            allRoutes = e.routes;
            activeRouteIndex = 0;

            const routeColors = ['#6366f1', '#9333ea', '#14b8a6'];
            allRoutes.forEach((route, index) => {
                const polyline = L.polyline(route.coordinates.map(c => [c.lat, c.lng]), {
                    color: routeColors[index] || '#6b7a99',
                    weight: 7,
                    opacity: index === 0 ? 0.9 : 0.3,
                    className: `route-polyline`
                }).addTo(map).on('click', () => switchToRoute(index));
                routeLayers.push(polyline);
            });

            displayRouteOptions(allRoutes);
            displayRouteDetails(allRoutes[0]);
            map.fitBounds(L.latLngBounds(allRoutes[0].coordinates), { padding: [50, 50] });

            // Run Analysis instantly on active route
            analyzeAllRoutes();

            // Auto-load hazards if checked
            if (document.getElementById('toggleHazards')?.checked) toggleHazards(true);
            if (document.getElementById('toggleRoads')?.checked) toggleRoadStatuses(true);
        });

        routingControl.on('routingerror', function (err) {
            console.warn("Routing notice:", err);
            navBtn.disabled = false;
            navBtn.innerHTML = `🚀 Start Navigation`;
        });

    } catch (err) {
        console.error("Navigation error:", err);
        navBtn.disabled = false;
        navBtn.innerHTML = `🚀 Start Navigation`;
    }
}

async function analyzeAllRoutes() {
    updateMapStatus('Probing route corridors for AI disaster threats...', 'warning');
    if (!allRoutes || allRoutes.length === 0) return;

    // Immediately analyze the selected route first for sub-second UI feedback
    const activeRoute = allRoutes[activeRouteIndex];
    if (activeRoute) {
        const scoreData = await performRouteAnalysis(activeRoute);
        updateRouteBadge(activeRouteIndex, scoreData);
        displaySafetyDetails(scoreData);
    }

    // Process alternatives asynchronously in background
    for (let i = 0; i < allRoutes.length; i++) {
        if (i !== activeRouteIndex) {
            performRouteAnalysis(allRoutes[i]).then(data => updateRouteBadge(i, data));
        }
    }
}

async function performRouteAnalysis(route) {
    try {
        const coords = route.coordinates;
        // Sample points for backend analysis
        const points = [];
        const step = Math.ceil(coords.length / 10);
        for (let i = 0; i < coords.length; i += step) points.push({ lat: coords[i].lat, lon: coords[i].lng });

        const resp = await fetch(`${API_BASE_URL}/routes/analyze`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                start_lat: coords[0].lat, start_lon: coords[0].lng,
                end_lat: coords[coords.length - 1].lat, end_lon: coords[coords.length - 1].lng,
                route_points: points
            })
        });
        return resp.ok ? await resp.json() : null;
    } catch (e) { return null; }
}

let allRouteAnalyses = [];

function updateRouteBadge(index, data) {
    allRouteAnalyses[index] = data;
    const badge = document.getElementById(`safety-badge-${index}`);
    if (!badge || !data) return;
    const score = data.safety_score;
    const hasBlocked = data.blocked_roads && data.blocked_roads.length > 0;
    
    if (hasBlocked) {
        badge.className = 'route-safety-badge danger';
        badge.textContent = '⛔ Road Blocked';
    } else {
        badge.className = `route-safety-badge ${score > 80 ? 'safe' : score > 50 ? 'warning' : 'danger'}`;
        badge.textContent = score > 80 ? '✓ Safe' : score > 50 ? '⚠ Caution' : '⛔ High Risk';
    }
}

function displaySafetyDetails(data) {
    const indicator = document.getElementById('safetyIndicator');
    const detourBox = document.getElementById('detourNotice');
    if (!indicator || !data) return;
    
    const hasBlocked = data.blocked_roads && data.blocked_roads.length > 0;
    const isSafe = data.safety_score > 80 && !hasBlocked;
    
    indicator.className = `safety-indicator ${isSafe ? 'safe' : 'danger'}`;
    indicator.innerHTML = isSafe 
        ? `✅ ROUTE SECURE: No disaster risks detected.` 
        : hasBlocked 
            ? `🛑 BLOCKED CORRIDOR AVOIDED: Detour engaged!` 
            : `⚠️ DANGER: Hazard zones detected on path!`;
            
    updateMapStatus(
        isSafe ? 'Path Verified Safe' : hasBlocked ? 'DETOUR ACTIVE: Blocked Road Detected' : 'CRISIS ALERT: Hazards Intercepted', 
        isSafe ? 'success' : 'danger'
    );

    if (detourBox) {
        if (hasBlocked) {
            detourBox.style.display = 'block';
            detourBox.innerHTML = `
                <div style="font-weight: 700; color: #f87171; display: flex; align-items: center; gap: 6px; margin-bottom: 6px;">
                    <span>🛑</span> ROADWAY IMPASSIBLE — DETOUR ROUTING ENGAGED
                </div>
                ${data.blocked_roads.map(b => `
                    <div style="background: rgba(0,0,0,0.25); border-left: 3px solid #ef4444; padding: 6px 8px; margin-bottom: 6px; border-radius: 4px;">
                        <strong style="color: #fff;">${b.name} (${b.status})</strong>: <span style="color: #cbd5e1;">${b.reason}</span>
                        <div style="color: #38bdf8; font-weight: 600; margin-top: 4px; font-size: 11px;">
                            ↪ Recommended Detour: ${b.detour}
                        </div>
                    </div>
                `).join('')}
            `;
        } else {
            detourBox.style.display = 'none';
        }
    }
}

function switchToRoute(index) {
    if (index === activeRouteIndex) return;
    activeRouteIndex = index;
    document.querySelectorAll('.route-option-card').forEach((c, i) => c.classList.toggle('active', i === index));
    routeLayers.forEach((l, i) => l.setStyle({ opacity: i === index ? 0.9 : 0.3, weight: i === index ? 7 : 5 }));
    displayRouteDetails(allRoutes[index]);
    if (allRouteAnalyses[index]) {
        displaySafetyDetails(allRouteAnalyses[index]);
    }
    map.fitBounds(L.latLngBounds(allRoutes[index].coordinates), { padding: [50, 50] });
}

// Real-Time Road Status Layer (Sprint 4: Evacuation Road Telemetry)
async function toggleRoadStatuses(show) {
    if (!show) return clearRoadMarkers();
    try {
        const resp = await fetch(`${API_BASE_URL}/roads/status`);
        if (!resp.ok) return;
        const data = await resp.json();
        clearRoadMarkers();
        data.roads.forEach(r => {
            const isBlocked = r.status === 'BLOCKED';
            const isWaterlogged = r.status === 'WATERLOGGED';
            const isLandslide = r.status === 'LANDSLIDE';
            const color = isBlocked ? '#ef4444' : isWaterlogged ? '#0284c7' : isLandslide ? '#ea580c' : '#10b981';
            const iconChar = isBlocked ? '🛑' : isWaterlogged ? '🌊' : isLandslide ? '⛰️' : '🚗';
            
            const icon = L.divIcon({
                className: 'road-status-marker',
                html: `<div style="background: ${color}; color: white; width: 30px; height: 30px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 15px; box-shadow: 0 0 12px ${color}; border: 2px solid #fff; cursor: pointer;">${iconChar}</div>`,
                iconSize: [30, 30],
                iconAnchor: [15, 15]
            });

            const m = L.marker([r.latitude, r.longitude], { icon }).addTo(map).bindPopup(`
                <div style="font-family: 'Inter', sans-serif; min-width: 220px; color: #fff;">
                    <div style="color: ${color}; font-size: 13px; font-weight: 700; margin-bottom: 4px;">${iconChar} ${r.status} CORRIDOR</div>
                    <strong style="color: #fff; font-size: 13px;">${r.name}</strong><br>
                    <div style="color: #94a3b8; font-size: 11px; margin-top: 4px;">${r.reason}</div>
                    ${r.detour ? `<div style="margin-top: 8px; padding: 6px 8px; background: rgba(56,189,248,0.12); border-left: 3px solid #38bdf8; border-radius: 4px; font-size: 11px; color: #38bdf8;"><strong>↪ Tactical Detour:</strong> ${r.detour}</div>` : ''}
                </div>
            `);
            roadMarkers.push(m);
        });
    } catch (e) {
        console.error('Road status load error:', e);
    }
}

function clearRoadMarkers() {
    roadMarkers.forEach(m => map.removeLayer(m));
    roadMarkers = [];
}

// Support Functions
function clearMarkers(type) {
    markers = markers.filter(m => {
        if (m.options?.markerType === type) { map.removeLayer(m); return false; }
        return true;
    });
}

function addMarker(pt, label, color, title, text) {
    const icon = L.icon({
        iconUrl: 'data:image/svg+xml;base64,' + btoa(`<svg xmlns="http://www.w3.org/2000/svg" width="25" height="41"><path fill="${color}" stroke="#fff" stroke-width="2" d="M12.5 0C5.6 0 0 5.6 0 12.5c0 2 .5 3.9 1.3 5.5l10.4 21.2a1 1 0 001.6 0l10.4-21.2c.8-1.6 1.3-3.9 1.3-5.5C25 5.6 19.4 0 12.5 0z"/><circle fill="#fff" cx="12.5" cy="12.5" r="5"/><text x="12.5" y="16" font-family="Arial" font-size="10" font-weight="bold" fill="${color}" text-anchor="middle">${label}</text></svg>`),
        iconSize: [25, 41], iconAnchor: [12, 41]
    });
    const m = L.marker([pt.lat, pt.lng], { icon, markerType: 'route-location' }).addTo(map).bindPopup(`<b>${title}</b><br>${text}`);
    markers.push(m);
}

// Shelter & Hazard Logic (Merged from enhanced)
async function toggleShelters(show) {
    if (!show) return clearShelterMarkers();
    updateMapStatus('Scanning for emergency recovery hubs...', 'warning');
    const center = map.getCenter();
    try {
        const resp = await fetch(`${API_BASE_URL}/shelters/nearby?lat=${center.lat}&lon=${center.lng}&radius_km=30&limit=20`);
        const data = await resp.json();
        data.nearest_shelters.forEach(s => {
            const m = L.marker(s.coords, { zIndexOffset: 500 }).addTo(map).bindPopup(`<b>${s.name}</b><br>${s.type.toUpperCase()}<br>${s.address}`);
            shelterMarkers.push(m);
        });
        updateMapStatus(`${data.nearest_shelters.length} facilities intercepted`, 'success');
    } catch (e) { }
}

function clearShelterMarkers() { shelterMarkers.forEach(m => map.removeLayer(m)); shelterMarkers = []; }

async function toggleHazards(show) {
    if (!show) return clearHazardMarkers();
    if (!allRoutes[activeRouteIndex]) return;
    const r = allRoutes[activeRouteIndex];
    const start = r.coordinates[0];
    const end = r.coordinates[r.coordinates.length - 1];
    try {
        const resp = await fetch(`${API_BASE_URL}/route/hazards?start_lat=${start.lat}&start_lon=${start.lng}&end_lat=${end.lat}&end_lon=${end.lng}`);
        const data = await resp.json();
        data.fire_hotspots.forEach(h => {
            const c = L.circle([h.latitude, h.longitude], { radius: 5000, color: '#ff4444', fillOpacity: 0.4 }).addTo(map).bindPopup('🔥 Fire Hotspot');
            hazardMarkers.push(c);
        });
    } catch (e) { }
}

function clearHazardMarkers() { hazardMarkers.forEach(m => map.removeLayer(m)); hazardMarkers = []; }

function updateMapStatus(msg, type) {
    const el = document.getElementById('mapStatus');
    if (el) el.innerHTML = `<span style="color: var(--accent-${type})">●</span> <span>${msg}</span>`;
}

async function resolveLocation(text) {
    if (!text) return null;
    let clean = text.trim();

    // 1. Normalize coordinates typed with spaces instead of dots (e.g. "20 17593, 85 61965" -> "20.17593, 85.61965")
    if (clean.match(/\d+\s+\d{3,}/)) {
        clean = clean.replace(/(\d+)\s+(\d{3,})/g, '$1.$2');
    }

    // 2. Check if direct coordinates match
    const coordMatch = clean.match(/^[-+]?[\d\.]+\s*,\s*[-+]?[\d\.]+$/);
    if (coordMatch) {
        const p = clean.split(',');
        const lat = parseFloat(p[0].trim());
        const lng = parseFloat(p[1].trim());
        if (!isNaN(lat) && !isNaN(lng) && lat >= -90 && lat <= 90 && lng >= -180 && lng <= 180) {
            return { lat, lng };
        }
    }

    // 3. Smart local aliases for instant resolution without any API lag
    const lower = clean.toLowerCase().trim();
    const cityAliases = {
        // Cuttack
        'chauliaganj': { lat: 20.4584, lng: 85.9091 },
        'badambadi': { lat: 20.4530, lng: 85.8670 },
        'ranihat': { lat: 20.4680, lng: 85.8810 },
        'college square': { lat: 20.4625, lng: 85.8920 },
        'manglabag': { lat: 20.4695, lng: 85.8870 },
        'scb medical': { lat: 20.4690, lng: 85.8880 },
        'scb': { lat: 20.4690, lng: 85.8880 },
        'jobra': { lat: 20.4720, lng: 85.8990 },
        'madhupatna': { lat: 20.4480, lng: 85.8920 },
        'link road': { lat: 20.4450, lng: 85.8780 },
        'cda': { lat: 20.4750, lng: 85.8350 },
        'bidanasi': { lat: 20.4760, lng: 85.8230 },
        'khannagar': { lat: 20.4430, lng: 85.8710 },
        'choudwar': { lat: 20.5280, lng: 85.9080 },
        'jagatpur': { lat: 20.4980, lng: 85.9250 },
        'cuttack': { lat: 20.4625, lng: 85.8828 },
        // Bhubaneswar
        'patia': { lat: 20.3540, lng: 85.8180 },
        'kiit': { lat: 20.3533, lng: 85.8178 },
        'nayapalli': { lat: 20.2980, lng: 85.8120 },
        'jaydev vihar': { lat: 20.3020, lng: 85.8240 },
        'saheed nagar': { lat: 20.2910, lng: 85.8450 },
        'rasulgarh': { lat: 20.2980, lng: 85.8640 },
        'chandrasekharpur': { lat: 20.3250, lng: 85.8190 },
        'khandagiri': { lat: 20.2580, lng: 85.7760 },
        'baramunda': { lat: 20.2780, lng: 85.7980 },
        'master canteen': { lat: 20.2680, lng: 85.8410 },
        'samantarapur': { lat: 20.2350, lng: 85.8420 },
        'aiims': { lat: 20.2310, lng: 85.7780 },
        'bhubaneswar': { lat: 20.2961, lng: 85.8245 },
        'bhuban': { lat: 20.2961, lng: 85.8245 },
        'bbsr': { lat: 20.2961, lng: 85.8245 },
        // Odisha
        'puri': { lat: 19.8135, lng: 85.8312 },
        'konark': { lat: 19.8876, lng: 86.0945 },
        'paradeep': { lat: 20.3164, lng: 86.6114 },
        'balasore': { lat: 21.4934, lng: 86.9135 },
        'berhampur': { lat: 19.3149, lng: 84.7941 },
        'sambalpur': { lat: 21.4669, lng: 83.9812 },
        'rourkela': { lat: 22.2604, lng: 84.8536 },
        'angul': { lat: 20.8400, lng: 85.1010 },
        'jajpur': { lat: 20.8520, lng: 86.3310 },
        'kendrapara': { lat: 20.5020, lng: 86.4220 },
        'khurda': { lat: 20.1880, lng: 85.6210 },
        'jatni': { lat: 20.1650, lng: 85.7060 },
        // Indian Metros
        'delhi': { lat: 28.6139, lng: 77.2090 },
        'mumbai': { lat: 19.0760, lng: 72.8777 },
        'kolkata': { lat: 22.5726, lng: 88.3639 },
        'chennai': { lat: 13.0827, lng: 80.2707 },
        'bangalore': { lat: 12.9716, lng: 77.5946 },
        'bengaluru': { lat: 12.9716, lng: 77.5946 },
        'hyderabad': { lat: 17.3850, lng: 78.4867 }
    };
    if (cityAliases[lower]) return cityAliases[lower];

    // 4. Backend multi-tier search (Gazetteer + Open-Meteo + Nominatim)
    try {
        const res = await fetch(`${API_BASE_URL}/search/${encodeURIComponent(clean)}`);
        if (res.ok) {
            const data = await res.json();
            if (data.found) return { lat: data.lat, lng: data.lon };
        }
    } catch (e) { console.warn('Backend search failed:', e); }

    // 5. Final fallback: Leaflet Nominatim geocoder
    return new Promise(r => {
        geocoder.geocode(clean, res => r(res?.[0]?.center || null));
        setTimeout(() => r(null), 4000);
    });
}

function displayRouteDetails(route) {
    document.getElementById('routeDetails').style.display = 'block';
    const dist = (route.summary.totalDistance / 1000).toFixed(1);
    const time = Math.round(route.summary.totalTime / 60);
    document.getElementById('travelDist').innerText = `${dist} km`;
    document.getElementById('travelTime').innerText = time > 60 ? `${Math.floor(time / 60)}h ${time % 60}m` : `${time} min`;
    const list = document.getElementById('navigationSteps');
    list.innerHTML = route.instructions.map(i => `<li class="step-item"><div class="step-desc">${i.text} <small>(${Math.round(i.distance)}m)</small></div></li>`).join('');
}

function displayRouteOptions(routes) {
    const container = document.getElementById('routeOptionsContainer');
    document.getElementById('routeOptions').style.display = routes.length > 1 ? 'block' : 'none';
    container.innerHTML = routes.map((r, i) => `
        <div class="route-option-card ${i === 0 ? 'active' : ''}" onclick="switchToRoute(${i})">
            <div class="route-option-info">
                <div class="route-option-title">Route ${i + 1}</div>
                <div class="route-option-meta">⏱️ ${Math.round(r.summary.totalTime / 60)}m | 📏 ${(r.summary.totalDistance / 1000).toFixed(1)}km</div>
            </div>
            <div class="route-safety-badge analyzing" id="safety-badge-${i}">Analyzing...</div>
        </div>
    `).join('');
}

// Use My Location
function useMyLocation() {
    if (!navigator.geolocation) return alert("Geolocation not supported.");
    
    updateMapStatus('Intercepting satellite coordinates...', 'warning');
    
    navigator.geolocation.getCurrentPosition(
        pos => {
            userCoords = [pos.coords.latitude, pos.coords.longitude];
            document.getElementById('startInput').value = `${userCoords[0].toFixed(5)}, ${userCoords[1].toFixed(5)}`;
            map.flyTo(userCoords, 16); // Slightly closer zoom for precision
            updateMapStatus('Location Fixed via GPS', 'success');
            if (window.showSuccess) showSuccess("Current location accurately fixed.");
        },
        err => {
            console.error("Geolocation error:", err);
            updateMapStatus('GPS Signal Interrupted', 'danger');
            let msg = "Could not get location.";
            if (err.code === 1) msg = "Location permission denied.";
            else if (err.code === 2) msg = "Location unavailable.";
            else if (err.code === 3) msg = "Timeout obtaining location.";
            alert(msg);
        },
        {
            enableHighAccuracy: true,
            timeout: 10000,
            maximumAge: 0
        }
    );
}

// Interactive Map Picker
let isPickingMap = false;
let pickerInputId = null;

function enableMapPicker(inputId) {
    if (isPickingMap) {
        // Cancel active picker
        document.getElementById('map').style.cursor = '';
        map.off('click', onMapPicked);
        updateMapStatus('Map picker canceled', 'warning');
        isPickingMap = false;
        return;
    }
    
    isPickingMap = true;
    pickerInputId = inputId;
    document.getElementById('map').style.cursor = 'crosshair';
    updateMapStatus('Click anywhere on the map to select location...', 'warning');
    
    if (window.showSuccess) showSuccess("Click on the map to drop a pin.");
    
    // Listen for a single click
    setTimeout(() => {
        map.once('click', onMapPicked);
    }, 100);
}

function onMapPicked(e) {
    if (!isPickingMap || !pickerInputId) return;
    
    const lat = e.latlng.lat;
    const lng = e.latlng.lng;
    
    const input = document.getElementById(pickerInputId);
    if (input) {
        input.value = `${lat.toFixed(5)}, ${lng.toFixed(5)}`;
        input.classList.add('flash-highlight'); // Optionally add CSS for visual feedback
        setTimeout(() => input.classList.remove('flash-highlight'), 1000);
    }
    
    // Draw a temporary marker just to show where they clicked
    const tempMarker = L.circleMarker([lat, lng], {
        radius: 6,
        fillColor: pickerInputId === 'startInput' ? '#10b981' : '#ef4444',
        color: '#fff',
        weight: 2,
        opacity: 1,
        fillOpacity: 1
    }).addTo(map);
    
    // Clear the marker after a short delay since routing will redraw main markers anyway
    setTimeout(() => map.removeLayer(tempMarker), 4000);
    
    document.getElementById('map').style.cursor = '';
    isPickingMap = false;
    pickerInputId = null;
    
    updateMapStatus('Coordinates Locked', 'success');
}

