

const errorBannerHTML = `
<div id="globalErrorBanner" style="display: none; background: #ef4444; color: white; text-align: center; padding: 10px; font-weight: bold; position: fixed; top: 0; width: 100%; z-index: 9999; box-shadow: 0 4px 6px rgba(0,0,0,0.3);">
    [SYSTEM OFFLINE] Unable to reach SDARS Backend Servers. Please check your network connection.
</div>
`;

document.addEventListener("DOMContentLoaded", () => {
    // Inject components
    const navHTML = `
<nav class="navbar">
    <div class="nav-container">
        <div class="nav-logo">
            <img src="logo.png?v=2" alt="SDARS Logo" class="logo-image">
            <span class="logo-fallback"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#00e5ff" stroke-width="2"><circle cx="12" cy="12" r="2"/><path d="M16.24 7.76a6 6 0 0 1 0 8.49m-8.48-.01a6 6 0 0 1 0-8.49m11.31-2.82a10 10 0 0 1 0 14.14m-14.14 0a10 10 0 0 1 0-14.14"/></svg></span>
            <div class="logo-text">
                <h1>SDARS</h1>
                <p>TACTICAL INTELLIGENCE HUB</p>
            </div>
        </div>
        <ul class="nav-menu">
            <li><a href="index.html" class="nav-link">DASHBOARD</a></li>
            <li><a href="map.html" class="nav-link">STRATEGIC MAP</a></li>
            <li><a href="navigation.html" class="nav-link">NAVIGATOR</a></li>
            <li><a href="3d-view.html" class="nav-link">WAR ROOM</a></li>
            <li><a href="prediction.html" class="nav-link">AI SCAN</a></li>
            <li><a href="zones.html" class="nav-link">ZONES</a></li>
            <li><a href="alerts.html" class="nav-link">ALERTS</a></li>
            <!-- Login Button -->
            <li><a href="#" class="nav-link" id="loginBtn" onclick="openAuthModal()">LOGIN</a></li>
            <li id="userProfileDisplay" style="display: none; align-items: center; gap: 8px;">
                <span style="font-size: 12px; color: #a8b3cf;" id="userEmailDisplay"></span>
                <button onclick="logout()"
                    style="background: none; border: 1px solid rgba(255,255,255,0.2); color: white; border-radius: 4px; padding: 2px 6px; cursor: pointer; font-size: 10px;">LOGOUT</button>
            </li>
        </ul>
    </div>
</nav>
`;
    const footerHTML = `
<footer class="footer">
    <p>SDARS - AI-Based Satellite-Driven Smart Disaster Alert and Rescue System</p>
    <p>Powered by Multi-Modal AI | Real-Time Monitoring Active</p>
</footer>
`;

    const mobileBottomNavHTML = `
<nav class="mobile-bottom-nav">
    <a href="index.html" class="mobile-nav-link" id="m-nav-index.html">
        <span style="display: flex; justify-content: center; margin-bottom: 2px;"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg></span><small>Home</small>
    </a>
    <a href="map.html" class="mobile-nav-link" id="m-nav-map.html">
        <span style="display: flex; justify-content: center; margin-bottom: 2px;"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="3 6 9 3 15 6 21 3 21 18 15 21 9 18 3 21"/><line x1="9" x2="9" y1="3" y2="18"/><line x1="15" x2="15" y1="6" y2="21"/></svg></span><small>Map</small>
    </a>
    <a href="3d-view.html" class="mobile-nav-link" id="m-nav-3d-view.html">
        <span style="display: flex; justify-content: center; margin-bottom: 2px;"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"/><path d="M2 12h20"/></svg></span><small>3D Room</small>
    </a>
    <a href="prediction.html" class="mobile-nav-link" id="m-nav-prediction.html">
        <span style="display: flex; justify-content: center; margin-bottom: 2px;"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 2a10 10 0 0 1 10 10"/><path d="m12 12 5-5"/></svg></span><small>AI Scan</small>
    </a>
</nav>
`;
    const authHTML = `
<div id="authModal" class="modal-backdrop"
    style="display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.8); z-index: 2000; align-items: center; justify-content: center;">
    <div class="auth-card"
        style="background: #0d1117; border: 1px solid rgba(255,255,255,0.1); padding: 30px; border-radius: 12px; width: 350px; text-align: center; position: relative;">
        <img src="logo.png" alt="SDARS"
            style="height: 60px; margin-bottom: 20px; filter: drop-shadow(0 0 8px rgba(0, 229, 255, 0.3));">
        <button onclick="closeAuthModal()"
            style="position: absolute; top: 10px; right: 10px; background: none; border: none; color: white; cursor: pointer; font-size: 16px;">&times;</button>
        <h2
            style="margin-bottom: 10px; color: white; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 15px;">
            SECURE ACCESS</h2>

        <!-- Step 1: Email -->
        <div id="stepEmail">
            <p style="color: #a8b3cf; font-size: 14px; margin-bottom: 20px;">Enter your email to receive a
                verification code.</p>
            <input type="email" id="authEmail" placeholder="name@agency.com"
                style="width: 100%; padding: 12px; margin-bottom: 15px; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); color: white; border-radius: 6px;">
            <button class="btn-primary" onclick="requestOTP()" style="width: 100%; justify-content: center;">SEND
                CODE</button>
        </div>

        <!-- Step 2: OTP -->
        <div id="stepOTP" style="display: none;">
            <p style="color: #a8b3cf; font-size: 14px; margin-bottom: 20px;">Enter the 6-digit code sent to your
                email.</p>
            <div style="margin-bottom: 10px; font-weight: bold; color: #00f2ff;" id="otpDemoHint"></div>
            <input type="text" id="authOTP" placeholder="000000" maxlength="6"
                style="width: 100%; padding: 12px; margin-bottom: 15px; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); color: white; border-radius: 6px; letter-spacing: 5px; text-align: center; font-size: 18px;">
            <button class="btn-primary" onclick="verifyOTP()" style="width: 100%; justify-content: center;">VERIFY
                ACCESS</button>
            <button onclick="backToEmail()"
                style="background: none; border: none; color: #a8b3cf; margin-top: 15px; cursor: pointer; font-size: 12px; text-decoration: underline;">Change
                Email</button>
        </div>
    </div>
</div>
`;
    
    // Find where to put nav
    const body = document.body;
    
    // We insert nav at the top
    const navContainer = document.createElement('div');
    navContainer.innerHTML = navHTML;
    
    // Insert error banner at the very top
    const bannerContainer = document.createElement('div');
    bannerContainer.innerHTML = errorBannerHTML;
    body.insertBefore(bannerContainer.firstElementChild, body.firstChild);
    
    // Offline listener
    window.addEventListener('offline', () => {
        document.getElementById('globalErrorBanner').style.display = 'block';
    });
    
    window.addEventListener('online', () => {
        document.getElementById('globalErrorBanner').style.display = 'none';
    });
    
    window.showApiFailure = (message) => {
        const banner = document.getElementById('globalErrorBanner');
        banner.innerHTML = `[API ERROR] ${message || "Unable to reach SDARS Backend."}`;
        banner.style.display = 'block';
        setTimeout(() => {
            banner.style.display = 'none';
        }, 5000);
    };

    // Set active nav link
    const path = window.location.pathname;
    const page = path.split("/").pop() || "index.html";
    
    // We only inject the generic nav and footer if it's NOT the 3D War Room
    if (page !== "3d-view.html") {
        body.insertBefore(navContainer.firstElementChild, body.firstChild);
        
        // Footer
        const footerContainer = document.createElement('div');
        footerContainer.innerHTML = footerHTML;
        body.appendChild(footerContainer.firstElementChild);
    }
    
    // Auth modal
    const authContainer = document.createElement('div');
    authContainer.innerHTML = authHTML;
    body.appendChild(authContainer.firstElementChild);

    document.querySelectorAll(".nav-link").forEach(link => {
        if (link.getAttribute("href") === page) {
            link.classList.add("active");
        }
    });

    // Inject mobile bottom nav
    const mNavContainer = document.createElement('div');
    mNavContainer.innerHTML = mobileBottomNavHTML;
    body.appendChild(mNavContainer.firstElementChild);

    const mNavLink = document.getElementById("m-nav-" + page);
    if(mNavLink) mNavLink.style.color = "var(--accent-signal)";
});
