(function () {
    // ================================================
    // SDARS - CORE System JavaScript (Optimized)
    // ================================================

    window.API_BASE_URL = 'http://localhost:8000/api';
    const API_BASE_URL = window.API_BASE_URL;

    // ===== Theme & UI =====
    function applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('sdars_theme', theme);
        const btn = document.getElementById('themeToggleBtn');
        if (btn) {
            btn.innerHTML = theme === 'dark' ? '☀️' : '🌙';
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
            'font-size: 1.1rem',
            'display: flex',
            'align-items: center',
            'justify-content: center',
            'transition: all 0.3s ease',
            'flex-shrink: 0',
            'margin-left: 8px'
        ].join(';');
        btn.title = 'Switch to Light Mode';
        btn.innerHTML = '☀️';
        btn.onmouseover = () => { btn.style.background = 'rgba(255,255,255,0.15)'; btn.style.transform = 'scale(1.1) rotate(20deg)'; };
        btn.onmouseout = () => { btn.style.background = 'rgba(255,255,255,0.07)'; btn.style.transform = 'scale(1) rotate(0deg)'; };
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
            const icons = { success: '✅', error: '❌', warning: '⚠️', info: 'ℹ️', fire: '🔥', flood: '🌊', cyclone: '🌪️' };
            const colors = { success: '#4caf50', error: '#f44336', warning: '#ff9800', info: '#2196f3', fire: '#ff5722' };
            const el = document.createElement('div');
            el.style.cssText = `background:rgba(19,24,37,0.95); backdrop-filter:blur(20px); border:1px solid rgba(255,255,255,0.1); border-left:4px solid ${colors[t] || '#2196f3'}; border-radius:12px; padding:16px; color:white; box-shadow:0 8px 32px rgba(0,0,0,0.5); transition:all 0.3s ease; display:flex; gap:12px;`;
            el.innerHTML = `<div>${icons[t] || 'ℹ️'}</div><div style="flex:1; font-size:14px;">${m}</div><button onclick="this.parentElement.remove()" style="background:none; border:none; color:#6b7a99; cursor:pointer;">✕</button>`;
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
                        <span style="margin-right:10px;">🔍</span>
                        <input type="text" id="globalSearchInput" placeholder="Search worldwide..." style="width:100%; background:none; border:none; color:white; outline:none; font-size:14px; padding:8px 0;">
                        <button onclick="useMyLoc()" style="background:none; border:none; cursor:pointer;">📍</button>
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
                    c.innerHTML = high.map(a => `<div style="margin-right:50px;">🚨 <strong>${a.severity}:</strong> ${a.location?.name}: ${a.title}</div>`).join('');
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
