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

document.addEventListener('DOMContentLoaded', () => {
    initMap();
    setupGeocoders();
});

function initMap() {
    map = L.map('map', { zoomControl: false, attributionControl: false }).setView([20.5937, 78.9629], 5);
    terrainLayers = {
        dark: L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', { subdomains: 'abcd', maxZoom: 19 }),
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
                serviceUrl: 'https://router.project-osrm.org/route/v1',
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

            // Run Analysis
            analyzeAllRoutes();

            // Auto-load hazards if checked
            if (document.getElementById('toggleHazards')?.checked) toggleHazards(true);
        });

    } catch (err) {
        navBtn.disabled = false;
        navBtn.innerHTML = `🚀 Start Navigation`;
    }
}

async function analyzeAllRoutes() {
    updateMapStatus('Probing routes for AI security threats...', 'warning');
    for (let i = 0; i < allRoutes.length; i++) {
        const scoreData = await performRouteAnalysis(allRoutes[i]);
        updateRouteBadge(i, scoreData);
        if (i === activeRouteIndex) displaySafetyDetails(scoreData);
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

function updateRouteBadge(index, data) {
    const badge = document.getElementById(`safety-badge-${index}`);
    if (!badge || !data) return;
    const score = data.safety_score;
    badge.className = `route-safety-badge ${score > 80 ? 'safe' : score > 50 ? 'warning' : 'danger'}`;
    badge.textContent = score > 80 ? '✓ Safe' : score > 50 ? '⚠ Caution' : '⛔ High Risk';
}

function displaySafetyDetails(data) {
    const indicator = document.getElementById('safetyIndicator');
    if (!indicator || !data) return;
    const isSafe = data.safety_score > 80;
    indicator.className = `safety-indicator ${isSafe ? 'safe' : 'danger'}`;
    indicator.innerHTML = isSafe ? `✅ ROUTE SECURE: No disaster risks detected.` : `⚠️ DANGER: Hazard zones detected on path!`;
    updateMapStatus(isSafe ? 'Path Verified Safe' : 'CRISIS ALERT: Hazards Intercepted', isSafe ? 'success' : 'danger');
}

function switchToRoute(index) {
    if (index === activeRouteIndex) return;
    activeRouteIndex = index;
    document.querySelectorAll('.route-option-card').forEach((c, i) => c.classList.toggle('active', i === index));
    routeLayers.forEach((l, i) => l.setStyle({ opacity: i === index ? 0.9 : 0.3, weight: i === index ? 7 : 5 }));
    displayRouteDetails(allRoutes[index]);
    map.fitBounds(L.latLngBounds(allRoutes[index].coordinates), { padding: [50, 50] });
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
    if (text.match(/^[-+]?[\d\.]+\s*,\s*[-+]?[\d\.]+$/)) {
        const p = text.split(','); return { lat: parseFloat(p[0]), lng: parseFloat(p[1]) };
    }
    try {
        const res = await fetch(`${API_BASE_URL}/search/${encodeURIComponent(text)}`);
        const data = await res.json();
        if (data.found) return { lat: data.lat, lng: data.lon };
    } catch (e) { }
    return new Promise(r => geocoder.geocode(text, res => r(res?.[0]?.center || null)));
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
    navigator.geolocation.getCurrentPosition(pos => {
        userCoords = [pos.coords.latitude, pos.coords.longitude];
        document.getElementById('startInput').value = `${userCoords[0].toFixed(5)}, ${userCoords[1].toFixed(5)}`;
        map.flyTo(userCoords, 15);
    });
}
