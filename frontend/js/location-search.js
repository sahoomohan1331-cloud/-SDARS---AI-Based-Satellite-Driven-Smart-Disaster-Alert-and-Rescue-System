(function () {
    // ================================================
    // Google Maps Style Location Search with Autocomplete
    // Uses OpenStreetMap Nominatim API (FREE)
    // ================================================

    let searchTimeout = null;
    let currentSearchController = null;

    // Initialize search functionality
    document.addEventListener('DOMContentLoaded', () => {
        initializeLocationSearch();
    });

    function initializeLocationSearch() {
        const searchInput = document.getElementById('locationSearchInput');
        const suggestionsBox = document.getElementById('searchSuggestions');

        if (!searchInput) return;

        // Input event for autocomplete
        searchInput.addEventListener('input', (e) => {
            const query = e.target.value.trim();

            // Clear previous timeout
            if (searchTimeout) clearTimeout(searchTimeout);

            if (query.length < 2) {
                hideSuggestions();
                return;
            }

            // Debounce - wait 300ms after user stops typing
            searchTimeout = setTimeout(() => {
                fetchSuggestions(query);
            }, 300);
        });

        // Handle Enter key
        searchInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                const query = searchInput.value.trim();
                if (query) {
                    searchLocation(query);
                    hideSuggestions();
                }
            }

            // Arrow key navigation
            if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
                navigateSuggestions(e.key === 'ArrowDown' ? 1 : -1);
                e.preventDefault();
            }

            // Escape to close
            if (e.key === 'Escape') {
                hideSuggestions();
            }
        });

        // Close suggestions when clicking outside
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.search-container')) {
                hideSuggestions();
            }
        });

        // Focus styling
        searchInput.addEventListener('focus', () => {
            if (!searchInput.parentElement.classList.contains('crisis-glow')) {
                searchInput.parentElement.style.boxShadow = '0 0 0 3px rgba(102, 126, 234, 0.3)';
            }
        });

        searchInput.addEventListener('blur', () => {
            if (!searchInput.parentElement.classList.contains('crisis-glow')) {
                searchInput.parentElement.style.boxShadow = 'none';
            }
        });
    }

    // Fetch autocomplete suggestions from Nominatim
    async function fetchSuggestions(query) {
        const suggestionsBox = document.getElementById('searchSuggestions');

        // Cancel previous request
        if (currentSearchController) {
            currentSearchController.abort();
        }
        currentSearchController = new AbortController();

        try {
            // Show loading state
            suggestionsBox.innerHTML = `
                <div style="padding: 15px; text-align: center; color: #a8b3cf;">
                    <div class="loading-spinner" style="margin: 0 auto 10px;"></div>
                    Searching "${query}"...
                </div>
            `;
            suggestionsBox.style.display = 'block';

            // Fetch from SDARS Intelligence Backend (Proxies to Nominatim + Risk Analysis)
            const response = await fetch(
                `${window.API_BASE_URL || 'http://localhost:8000/api'}/autocomplete/${encodeURIComponent(query)}`,
                {
                    signal: currentSearchController.signal
                }
            );

            if (!response.ok) throw new Error('Search failed');

            const data = await response.json();
            const results = data.suggestions || [];

            if (results.length === 0) {
                suggestionsBox.innerHTML = `
                    <div style="padding: 20px; text-align: center; color: #6b7a99;">
                        <span style="font-size: 24px;">🔍</span>
                        <p style="margin: 10px 0 0;">No locations found for "${query}"</p>
                        <small>Try a different spelling or add state/country name</small>
                    </div>
                `;
                return;
            }

            // Build suggestions HTML
            let html = '';
            results.forEach((result, index) => {
                const displayName = result.display_name;
                const shortName = result.name;
                const locationType = result.type.charAt(0).toUpperCase() + result.type.slice(1);

                // ⭐ THREAT SCANNING UI
                const risk = result.risk_level || 'NORMAL';
                const threat = result.primary_threat || 'SAFE';

                let badgeHtml = '';
                if (risk !== 'NORMAL' && risk !== 'LOW') {
                    const color = risk === 'CRITICAL' ? '#ff0000' : (risk === 'HIGH' ? '#ff4d00' : '#ffab00');
                    badgeHtml = `
                        <div class="risk-ping-badge" style="background: ${color}22; border: 1px solid ${color}; color: ${color}; font-family: 'JetBrains Mono', monospace;">
                            <span class="ping-dot" style="background: ${color};"></span>
                            ${risk}: ${threat}
                        </div>
                    `;
                }

                html += `
                    <div class="suggestion-item" 
                        data-lat="${result.lat}" 
                        data-lon="${result.lon}"
                        data-name="${shortName}"
                        data-index="${index}"
                        style="padding: 12px 15px; cursor: pointer; border-bottom: 1px solid rgba(255,255,255,0.05); transition: all 0.2s; position: relative; overflow: hidden;">
                        <div style="display: flex; align-items: center; gap: 12px; position: relative; z-index: 1;">
                            <span style="font-size: 20px;">${this.window.getLocationIcon ? window.getLocationIcon(result) : '📍'}</span>
                            <div style="flex: 1;">
                                <div style="display: flex; align-items: center; gap: 8px;">
                                    <div style="color: white; font-weight: 600; font-size: 14px;">${shortName}</div>
                                    ${badgeHtml}
                                </div>
                                <div style="color: #6b7a99; font-size: 11px; margin-top: 2px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 320px;">
                                    ${displayName}
                                </div>
                            </div>
                            <span style="color: #667eea; font-size: 10px; background: rgba(102,126,234,0.1); padding: 2px 6px; border-radius: 4px; text-transform: uppercase; font-weight: 700; letter-spacing: 0.5px;">
                                ${locationType}
                            </span>
                        </div>
                    </div>
                `;
            });

            suggestionsBox.innerHTML = html;

            // Handle selection for IIFE compatibility
            document.querySelectorAll('.suggestion-item').forEach(item => {
                const isRisk = item.querySelector('.risk-ping-badge');

                item.addEventListener('click', () => {
                    selectSuggestion(item);
                    searchInput.parentElement.classList.remove('crisis-glow');
                });
                item.addEventListener('mouseenter', () => {
                    item.style.background = 'rgba(102, 126, 234, 0.1)';
                    if (isRisk) {
                        searchInput.parentElement.classList.add('crisis-glow');
                        searchInput.parentElement.style.boxShadow = '0 0 15px rgba(239, 68, 68, 0.5)';
                    }
                });
                item.addEventListener('mouseleave', () => {
                    item.style.background = 'transparent';
                    if (isRisk) {
                        searchInput.parentElement.classList.remove('crisis-glow');
                        searchInput.parentElement.style.boxShadow = searchInput === document.activeElement ? '0 0 0 3px rgba(102, 126, 234, 0.3)' : 'none';
                    }
                });
            });

        } catch (error) {
            if (error.name === 'AbortError') return; // Ignore abort errors

            console.error('Search error:', error);
            suggestionsBox.innerHTML = `
                <div style="padding: 20px; text-align: center; color: #ff5722;">
                    <span style="font-size: 24px;">⚠️</span>
                    <p style="margin: 10px 0 0;">Search service unavailable</p>
                    <small>Please try again later</small>
                </div>
            `;
        }
    }

    // Get short location name
    function getShortLocationName(result) {
        const address = result.address || {};

        // Priority: city > town > village > county > state
        return address.city ||
            address.town ||
            address.village ||
            address.county ||
            address.state ||
            address.suburb ||
            result.name ||
            'Unknown Location';
    }

    // Get location type string
    function getLocationType(result) {
        const type = result.type || result.class || '';
        const address = result.address || {};

        if (address.city) return 'City';
        if (address.town) return 'Town';
        if (address.village) return 'Village';
        if (address.state) return 'State';
        if (address.country) return 'Area';

        return type.charAt(0).toUpperCase() + type.slice(1) || 'Location';
    }

    // Get appropriate icon for location type
    function getLocationIcon(result) {
        const address = result.address || {};
        const type = result.type || '';

        if (address.city) return '🏙️';
        if (address.town) return '🏘️';
        if (address.village) return '🏡';
        if (type.includes('water') || type.includes('river')) return '🌊';
        if (type.includes('mountain') || type.includes('peak')) return '⛰️';
        if (type.includes('forest') || type.includes('park')) return '🌲';
        if (type.includes('airport')) return '✈️';
        if (type.includes('hospital')) return '🏥';

        return '📍';
    }

    // Select a suggestion
    function selectSuggestion(element) {
        const lat = parseFloat(element.dataset.lat);
        const lon = parseFloat(element.dataset.lon);
        const name = element.dataset.name;

        // Update search input
        const input = document.getElementById('locationSearchInput');
        if (input) input.value = name;

        // Hide suggestions
        hideSuggestions();

        // Navigate to location and show weather
        goToLocation(lat, lon, name);
    }

    // Navigate to location on map
    async function goToLocation(lat, lon, name) {
        // Show notification
        if (typeof notificationSystem !== 'undefined') {
            notificationSystem.info(`Finding ${name}...`, 2000);
        }

        // Fly to location
        if (typeof map !== 'undefined') {
            map.flyTo([lat, lon], 12, {
                duration: 1.5
            });

            // Fetch and show weather data
            setTimeout(async () => {
                if (typeof showWeatherForLocation !== 'undefined') {
                    await showWeatherForLocation(lat, lon, { lat, lng: lon });
                }

                if (typeof notificationSystem !== 'undefined') {
                    notificationSystem.success(`Loading data for ${name}!`, 3000);
                }
            }, 1500);
        }
    }

    // Use current GPS location
    async function useCurrentLocation() {
        const gpsButton = document.getElementById('gpsButton');
        const gpsText = gpsButton ? gpsButton.querySelector('.gps-text') : null;

        // Show loading state
        if (gpsText) gpsText.textContent = 'Locating...';
        if (gpsButton) {
            gpsButton.style.opacity = '0.7';
            gpsButton.disabled = true;
        }

        if (!navigator.geolocation) {
            if (typeof notificationSystem !== 'undefined') {
                notificationSystem.error('GPS not supported by your browser', 3000);
            }
            resetGpsButton();
            return;
        }

        navigator.geolocation.getCurrentPosition(
            async (position) => {
                const lat = position.coords.latitude;
                const lon = position.coords.longitude;

                // Get location name
                try {
                    const response = await fetch(
                        `https://nominatim.openstreetmap.org/reverse?lat=${lat}&lon=${lon}&format=json`,
                        { headers: { 'User-Agent': 'SDARS-DisasterAlertSystem/1.0' } }
                    );

                    const data = await response.json();
                    const address = data.address || {};
                    // Get cleanest name - prefer city/town/village over municipality
                    const locationName = address.city || address.town || address.village ||
                        address.suburb || address.county || address.state_district ||
                        'Your Location';

                    // Update search input
                    const input = document.getElementById('locationSearchInput');
                    if (input) input.value = locationName;

                    // Navigate to location
                    goToLocation(lat, lon, locationName);

                    if (typeof notificationSystem !== 'undefined') {
                        notificationSystem.success(`Found you at ${locationName}!`, 3000);
                    }

                } catch (error) {
                    console.error('Reverse geocoding error:', error);
                    goToLocation(lat, lon, 'Current Location');
                }

                resetGpsButton();
            },
            (error) => {
                console.error('GPS error:', error);

                let message = 'Unable to get your location';
                if (error.code === 1) message = 'Location access denied. Please enable GPS.';
                if (error.code === 2) message = 'Location unavailable. Try again.';
                if (error.code === 3) message = 'Location request timed out.';

                if (typeof notificationSystem !== 'undefined') {
                    notificationSystem.error(message, 4000);
                }

                resetGpsButton();
            },
            {
                enableHighAccuracy: true,
                timeout: 10000,
                maximumAge: 60000
            }
        );
    }

    function resetGpsButton() {
        const gpsButton = document.getElementById('gpsButton');
        const gpsText = gpsButton ? gpsButton.querySelector('.gps-text') : null;

        if (gpsText) gpsText.textContent = 'My Location';
        if (gpsButton) {
            gpsButton.style.opacity = '1';
            gpsButton.disabled = false;
        }
    }

    // Search location directly
    async function searchLocation(query) {
        if (typeof notificationSystem !== 'undefined') {
            notificationSystem.info(`Searching for "${query}"...`, 2000);
        }

        try {
            const response = await fetch(
                `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(query)}&format=json&limit=1`,
                { headers: { 'User-Agent': 'SDARS-DisasterAlertSystem/1.0' } }
            );

            const results = await response.json();

            if (results.length > 0) {
                const result = results[0];
                const name = getShortLocationName(result);
                goToLocation(parseFloat(result.lat), parseFloat(result.lon), name);
            } else {
                if (typeof notificationSystem !== 'undefined') {
                    notificationSystem.error(`Location "${query}" not found`, 3000);
                }
            }
        } catch (error) {
            console.error('Search error:', error);
            if (typeof notificationSystem !== 'undefined') {
                notificationSystem.error('Search failed. Please try again.', 3000);
            }
        }
    }

    // Hide suggestions dropdown
    function hideSuggestions() {
        const suggestionsBox = document.getElementById('searchSuggestions');
        if (suggestionsBox) {
            suggestionsBox.style.display = 'none';
        }
    }

    // Keyboard navigation for suggestions
    let selectedSuggestionIndex = -1;

    function navigateSuggestions(direction) {
        const items = document.querySelectorAll('.suggestion-item');
        if (items.length === 0) return;

        // Remove previous selection
        items.forEach(item => item.style.background = 'transparent');

        // Update index
        selectedSuggestionIndex += direction;

        if (selectedSuggestionIndex < 0) selectedSuggestionIndex = items.length - 1;
        if (selectedSuggestionIndex >= items.length) selectedSuggestionIndex = 0;

        // Highlight selected
        const selected = items[selectedSuggestionIndex];
        selected.style.background = 'rgba(102, 126, 234, 0.2)';
        selected.scrollIntoView({ block: 'nearest' });

        // Update input
        const input = document.getElementById('locationSearchInput');
        if (input) input.value = selected.dataset.name;
    }

    // Add CSS for loading spinner
    const locSearchStyles = document.createElement('style');
    locSearchStyles.textContent = `
        .loading-spinner {
            width: 24px;
            height: 24px;
            border: 3px solid rgba(102, 126, 234, 0.3);
            border-top: 3px solid #667eea;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .search-suggestions::-webkit-scrollbar {
            width: 8px;
        }
        
        .search-suggestions::-webkit-scrollbar-track {
            background: rgba(255,255,255,0.05);
            border-radius: 4px;
        }
        
        .search-suggestions::-webkit-scrollbar-thumb {
            background: rgba(102, 126, 234, 0.5);
            border-radius: 4px;
        }
        
        #locationSearchInput::placeholder {
            color: #6b7a99;
        }

        .risk-ping-badge {
            display: flex;
            align-items: center;
            gap: 5px;
            font-size: 9px;
            font-weight: 800;
            padding: 2px 6px;
            border-radius: 4px;
            text-transform: uppercase;
        }

        .ping-dot {
            width: 6px;
            height: 6px;
            border-radius: 50%;
            display: inline-block;
            animation: pulse-risk 1.2s infinite;
        }

        @keyframes pulse-risk {
            0% { transform: scale(0.9); opacity: 0.8; }
            50% { transform: scale(1.2); opacity: 1; }
            100% { transform: scale(0.9); opacity: 0.8; }
        }

        .crisis-glow {
            border-color: #ef4444 !important;
            box-shadow: 0 0 15px rgba(239, 68, 68, 0.5) !important;
            transition: all 0.3s ease;
        }
        
        @media (max-width: 600px) {
            .gps-text {
                display: none;
            }
            
            #gpsButton {
                padding: 10px !important;
            }
        }
    `;
    document.head.appendChild(locSearchStyles);

    // Expose necessary functions to global scope
    window.useCurrentLocation = useCurrentLocation;
    window.searchLocation = searchLocation;
    window.selectSuggestion = selectSuggestion;

    console.log('🔍 Google Maps style search initialized!');
})();
