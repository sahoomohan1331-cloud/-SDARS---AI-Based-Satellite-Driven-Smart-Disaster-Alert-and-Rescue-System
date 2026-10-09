(function () {
    // ================================================
    // SDARS - CORE System JavaScript (Optimized)
    // ================================================

    const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
    window.API_BASE_URL = (isLocal && window.location.port === '5500') ? `http://${window.location.hostname || '127.0.0.1'}:8000/api` : '/api';
    const API_BASE_URL = window.API_BASE_URL;

    // ===== Theme & UI =====
    const sunIcon = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="4"/><path d="M12 2v2"/><path d="M12 20v2"/><path d="m4.93 4.93 1.41 1.41"/><path d="m17.66 17.66 1.41 1.41"/><path d="M2 12h2"/><path d="M20 12h2"/><path d="m6.34 17.66-1.41 1.41"/><path d="m19.07 4.93-1.41 1.41"/></svg>';
    const moonIcon = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"/></svg>';

    function applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('sdars_theme', theme);
        const btn = document.getElementById('themeToggleBtn');
        if (btn) {
            btn.innerHTML = theme === 'dark' ? sunIcon : moonIcon;
            btn.title = theme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode';
        }
    }

    function injectThemeToggle() {
        const nav = document.querySelector('.nav-container');
        if (!nav || document.getElementById('themeToggleBtn')) return;
        const btn = document.createElement('button');
        btn.id = 'themeToggleBtn';
        btn.style.cssText = [
            'background: rgba(255,255,255,0.07)',
            'border: 1px solid rgba(255,255,255,0.15)',
            'color: white',
            'width: 38px',
            'height: 38px',
            'border-radius: 50%',
            'cursor: pointer',
            'display: flex',
            'align-items: center',
            'justify-content: center',
            'transition: all 0.3s ease',
            'flex-shrink: 0',
            'margin-left: 8px'
        ].join(';');
        btn.title = 'Switch to Light Mode';
        btn.innerHTML = sunIcon;
        btn.onmouseover = () => { btn.style.background = 'rgba(255,255,255,0.15)'; btn.style.transform = 'scale(1.05)'; };
        btn.onmouseout = () => { btn.style.background = 'rgba(255,255,255,0.07)'; btn.style.transform = 'scale(1)'; };
        btn.onclick = () => {
            const current = document.documentElement.getAttribute('data-theme') || 'dark';
            applyTheme(current === 'dark' ? 'light' : 'dark');
        };
        nav.appendChild(btn);
    }

    function initUI() {
        // Theme — apply saved preference immediately
        const savedTheme = localStorage.getItem('sdars_theme') || 'dark';
        applyTheme(savedTheme);

        // Inject toggle button into navbar
        injectThemeToggle();

        // Mobile Menu
        const mBtn = document.querySelector('.mobile-menu-toggle');
        const mMenu = document.querySelector('.nav-menu');
        if (mBtn && mMenu) mBtn.onclick = () => mMenu.classList.toggle('active');

        // Reveal animations
        document.querySelectorAll('.hero-dashboard, .stats-grid, .quick-actions').forEach((el, i) => {
            el.style.opacity = '0'; el.style.transform = 'translateY(20px)';
            el.style.transition = `all 0.6s ease ${i * 0.1}s`;
            setTimeout(() => { el.style.opacity = '1'; el.style.transform = 'translateY(0)'; }, 100);
        });
    }

    // ===== Notification System =====
    class NotifSys {
        constructor() { this.init(); }
        init() {
            if (document.getElementById('notifC')) return;
            const c = document.createElement('div'); c.id = 'notifC';
            c.style.cssText = 'position:fixed; top:80px; right:20px; z-index:10000; display:flex; flex-direction:column; gap:10px; max-width:400px;';
            document.body.appendChild(c);
        }
        show(m, t = 'info') {
            const icons = {
                success: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>',
                error: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#ef4444" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>',
                warning: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#f59e0b" stroke-width="2"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
                info: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#00f2ff" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>',
                fire: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#ff4d00" stroke-width="2"><path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 0 0 2.5 2.5z"/></svg>',
                flood: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#00f2ff" stroke-width="2"><path d="M2 6c.6.5 1.2 1 2.5 1C7 7 7 5 9.5 5c2.6 0 2.4 2 5 2 2.5 0 2.5-2 5-2 1.3 0 1.9.5 2.5 1"/><path d="M2 12c.6.5 1.2 1 2.5 1 2.5 0 2.5-2 5-2 2.6 0 2.4 2 5 2 2.5 0 2.5-2 5-2 1.3 0 1.9.5 2.5 1"/></svg>',
                cyclone: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#00f2ff" stroke-width="2"><path d="M17.7 7.7a2.5 2.5 0 1 1 1.8 4.3H2"/><path d="M9.6 4.6A2 2 0 1 1 11 8H2"/></svg>'
            };
            const colors = { success: '#10b981', error: '#ef4444', warning: '#f59e0b', info: '#00f2ff', fire: '#ff4d00' };
            const el = document.createElement('div');
            el.style.cssText = `background:rgba(19,24,37,0.95); backdrop-filter:blur(20px); border:1px solid rgba(255,255,255,0.1); border-left:4px solid ${colors[t] || '#00f2ff'}; border-radius:12px; padding:16px; color:white; box-shadow:0 8px 32px rgba(0,0,0,0.5); transition:all 0.3s ease; display:flex; gap:12px; align-items:center;`;
            el.innerHTML = `<div style="display:flex; align-items:center;">${icons[t] || icons.info}</div><div style="flex:1; font-size:14px;">${m}</div><button onclick="this.parentElement.remove()" style="background:none; border:none; color:#6b7a99; cursor:pointer; font-size:16px;">&times;</button>`;
            document.getElementById('notifC').appendChild(el);
            setTimeout(() => el.style.transform = 'translateX(0)', 10);
            setTimeout(() => { el.style.opacity = '0'; setTimeout(() => el.remove(), 300); }, 5000);
        }
    }
    const nsys = new NotifSys();
    window.showError = (m) => nsys.show(m, 'error');
    window.showSuccess = (m) => nsys.show(m, 'success');

    // ===== Global Search =====
    class GlobalSearch {
        constructor() { this.init(); }
        init() {
            const nav = document.querySelector('.nav-container');
            if (!nav || document.getElementById('globalSearchInput')) return;
            const html = `
                <div class="nav-search" style="flex:1; max-width:400px; margin:0 20px; position:relative;">
                    <div style="display:flex; align-items:center; background:rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.1); border-radius:50px; padding:4px 15px;">
                        <span style="margin-right:10px; display:flex; align-items:center; color:var(--accent-signal);"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg></span>
                        <input type="text" id="globalSearchInput" placeholder="Search worldwide..." style="width:100%; background:none; border:none; color:white; outline:none; font-size:14px; padding:8px 0;">
                        <button onclick="useMyLoc()" style="background:none; border:none; cursor:pointer; color:var(--accent-signal); display:flex; align-items:center;" title="Use My Location"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76"/></svg></button>
                    </div>
                    <div id="searchDrop" style="position:absolute; top:100%; left:0; width:100%; background:#0d1117; border:1px solid #333; border-radius:8px; display:none; z-index:1001; margin-top:10px; max-height:300px; overflow-y:auto;"></div>
                </div>`;
            const badge = nav.querySelector('.status-badge') || nav.querySelector('.nav-menu');
            badge.insertAdjacentHTML('beforebegin', html);
            this.attach();
        }
        attach() {
            const input = document.getElementById('globalSearchInput');
            const drop = document.getElementById('searchDrop');
            input.oninput = async (e) => {
                const q = e.target.value.trim();
                if (q.length < 2) return drop.style.display = 'none';
                drop.style.display = 'block';
                drop.innerHTML = '<div style="padding:10px; color:#6b7a99; font-size:12px;">Scanning...</div>';
                try {
                    const r = await fetch(`https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(q)}&format=json&limit=5`, { headers: { 'User-Agent': 'SDARS-System/1.0' } });
                    const res = await r.json();
                    drop.innerHTML = res.map(l => `
                        <div onclick="selectLoc('${l.display_name}', ${l.lat}, ${l.lon})" style="padding:10px; border-bottom:1px solid #333; cursor:pointer; font-size:13px;">
                            <strong>${l.display_name.split(',')[0]}</strong><br>
                            <small style="color:#6b7a99;">${l.display_name}</small>
                        </div>`).join('') || '<div style="padding:10px;">No results</div>';
                } catch (e) { }
            };
            document.onclick = (e) => { if (!e.target.closest('.nav-search')) drop.style.display = 'none'; };
        }
    }

    // ===== Alert Ticker =====
    async function updateTicker() {
        const c = document.getElementById('tickerC');
        if (!c) return;
        try {
            const r = await fetch(`${API_BASE_URL}/alerts/active`);
            if (r.ok) {
                const d = await r.json();
                const high = (d.alerts || []).filter(a => a.severity === 'CRITICAL' || a.severity === 'HIGH');
                if (high.length > 0) {
                    c.innerHTML = high.map(a => `<div style="margin-right:50px; display:inline-flex; align-items:center; gap:6px;"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#ef4444" stroke-width="2"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg> <strong>${a.severity}:</strong> ${a.location?.name}: ${a.title}</div>`).join('');
                    c.parentElement.style.display = 'block';
                } else c.parentElement.style.display = 'none';
            }
        } catch (e) { }
    }

    window.selectLoc = (name, lat, lon) => {
        window.location.href = `prediction.html?lat=${lat}&lon=${lon}&name=${encodeURIComponent(name)}`;
    };

    window.useMyLoc = () => {
        navigator.geolocation.getCurrentPosition(p => selectLoc("Current Location", p.coords.latitude, p.coords.longitude));
    };

    // ===== Initialization =====
    document.addEventListener('DOMContentLoaded', () => {
        initUI();
        new GlobalSearch();

        // Create Ticker Container
        const tc = document.createElement('div');
        tc.style.cssText = 'position:fixed; bottom:0; left:0; right:0; background:rgba(13,17,23,0.95); backdrop-filter:blur(10px); color:white; padding:10px 0; z-index:9999; border-top:1px solid rgba(239,68,68,0.3); overflow:hidden; display:none;';
        tc.innerHTML = `<div id="tickerC" style="display:flex; white-space:nowrap; animation:tScroll 30s linear infinite;"></div><style>@keyframes tScroll { 0%{transform:translateX(100%)} 100%{transform:translateX(-100%)} }</style>`;
        document.body.appendChild(tc);
        updateTicker();
        setInterval(updateTicker, 60000);
    });

    Object.assign(window, {
        fetchPrediction: async (lat, lon, name) => {
            const r = await fetch(`${API_BASE_URL}/predict`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ lat, lon, name }) });
            return r.ok ? await r.json() : null;
        },
        viewLoc: (n, lat, lon) => window.location.href = `prediction.html?lat=${lat}&lon=${lon}&name=${encodeURIComponent(n)}`,
        goToDashboard: () => window.location.href = 'index.html',
        goToMap: () => window.location.href = 'map.html',
        goToPrediction: () => window.location.href = 'prediction.html',
        getURLParams: () => {
            const p = new URLSearchParams(window.location.search);
            return { lat: p.get('lat'), lon: p.get('lon'), name: p.get('name') };
        }
    });

})();
