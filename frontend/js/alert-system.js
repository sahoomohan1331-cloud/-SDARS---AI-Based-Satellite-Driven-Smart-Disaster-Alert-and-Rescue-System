/**
 * SDARS Real-time Alert Notification System (Frontend)
 * Displays alerts, manages notifications, and handles user interactions
 */

// Alert State Management
const alertState = {
    activeAlerts: [],
    alertHistory: [],
    notificationSound: null,
    pollingInterval: null,
    lastCheck: Date.now()
};

/**
 * Initialize Alert System
 */
function initAlertSystem() {
    console.log('🚨 Initializing Alert System...');

    // Create alert container if it doesn't exist
    createAlertContainer();

    // Load notification sound
    loadNotificationSound();

    // Start polling for new alerts
    startAlertPolling();

    // Load initial alerts
    loadActiveAlerts();

    // Request notification permission
    requestNotificationPermission();

    console.log('✅ Alert System initialized');
}

/**
 * Create alert notification container
 */
function createAlertContainer() {
    if (document.getElementById('alertContainer')) return;

    const container = document.createElement('div');
    container.id = 'alertContainer';
    container.style.cssText = `
        position: fixed;
        top: 80px;
        right: 20px;
        z-index: 10000;
        max-width: 400px;
        display: flex;
        flex-direction: column;
        gap: 12px;
        pointer-events: none;
    `;

    document.body.appendChild(container);
}

/**
 * Load notification sound
 */
function loadNotificationSound() {
    alertState.notificationSound = new Audio('data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrHp66hVFApGn+DyvmwhBit+z/DYiSwHG2W37OOWRgsMT6nn');
}

/**
 * Request browser notification permission
 */
function requestNotificationPermission() {
    if ('Notification' in window && Notification.permission === 'default') {
        Notification.requestPermission().then(permission => {
            console.log(`🔔 Notification permission: ${permission}`);
        });
    }
}

/**
 * Start polling for new alerts
 */
function startAlertPolling(intervalMs = 30000) {
    // Poll every 30 seconds
    alertState.pollingInterval = setInterval(async () => {
        await checkForNewAlerts();
    }, intervalMs);
}

/**
 * Stop alert polling
 */
function stopAlertPolling() {
    if (alertState.pollingInterval) {
        clearInterval(alertState.pollingInterval);
        alertState.pollingInterval = null;
    }
}

/**
 * Check for new alerts from backend
 */
async function checkForNewAlerts() {
    try {
        const response = await fetch(`${API_BASE_URL}/alerts/active`);

        if (response.ok) {
            const data = await response.json();
            const newAlerts = data.alerts || [];

            // Find alerts we haven't seen yet
            for (const alert of newAlerts) {
                const exists = alertState.activeAlerts.find(a => a.alert_id === alert.alert_id);
                if (!exists) {
                    // New alert!
                    displayAlert(alert);
                    playNotificationSound(alert.severity);
                    showBrowserNotification(alert);
                }
            }

            alertState.activeAlerts = newAlerts;
        }

    } catch (error) {
        console.error('Error checking for alerts:', error);
    }
}

/**
 * Load active alerts on page load
 */
async function loadActiveAlerts() {
    try {
        const response = await fetch(`${API_BASE_URL}/alerts/active`);

        if (response.ok) {
            const data = await response.json();
            alertState.activeAlerts = data.alerts || [];

            // Display existing alerts (without sound)
            alertState.activeAlerts.forEach(alert => {
                displayAlert(alert, false);
            });

            console.log(`📋 Loaded ${alertState.activeAlerts.length} active alerts`);
        }

    } catch (error) {
        console.error('Error loading alerts:', error);
    }
}

/**
 * Display an alert notification
 */
function displayAlert(alert, playSound = true) {
    const container = document.getElementById('alertContainer');
    if (!container) return;

    // Create alert card
    const alertCard = createAlertCard(alert);
    container.appendChild(alertCard);

    // Animate in
    setTimeout(() => {
        alertCard.style.transform = 'translateX(0)';
        alertCard.style.opacity = '1';
    }, 100);

    // Auto-dismiss after 10 seconds for low/medium severity
    if (alert.severity === 'LOW' || alert.severity === 'MEDIUM') {
        setTimeout(() => {
            dismissAlertCard(alertCard);
        }, 10000);
    }
}

/**
 * Create alert card HTML
 */
function createAlertCard(alert) {
    const card = document.createElement('div');
    card.className = `alert-card alert-${alert.severity.toLowerCase()}`;
    card.id = `alert-${alert.alert_id}`;
    card.style.cssText = `
        background: rgba(13, 17, 23, 0.98);
        border-radius: 12px;
        padding: 16px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
        border-left: 4px solid ${getSeverityColor(alert.severity)};
        pointer-events: all;
        transform: translateX(450px);
        opacity: 0;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        max-width: 400px;
    `;

    const severityEmoji = {
        'LOW': 'ℹ️',
        'MEDIUM': '⚠️',
        'HIGH': '🚨',
        'CRITICAL': '🆘'
    };

    card.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 12px;">
            <div style="display: flex; align-items: center; gap: 8px;">
                <span style="font-size: 24px;">${severityEmoji[alert.severity] || '⚠️'}</span>
                <div>
                    <div style="font-weight: 700; color: ${getSeverityColor(alert.severity)}; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px;">
                        ${alert.severity} ALERT
                    </div>
                    <div style="color: white; font-weight: 600; font-size: 14px; margin-top: 2px;">
                        ${alert.disaster_type.toUpperCase()} Risk Detected
                    </div>
                </div>
            </div>
            <button onclick="dismissAlert('${alert.alert_id}')" style="
                background: rgba(255,255,255,0.1);
                border: none;
                color: white;
                width: 24px;
                height: 24px;
                border-radius: 50%;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 16px;
                transition: background 0.2s;
            " onmouseover="this.style.background='rgba(255,255,255,0.2)'" 
               onmouseout="this.style.background='rgba(255,255,255,0.1)'">
                ×
            </button>
        </div>
        
        <div style="color: #e2e8f0; font-size: 13px; line-height: 1.5; margin-bottom: 12px;">
            <strong>📍 ${alert.location.name}</strong><br>
            <span style="color: #94a3b8;">${formatAlertTime(alert.created_at)}</span>
        </div>
        
        <div style="color: #cbd5e1; font-size: 12px; line-height: 1.6; margin-bottom: 16px; max-height: 100px; overflow-y: auto;">
            ${alert.message.substring(0, 200).replace(/\n/g, '<br>')}${alert.message.length > 200 ? '...' : ''}
        </div>
        
        <div style="display: flex; gap: 8px;">
            <button onclick="viewAlertDetails('${alert.alert_id}')" style="
                flex: 1;
                background: linear-gradient(135deg, #6366f1, #4f46e5);
                color: white;
                border: none;
                padding: 10px;
                border-radius: 8px;
                font-weight: 600;
                font-size: 12px;
                cursor: pointer;
                transition: transform 0.2s;
            " onmouseover="this.style.transform='scale(1.02)'" 
               onmouseout="this.style.transform='scale(1)'">
                📋 View Details
            </button>
            <button onclick="acknowledgeAlert('${alert.alert_id}')" style="
                flex: 1;
                background: rgba(34, 197, 94, 0.2);
                color: #22c55e;
                border: 1px solid rgba(34, 197, 94, 0.3);
                padding: 10px;
                border-radius: 8px;
                font-weight: 600;
                font-size: 12px;
                cursor: pointer;
                transition: background 0.2s;
            " onmouseover="this.style.background='rgba(34, 197, 94, 0.3)'" 
               onmouseout="this.style.background='rgba(34, 197, 94, 0.2)'">
                ✓ Acknowledge
            </button>
        </div>
    `;

    return card;
}

/**
 * Get color for severity level
 */
function getSeverityColor(severity) {
    const colors = {
        'LOW': '#3b82f6',
        'MEDIUM': '#f59e0b',
        'HIGH': '#ef4444',
        'CRITICAL': '#dc2626'
    };
    return colors[severity] || '#6b7280';
}

/**
 * Format alert timestamp
 */
function formatAlertTime(timestamp) {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = Math.floor((now - date) / 1000); // seconds

    if (diff < 60) return 'Just now';
    if (diff < 3600) return `${Math.floor(diff / 60)} minutes ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)} hours ago`;

    return date.toLocaleString();
}

/**
 * Play notification sound
 */
function playNotificationSound(severity) {
    if (alertState.notificationSound) {
        try {
            alertState.notificationSound.volume = severity === 'CRITICAL' ? 1.0 : 0.5;
            alertState.notificationSound.play();
        } catch (error) {
            console.warn('Could not play notification sound:', error);
        }
    }
}

/**
 * Show browser notification
 */
function showBrowserNotification(alert) {
    if ('Notification' in window && Notification.permission === 'granted') {
        const notification = new Notification(`${alert.severity} Alert`, {
            body: `${alert.disaster_type.toUpperCase()} risk detected in ${alert.location.name}`,
            icon: '/assets/logo.png', // Update with actual icon path
            badge: '/assets/badge.png',
            tag: alert.alert_id,
            requireInteraction: alert.severity === 'CRITICAL',
            vibrate: [200, 100, 200]
        });

        notification.onclick = () => {
            window.focus();
            viewAlertDetails(alert.alert_id);
            notification.close();
        };
    }
}

/**
 * Dismiss alert notification
 */
function dismissAlert(alertId) {
    const card = document.getElementById(`alert-${alertId}`);
    if (card) {
        dismissAlertCard(card);
    }
}

/**
 * Dismiss alert card with animation
 */
function dismissAlertCard(card) {
    card.style.transform = 'translateX(450px)';
    card.style.opacity = '0';

    setTimeout(() => {
        if (card.parentNode) {
            card.parentNode.removeChild(card);
        }
    }, 300);
}

/**
 * Acknowledge an alert
 */
async function acknowledgeAlert(alertId) {
    try {
        const currentUser = JSON.parse(localStorage.getItem('sdars_user'));
        const userEmail = currentUser ? currentUser.email : null;
        const userId = currentUser ? currentUser.id || 'web_user' : 'web_user';

        const response = await fetch(`${API_BASE_URL}/alerts/acknowledge`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                alert_id: alertId,
                user_id: String(userId),
                email: userEmail
            })
        });

        if (response.ok) {
            // Remove from active alerts
            alertState.activeAlerts = alertState.activeAlerts.filter(a => a.alert_id !== alertId);

            // Dismiss card
            dismissAlert(alertId);

            // Show success message
            if (typeof showSuccess === 'function') {
                showSuccess('Alert acknowledged and tactical report sent to email.');
            }
        } else {
            const errorData = await response.json().catch(() => ({ detail: 'Unknown server error' }));
            if (typeof showError === 'function') {
                showError(`Acknowledgment failed: ${errorData.detail || 'Server rejected request'}`);
            }
        }

    } catch (error) {
        console.error('Error acknowledging alert:', error);
        if (typeof showError === 'function') {
            showError('Network error: Could not reach the AI Command Center.');
        }
    }
}

/**
 * View alert details
 */
function viewAlertDetails(alertId) {
    const alert = alertState.activeAlerts.find(a => a.alert_id === alertId);
    if (!alert) return;

    //Create modal or navigate to details page
    showAlertModal(alert);
}

/**
 * Show alert details modal
 */
function showAlertModal(alert) {
    // Remove existing modal if any
    const existingModal = document.getElementById('alertModal');
    if (existingModal) existingModal.remove();

    const modal = document.createElement('div');
    modal.id = 'alertModal';
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0, 0, 0, 0.8);
        z-index: 20000;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 20px;
    `;

    modal.innerHTML = `
        <div style="
            background: linear-gradient(135deg, #0d1117 0%, #1a1f2e 100%);
            border-radius: 16px;
            max-width: 600px;
            width: 100%;
            max-height: 80vh;
            overflow-y: auto;
            border: 1px solid rgba(255,255,255,0.1);
            box-shadow: 0 20px 60px rgba(0,0,0,0.5);
        ">
            <div style="padding: 24px; border-bottom: 1px solid rgba(255,255,255,0.1);">
                <div style="display: flex; justify-content: space-between; align-items: start;">
                    <h2 style="margin: 0; color: white; font-size: 24px;">
                        ${alert.title}
                    </h2>
                    <button onclick="document.getElementById('alertModal').remove()" style="
                        background: rgba(255,255,255,0.1);
                        border: none;
                        color: white;
                        width: 32px;
                        height: 32px;
                        border-radius: 50%;
                        cursor: pointer;
                        font-size: 20px;
                    ">×</button>
                </div>
                <div style="color: #94a3b8; margin-top: 8px;">
                    ${formatAlertTime(alert.created_at)} • ${alert.location.name}
                </div>
            </div>
            
            <div style="padding: 24px;">
                <pre style="white-space: pre-wrap; font-family: inherit; color: #e2e8f0; line-height: 1.8; margin: 0;">
${alert.message}
                </pre>
                
                <div style="margin-top: 24px; padding: 16px; background: rgba(255,255,255,0.03); border-radius: 12px;">
                    <div style="color: #94a3b8; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 12px;">
                        Alert Metadata
                    </div>
                    <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; color: white;">
                        <div>
                            <div style="color: #64748b; font-size: 12px;">Severity</div>
                            <div style="color: ${getSeverityColor(alert.severity)}; font-weight: 700;">${alert.severity}</div>
                        </div>
                        <div>
                            <div style="color: #64748b; font-size: 12px;">Disaster Type</div>
                            <div style="font-weight: 600; text-transform: uppercase;">${alert.disaster_type}</div>
                        </div>
                        <div>
                            <div style="color: #64748b; font-size: 12px;">Confidence</div>
                            <div style="font-weight: 600;">${(alert.metadata.confidence * 100).toFixed(1)}%</div>
                        </div>
                        <div>
                            <div style="color: #64748b; font-size: 12px;">Alert ID</div>
                            <div style="font-family: monospace; font-size: 11px;">${alert.alert_id}</div>
                        </div>
                    </div>
                </div>
                
                <div style="margin-top: 24px; display: flex; gap: 12px;">
                    <button onclick="acknowledgeAlert('${alert.alert_id}'); document.getElementById('alertModal').remove();" style="
                        flex: 1;
                        background: linear-gradient(135deg, #22c55e, #16a34a);
                        color: white;
                        border: none;
                        padding: 14px;
                        border-radius: 10px;
                        font-weight: 600;
                        font-size: 14px;
                        cursor: pointer;
                    ">
                        ✓ Acknowledge & Close
                    </button>
                     <button onclick="document.getElementById('alertModal').remove()" style="
                        background: rgba(255,255,255,0.05);
                        color: white;
                        border: 1px solid rgba(255,255,255,0.1);
                        padding: 14px 24px;
                        border-radius: 10px;
                        font-weight: 600;
                        font-size: 14px;
                        cursor: pointer;
                    ">
                        Close
                    </button>
                </div>
            </div>
        </div>
    `;

    document.body.appendChild(modal);

    // Close on background click
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.remove();
        }
    });
}

// Initialize alerts when page loads
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initAlertSystem);
} else {
    initAlertSystem();
}

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    stopAlertPolling();
});
