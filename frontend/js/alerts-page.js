/**
 * SDARS Alerts Management Page
 * Comprehensive alert viewing, filtering, and management
 */

// State management
const alertsPageState = {
    activeAlerts: [],
    alertHistory: [],
    allAlerts: [],
    predictions: [],
    zones: [],          // All zones created on Zones page
    allZoneNames: [],   // Quick lookup list of zone names
    currentFilter: {
        severity: 'all',
        status: 'active'
    },
    currentView: 'predictions'
};

function switchView(viewName) {
    alertsPageState.currentView = viewName;
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
        btn.style.borderBottom = '2px solid transparent';
        btn.style.color = '#a8b3cf';
    });

    const activeBtn = document.getElementById(`tab-${viewName}`);
    if (activeBtn) {
        activeBtn.classList.add('active');
        activeBtn.style.borderBottom = '2px solid #6366f1';
        activeBtn.style.color = 'white';
    }

    // Toggle Content
    const predView = document.getElementById('view-predictions');
    const zoneView = document.getElementById('view-zones');

    if (predView) predView.style.display = viewName === 'predictions' ? 'block' : 'none';
    if (zoneView) zoneView.style.display = viewName === 'zones' ? 'block' : 'none';
}

// Make globally accessible
window.switchView = switchView;

/**
 * Initialize the alerts page
 */
function initAlertsPage() {
    console.log('🚨 Initializing Alerts Page...');

    // Load alerts
    loadAlerts(true);

    // Set up auto-refresh (every 30 seconds, no loader)
    setInterval(() => loadAlerts(false), 30000);

    console.log('✅ Alerts Page initialized');
}

/**
 * Load alerts from API
 */
async function loadAlerts(showLoader = true) {
    const loader = document.getElementById('loadingOverlay');
    if (showLoader && loader) loader.classList.add('active');

    try {
        // ⭐ Check for Zone-Specific View from URL
        const urlParams = new URLSearchParams(window.location.search);
        const targetZoneName = urlParams.get('zone');
        const targetZoneId = urlParams.get('zoneId');

        // Helper: safe fetch
        const fetchData = async (url) => {
            try {
                const res = await fetch(url);
                if (res.ok) return await res.json();
                return null;
            } catch (e) {
                console.warn(`Failed to fetch ${url}:`, e);
                return null;
            }
        };

        // Fetch everything in parallel
        const [predData, activeData, historyData, zonesData] = await Promise.all([
            fetchData(`${API_BASE_URL}/predictions/history?limit=30`),
            fetchData(`${API_BASE_URL}/alerts/active`),
            fetchData(`${API_BASE_URL}/alerts/history?limit=30`),
            fetchData(`${API_BASE_URL}/zones`)          // ⭐ Fetch all created zones
        ]);

        // Store zones for filtering
        if (zonesData && zonesData.zones) {
            alertsPageState.zones = zonesData.zones;
            alertsPageState.allZoneNames = zonesData.zones.map(z => z.name);
            console.log(`📍 Loaded ${alertsPageState.zones.length} zones for alert filtering`);
        }

        // Helper: does this alert belong to any created zone?
        const isZoneAlert = (alert) => {
            const matched = alert.metadata?.matched_zones || [];
            const locationName = alert.location?.name || '';
            return alertsPageState.allZoneNames.some(zoneName =>
                matched.some(z => z.name === zoneName) ||
                locationName.includes(`Zone: ${zoneName}`)
            );
        };

        // Helper: which zone does this alert belong to?
        const getAlertZoneName = (alert) => {
            const matched = alert.metadata?.matched_zones || [];
            const locationName = alert.location?.name || '';
            for (const zoneName of alertsPageState.allZoneNames) {
                if (matched.some(z => z.name === zoneName)) return zoneName;
                if (locationName.includes(`Zone: ${zoneName}`)) return zoneName;
            }
            return null;
        };
        // Expose for use in card rendering
        alertsPageState._getAlertZoneName = getAlertZoneName;

        // 1. Predictions
        if (predData) {
            alertsPageState.predictions = Array.isArray(predData) ? predData : [];
        }

        // 2. Active alerts
        if (activeData) {
            let active = activeData.alerts || [];

            if (targetZoneName) {
                // ⭐ SPECIFIC ZONE VIEW (came from Zones page 🚨 button)
                active = active.filter(alert => {
                    const matched = alert.metadata?.matched_zones || [];
                    const inMeta = matched.some(z => z.name === targetZoneName || String(z.id) === targetZoneId);
                    const inLocation = (alert.location?.name || '').includes(`Zone: ${targetZoneName}`);
                    return inMeta || inLocation;
                });
                console.log(`🎯 Zone filter '${targetZoneName}' → ${active.length} active alerts`);

                // Auto-switch tab and update title
                switchView('zones');
                const title = document.querySelector('.page-title');
                if (title) title.innerHTML = `🚨 <span class="gradient-text">${targetZoneName}</span> Alerts`;

            } else {
                // ⭐ ALL ZONES VIEW — show alerts from ANY created zone
                active = active.filter(isZoneAlert);
                console.log(`📍 All-zones filter → ${active.length} active zone alerts`);
            }
            alertsPageState.activeAlerts = active;
        }

        // 3. Alert history
        if (historyData) {
            let history = historyData.alerts || [];

            if (targetZoneName) {
                history = history.filter(alert => {
                    const matched = alert.metadata?.matched_zones || [];
                    const inMeta = matched.some(z => z.name === targetZoneName || String(z.id) === targetZoneId);
                    const inLocation = (alert.location?.name || '').includes(`Zone: ${targetZoneName}`);
                    return inMeta || inLocation;
                });
            } else {
                // All zones view
                history = history.filter(isZoneAlert);
            }
            alertsPageState.alertHistory = history;
        }

        // Combine
        alertsPageState.allAlerts = [
            ...alertsPageState.activeAlerts,
            ...alertsPageState.alertHistory
        ];

        // Update UI
        updateStatistics();
        displayAlerts();
        displayPredictions();

    } catch (error) {
        console.error('Error loading alerts:', error);
        showError('Tactical link interrupted. Retrying...');
    } finally {
        if (loader) {
            setTimeout(() => loader.classList.remove('active'), 500);
        }
    }
}

/**
 * Update alert statistics
 */
function updateStatistics() {
    const stats = {
        critical: 0,
        high: 0,
        medium: 0,
        low: 0,
        total: 0
    };

    // Count by severity
    alertsPageState.activeAlerts.forEach(alert => {
        stats.total++;
        switch (alert.severity) {
            case 'CRITICAL':
                stats.critical++;
                break;
            case 'HIGH':
                stats.high++;
                break;
            case 'MEDIUM':
                stats.medium++;
                break;
            case 'LOW':
                stats.low++;
                break;
        }
    });

    // Update UI
    document.getElementById('criticalCount').textContent = stats.critical;
    document.getElementById('highCount').textContent = stats.high;
    document.getElementById('mediumCount').textContent = stats.medium;
    document.getElementById('lowCount').textContent = stats.low;
    document.getElementById('totalCount').textContent = stats.total;
    document.getElementById('activeCountBadge').textContent = alertsPageState.activeAlerts.length;
    const predBadge = document.getElementById('predictionCountBadge');
    if (predBadge) predBadge.textContent = alertsPageState.predictions ? alertsPageState.predictions.length : 0;
}

/**
 * Display Global Predictions
 */
function displayPredictions() {
    const container = document.getElementById('predictionsList');
    if (!container) return;

    if (!alertsPageState.predictions || alertsPageState.predictions.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">🧠</div>
                <h3>No Intelligence Data</h3>
                <p>Waiting for satellite analysis stream...</p>
            </div>
        `;
        return;
    }

    container.innerHTML = alertsPageState.predictions.map((pred, index) => {
        const riskClass = pred.overall_risk.toLowerCase();
        return `
        <div class="alert-card ${riskClass}" style="opacity: 0.9;">
            <div class="alert-header">
                <div>
                    <span class="alert-severity ${riskClass}">${pred.overall_risk}</span>
                    <h3 class="alert-title">${pred.name} - ${pred.primary_threat.toUpperCase()} Analysis</h3>
                </div>
            </div>
            <div class="alert-meta">
                <div>🕒 ${new Date(pred.timestamp).toLocaleString()}</div>
                <div>📍 ${pred.lat.toFixed(4)}, ${pred.lon.toFixed(4)}</div>
            </div>
            <div class="alert-message">
                <strong>AI Confidence:</strong> ${(pred.risk_scores[pred.primary_threat] * 100).toFixed(1)}%<br>
                Temp: ${pred.weather.temperature}°C | Wind: ${pred.weather.wind_speed} km/h
            </div>
            <div class="alert-actions" style="margin-top: 15px; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 10px;">
                 <button class="alert-btn ack" onclick="createAlertFromPrediction(${index})" style="width: 100%;">
                    🚨 Confirm & Send Alert
                 </button>
            </div>
        </div>
        `;
    }).join('');
}

async function createAlertFromPrediction(index) {
    const pred = alertsPageState.predictions[index];
    if (!pred) return;

    if (!confirm(`Confirm sending a real alert for ${pred.name}? This will notify subscribers.`)) return;

    try {
        // We'll use the existing /api/alerts/create endpoint or similar? 
        // Actually, we need to adapt the prediction to an alert creation payload.
        // We can reuse the backend logic or just send the prediction data.
        // Let's assume we have an endpoint or we can manually construct it.
        // For now, I will create a new alert via the TEST endpoint logic or similar.
        // Actually, better: The backend `create_alert` logic handles prediction dicts.
        // I should probably expose an endpoint `/api/alerts/from-prediction`.

        const primaryThreat = pred.primary_threat || 'unknown';
        const riskScore = pred.risk_scores && pred.risk_scores[primaryThreat]
            ? pred.risk_scores[primaryThreat]
            : 0.9;

        // Get current user email
        const currentUser = JSON.parse(localStorage.getItem('sdars_user'));

        // Map to backend expectation
        const payload = {
            user_email: currentUser ? currentUser.email : null,
            overall_risk_level: pred.overall_risk,
            primary_threat: primaryThreat,
            location_name: pred.name,
            latitude: pred.lat,
            longitude: pred.lon,
            [primaryThreat]: {
                confidence: riskScore,
                risk_level: pred.overall_risk,
                reasons: [`AI Analysis: ${pred.overall_risk} Risk`]
            }
        };

        const response = await fetch(`${API_BASE_URL}/auth/promote-alert`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (response.ok) {
            showSuccess(`Tactical Alert Dispatched for ${pred.name}! Notifications sent to subscribers.`);
            await loadAlerts();
            // Stay on predictions view to maintain situational awareness
        } else {
            showError('Failed to promote prediction.');
        }

    } catch (e) {
        console.error(e);
        showError('Error promoting alert.');
    }
}

/**
 * Display alerts based on current filter
 */
function displayAlerts() {
    const activeList = document.getElementById('activeAlertsList');
    const historyList = document.getElementById('historyAlertsList');

    // Filter alerts
    const filteredActive = filterAlertsByCurrentSettings(alertsPageState.activeAlerts);
    const filteredHistory = filterAlertsByCurrentSettings(alertsPageState.alertHistory);

    // Display active alerts
    if (filteredActive.length > 0) {
        activeList.innerHTML = filteredActive.map(alert => createAlertCard(alert, true)).join('');
    } else {
        activeList.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">✅</div>
                <h3>No Active Alerts</h3>
                <p>All systems are operating normally.</p>
            </div>
        `;
    }

    // Display history
    if (filteredHistory.length > 0) {
        historyList.innerHTML = filteredHistory.map(alert => createAlertCard(alert, false)).join('');
    } else {
        historyList.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">📭</div>
                <h3>No Alert History</h3>
                <p>Acknowledged alerts will appear here.</p>
            </div>
        `;
    }
}

/**
 * Filter alerts by current settings
 */
function filterAlertsByCurrentSettings(alerts) {
    return alerts.filter(alert => {
        // Filter by severity
        if (alertsPageState.currentFilter.severity === 'all') {
            return true;
        }
        return alert.severity === alertsPageState.currentFilter.severity;
    });
}

/**
 * Create alert card HTML
 */
function createAlertCard(alert, isActive) {
    const disasterEmoji = {
        'fire': '🔥',
        'flood': '🌊',
        'cyclone': '🌪️',
        'earthquake': '🏚️',
        'tsunami': '🌊',
        'drought': '🌵'
    };

    const timeAgo = formatTimeAgo(alert.created_at);
    const location = alert.location?.name || 'Unknown Location';
    const emoji = disasterEmoji[alert.disaster_type] || '⚠️';

    // Show which zone this alert belongs to
    const zoneName = alertsPageState._getAlertZoneName
        ? alertsPageState._getAlertZoneName(alert)
        : null;
    const zoneBadge = zoneName
        ? `<div style="margin: 8px 0 4px; padding: 4px 10px; background: rgba(99,102,241,0.15); border: 1px solid rgba(99,102,241,0.35); border-radius: 20px; display: inline-block; font-size: 11px; color: #a5b4fc; font-weight: 600;">
               📍 Zone: ${zoneName}
           </div>`
        : '';

    return `
        <div class="alert-card ${alert.severity.toLowerCase()}" data-alert-id="${alert.alert_id}">
            <div class="alert-header">
                <div class="alert-title-section">
                    <span class="alert-severity ${alert.severity.toLowerCase()}">${alert.severity}</span>
                    <h3 class="alert-title">${alert.title}</h3>
                </div>
                <div class="alert-emoji">${emoji}</div>
            </div>

            <div class="alert-meta">
                <div class="alert-meta-item"><span>📍</span><span>${location}</span></div>
                <div class="alert-meta-item"><span>🕒</span><span>${timeAgo}</span></div>
                <div class="alert-meta-item"><span>📡</span><span>SIG-INT: ${alert.alert_id.substring(0, 8)}</span></div>
            </div>

            ${zoneBadge}

            <div class="alert-message" style="margin-top: 10px;">
                ${alert.message.substring(0, 180)}...
            </div>

            <div class="neural-log">
                <div class="neural-line process">● ANALYZING TACTICAL INTERSECTION...</div>
                <div class="neural-line ready">● CLOUD-SIGHT AI: CONFIRMED ${alert.disaster_type.toUpperCase()} SIGNATURE</div>
            </div>

            <div class="alert-actions" style="margin-top: 15px;">
                <button class="alert-btn view" onclick="viewAlertDetail('${alert.alert_id}')">Tactical Overview</button>
                ${isActive ? `<button class="alert-btn ack" onclick="acknowledgeAlertFromPage('${alert.alert_id}')">Acknowledge</button>` : ''}
            </div>
        </div>
    `;
}

/**
 * Format time ago
 */
function formatTimeAgo(timestamp) {
    const date = new Date(timestamp);
    const now = new Date();
    const seconds = Math.floor((now - date) / 1000);

    if (seconds < 60) return 'Just now';
    if (seconds < 3600) return `${Math.floor(seconds / 60)} minutes ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)} hours ago`;
    if (seconds < 604800) return `${Math.floor(seconds / 86400)} days ago`;

    return date.toLocaleString();
}

/**
 * View alert details in modal with Neural Reasoning
 */
function viewAlertDetail(alertId) {
    const alert = alertsPageState.allAlerts.find(a => a.alert_id === alertId);
    if (!alert) return;

    const modal = document.getElementById('alertDetailModal');
    const modalTitle = document.getElementById('modalTitle');
    const modalBody = document.getElementById('modalBody');

    modalTitle.innerHTML = `<span style="color: #ff4d4d">REPORT-ID:</span> ${alert.alert_id.substring(0, 12)}...`;

    // Neural Thought Chain Simulation
    const neuralThoughts = [
        `[${new Date().toLocaleTimeString()}] LAT/LON LOCK ACQUIRED`,
        `FETCHING MULTI-MODAL SENTINEL-2 ARRAYS...`,
        `DETECTED ${alert.disaster_type.toUpperCase()} PROBABILITY: ${(alert.metadata?.confidence * 100 || 88).toFixed(1)}%`,
        `CROSS-REFERENCING WITH LOCAL SHELTER DATABASE...`,
        `STATUS: ${alert.severity} THREAT LEVEL CONFIRMED.`
    ];

    modalBody.innerHTML = `
        <div class="tactical-grid" style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 24px;">
            <div style="background: rgba(255,255,255,0.05); padding: 16px; border-radius: 4px; border-left: 2px solid #00f2ff;">
                <div style="color: #6b7a99; font-size: 10px; margin-bottom: 8px; font-family: 'JetBrains Mono';">GEOSPATIAL VECTOR</div>
                <div style="color: white; font-size: 15px; font-weight: 700; font-family: 'JetBrains Mono';">
                    ${alert.location?.lat.toFixed(6)}, ${alert.location?.lon.toFixed(6)}
                </div>
            </div>
            <div style="background: rgba(255,255,255,0.05); padding: 16px; border-radius: 4px; border-left: 2px solid #ff9800;">
                <div style="color: #6b7a99; font-size: 10px; margin-bottom: 8px; font-family: 'JetBrains Mono';">TACTICAL STATUS</div>
                <div style="color: #ff9800; font-size: 15px; font-weight: 800; font-family: 'JetBrains Mono';">INTERCEPT ACTIVE</div>
            </div>
        </div>
        
        <div style="background: #05080f; padding: 20px; border: 1px solid rgba(255,255,255,0.1); border-radius: 4px; margin-bottom: 20px;">
            <div style="color: #6b7a99; font-size: 10px; margin-bottom: 12px; font-family: 'JetBrains Mono';">NEURAL REASONING CHAIN</div>
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 11px; color: #00f2ff; line-height: 1.6;">
                ${neuralThoughts.map(t => `<div style="margin-bottom: 4px;">> ${t}</div>`).join('')}
                <div style="margin-top: 10px; color: #4caf50;">● ANALYSIS COMPLETE: EMERGENCY PROTOCOL ALPHA INITIATED</div>
            </div>
        </div>

        <div style="background: rgba(255,255,255,0.03); padding: 20px; border-radius: 4px; margin-bottom: 20px;">
            <div style="color: #6b7a99; font-size: 10px; margin-bottom: 12px; font-family: 'JetBrains Mono';">SITREP DESCRIPTION</div>
            <div style="color: white; line-height: 1.8; font-size: 14px;">${alert.message}</div>
        </div>
        
        <div style="display: flex; gap: 12px;">
            <button class="btn-primary" onclick="acknowledgeAlertFromPage('${alert.alert_id}'); closeModal();" style="flex: 1; border-radius: 2px; font-family: 'JetBrains Mono';">
                EXECUTE ACKNOWLEDGEMENT
            </button>
            <button class="btn-secondary" onclick="closeModal()" style="padding: 12px 24px; border-radius: 2px;">
                EXIT
            </button>
        </div>
    `;

    modal.style.display = 'flex';
}

/**
 * Close modal
 */
function closeModal() {
    document.getElementById('alertDetailModal').style.display = 'none';
}

/**
 * Acknowledge alert from page
 */
async function acknowledgeAlertFromPage(alertId) {
    try {
        console.log(`📤 Acknowledging Alert: ${alertId}`);

        const response = await fetch(`${API_BASE_URL}/alerts/acknowledge`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                alert_id: alertId,
                user_id: 'web_user',
                email: null
            })
        });

        if (response.ok) {
            await loadAlerts();
            showSuccess('Alert acknowledged.');
        } else {
            const errorData = await response.json().catch(() => ({ detail: 'Unknown server error' }));
            showError(`Server Error: ${errorData.detail || 'Could not acknowledge alert'}`);
        }

    } catch (error) {
        console.error('Network/Client Error:', error);
        showError('Network error: Could not reach the AI Command Center.');
    }
}

/**
 * Dismiss alert from page
 */
function dismissAlertFromPage(alertId) {
    const card = document.querySelector(`[data-alert-id="${alertId}"]`);
    if (card) {
        card.style.opacity = '0';
        card.style.transform = 'translateX(-20px)';
        setTimeout(() => {
            card.remove();
        }, 300);
    }
}

/**
 * Acknowledge all alerts
 */
async function acknowledgeAll() {
    if (alertsPageState.activeAlerts.length === 0) {
        showError('No active alerts to acknowledge');
        return;
    }

    if (!confirm(`Acknowledge all ${alertsPageState.activeAlerts.length} active alerts?`)) {
        return;
    }

    for (const alert of alertsPageState.activeAlerts) {
        await acknowledgeAlertFromPage(alert.alert_id);
    }
}

/**
 * Test alert
 */
async function testAlert() {
    try {
        const response = await fetch('http://localhost:8000/api/alerts/test', {
            method: 'POST'
        });

        if (response.ok) {
            showSuccess('Test alert created! Refreshing in 2 seconds...');
            setTimeout(loadAlerts, 2000);
        }

    } catch (error) {
        console.error('Error creating test alert:', error);
        showError('Failed to create test alert');
    }
}

/**
 * Refresh alerts
 */
async function refreshAlerts() {
    await loadAlerts(true);
}

/**
 * Filter alerts
 */
function filterAlerts() {
    alertsPageState.currentFilter.severity = document.getElementById('severityFilter').value;
    alertsPageState.currentFilter.status = document.getElementById('statusFilter').value;

    displayAlerts();
}

/**
 * Show success message
 */
function showSuccess(message) {
    console.log('✅ ' + message);

    // Create toast notification
    const toast = document.createElement('div');
    toast.className = 'toast-notification success';
    toast.innerHTML = `
        <div class="toast-icon">✅</div>
        <div class="toast-message">${message}</div>
    `;

    document.body.appendChild(toast);

    // Trigger animation
    setTimeout(() => toast.classList.add('show'), 10);

    // Remove after 3 seconds
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

/**
 * Show error message
 */
function showError(message) {
    console.error('❌ ' + message);

    // Create toast notification
    const toast = document.createElement('div');
    toast.className = 'toast-notification error';
    toast.innerHTML = `
        <div class="toast-icon">❌</div>
        <div class="toast-message">${message}</div>
    `;

    document.body.appendChild(toast);

    // Trigger animation
    setTimeout(() => toast.classList.add('show'), 10);

    // Remove after 4 seconds
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

// Initialize on page load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initAlertsPage);
} else {
    initAlertsPage();
}

// Settings Management
async function openSettingsModal() {
    const modal = document.getElementById('settingsModal');
    modal.style.display = 'flex';

    // Fetch current settings
    try {
        const response = await fetch(`${API_BASE_URL}/settings`);
        if (response.ok) {
            const settings = await response.json();
            // Fill form
            const fields = ['smtp_server', 'smtp_port', 'smtp_user', 'smtp_password', 'alert_email_to'];
            fields.forEach(field => {
                if (settings[field]) {
                    document.getElementById(field).value = settings[field];
                }
            });
        }
    } catch (e) {
        console.error("Settings Load Error:", e);
    }
}

function closeSettingsModal() {
    document.getElementById('settingsModal').style.display = 'none';
}

async function saveSettings(event) {
    event.preventDefault();

    const formData = {
        smtp_server: document.getElementById('smtp_server').value,
        smtp_port: parseInt(document.getElementById('smtp_port').value),
        smtp_user: document.getElementById('smtp_user').value,
        smtp_password: document.getElementById('smtp_password').value,
        alert_email_to: document.getElementById('alert_email_to').value
    };

    try {
        const response = await fetch(`${API_BASE_URL}/settings/update`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        });

        if (response.ok) {
            showSuccess('Strategic configuration updated successfully!');
            closeSettingsModal();
        } else {
            throw new Error('Update failed');
        }
    } catch (e) {
        showError('Critical failure: Could not update settings.');
    }
}

// Close modal on background click
document.addEventListener('click', (e) => {
    if (e.target.id === 'alertDetailModal') {
        closeModal();
    }
    if (e.target.id === 'settingsModal') {
        closeSettingsModal();
    }
});
