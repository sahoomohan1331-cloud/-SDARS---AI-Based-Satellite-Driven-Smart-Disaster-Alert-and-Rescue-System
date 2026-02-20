
// Authentication Logic for SDARS

let currentUser = null;

document.addEventListener('DOMContentLoaded', () => {
    // Check for saved session
    const savedUser = localStorage.getItem('sdars_user');
    if (savedUser) {
        currentUser = JSON.parse(savedUser);
        updateUIForLogin();
    }

    // Wire up inputs
    const authOTP = document.getElementById('authOTP');
    if (authOTP) {
        authOTP.addEventListener('input', (e) => {
            // Auto-submit or focus logic could go here
            e.target.value = e.target.value.replace(/[^0-9]/g, '');
        });
    }
});

function openAuthModal() {
    const modal = document.getElementById('authModal');
    if (modal) {
        modal.style.display = 'flex';
        document.getElementById('stepEmail').style.display = 'block';
        document.getElementById('stepOTP').style.display = 'none';
    }
}

function closeAuthModal() {
    const modal = document.getElementById('authModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

function backToEmail() {
    document.getElementById('stepEmail').style.display = 'block';
    document.getElementById('stepOTP').style.display = 'none';
}

async function requestOTP() {
    const email = document.getElementById('authEmail').value;
    if (!email || !email.includes('@')) {
        alert('Please enter a valid email address.');
        return;
    }

    try {
        const btn = document.querySelector('#stepEmail button');
        const originalText = btn.innerText;
        btn.innerText = 'SENDING...';
        btn.disabled = true;

        const response = await fetch(`${API_BASE_URL}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email })
        });

        const data = await response.json();

        if (response.ok) {
            document.getElementById('stepEmail').style.display = 'none';
            document.getElementById('stepOTP').style.display = 'block';

            // For Demo/Dev purposes, show the hint if provided
            if (data.demo_hint) {
                document.getElementById('otpDemoHint').innerText = `DEV HINT: Code is likely in server logs`;
            } else if (data.demo_otp) {
                document.getElementById('otpDemoHint').innerText = `DEV CODE: ${data.demo_otp}`;
            }
        } else {
            alert(data.detail || 'Failed to send OTP');
        }

        btn.innerText = originalText;
        btn.disabled = false;

    } catch (error) {
        console.error('Auth Error:', error);
        alert('Connection failed.');
        document.querySelector('#stepEmail button').innerText = 'SEND CODE';
        document.querySelector('#stepEmail button').disabled = false;
    }
}

async function verifyOTP() {
    const email = document.getElementById('authEmail').value;
    const otp = document.getElementById('authOTP').value;

    if (otp.length !== 6) {
        alert('Please enter the 6-digit code.');
        return;
    }

    try {
        const btn = document.querySelector('#stepOTP .btn-primary');
        btn.innerText = 'VERIFYING...';
        btn.disabled = true;

        const response = await fetch(`${API_BASE_URL}/auth/verify`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, otp })
        });

        const data = await response.json();

        if (response.ok) {
            // Login Success
            currentUser = {
                id: data.user_id,
                email: data.email,
                subscribed_zones: data.subscribed_zones
            };

            localStorage.setItem('sdars_user', JSON.stringify(currentUser));
            updateUIForLogin();
            closeAuthModal();

            showSuccess(`Welcome back, ${data.email.split('@')[0]}`);
        } else {
            alert(data.detail || 'Verification failed');
            btn.innerText = 'VERIFY ACCESS';
            btn.disabled = false;
        }

    } catch (error) {
        console.error('Verify Error:', error);
        alert('Verification failed.');
    }
}

function logout() {
    localStorage.removeItem('sdars_user');
    currentUser = null;
    updateUIForLogin();
    showSuccess('Logged out successfully');
}

function updateUIForLogin() {
    const loginBtn = document.getElementById('loginBtn');
    const profileDisplay = document.getElementById('userProfileDisplay');
    const emailDisplay = document.getElementById('userEmailDisplay');

    if (currentUser) {
        if (loginBtn) loginBtn.style.display = 'none';
        if (profileDisplay) profileDisplay.style.display = 'flex';
        if (emailDisplay) emailDisplay.innerText = currentUser.email;

        // Update any subscription buttons on the page
        updateSubscriptionButtons();
    } else {
        if (loginBtn) loginBtn.style.display = 'block';
        if (profileDisplay) profileDisplay.style.display = 'none';
    }
}

// Global Subscription Helper
async function toggleZoneSubscription(zoneName, btnElement) {
    if (!currentUser) {
        openAuthModal();
        return;
    }

    const isSubscribed = currentUser.subscribed_zones.includes(zoneName);
    const endpoint = isSubscribed ? 'unsubscribe' : 'subscribe';

    try {
        if (btnElement) btnElement.disabled = true;

        const response = await fetch(`${API_BASE_URL}/auth/${endpoint}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                email: currentUser.email,
                zone_name: zoneName
            })
        });

        const data = await response.json();

        if (response.ok) {
            currentUser.subscribed_zones = data.zones;
            localStorage.setItem('sdars_user', JSON.stringify(currentUser));
            updateSubscriptionButtons(); // Refresh UI

            if (!isSubscribed) {
                showSuccess(`Subscribed to alerts for ${zoneName}`);
            } else {
                showSuccess(`Unsubscribed from ${zoneName}`);
            }
        }

        if (btnElement) btnElement.disabled = false;

    } catch (error) {
        console.error('Subscription Error:', error);
        if (btnElement) btnElement.disabled = false;
    }
}

function updateSubscriptionButtons() {
    // Find all subscription buttons and update state
    document.querySelectorAll('.subscribe-btn').forEach(btn => {
        const zone = btn.dataset.zone;
        if (!zone) return;

        if (currentUser && currentUser.subscribed_zones.includes(zone)) {
            btn.innerText = '🔕 Unsubscribe';
            btn.classList.add('active');
            btn.style.background = 'rgba(255,255,255,0.1)';
        } else {
            btn.innerText = '🔔 Subscribe to Alerts';
            btn.classList.remove('active');
            btn.style.background = ''; // reset to default class style
        }
    });
}

// Function to trigger a test alert
async function sendTestAlert(zoneName, btnElement) {
    if (!currentUser) {
        showError('Please login to send test alerts');
        openAuthModal();
        return;
    }

    if (!confirm(`Send a test alert email for zone "${zoneName}" to ${currentUser.email}?`)) {
        return;
    }

    try {
        const originalText = btnElement.innerText;
        btnElement.innerText = 'Sending...';
        btnElement.disabled = true;

        const response = await fetch(`${API_BASE_URL}/auth/test-alert`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                email: currentUser.email,
                zone_name: zoneName
            })
        });

        const data = await response.json();

        if (response.ok) {
            showSuccess(`Test alert sent! Check your inbox.`);
        } else {
            showError(data.detail || 'Failed to send test alert');
        }

        btnElement.innerText = originalText;
        btnElement.disabled = false;

    } catch (error) {
        console.error('Test Alert Error:', error);
        showError('Failed to trigger test alert');
        if (btnElement) {
            btnElement.disabled = false;
            btnElement.innerText = '⚠️ Error';
        }
    }
}
