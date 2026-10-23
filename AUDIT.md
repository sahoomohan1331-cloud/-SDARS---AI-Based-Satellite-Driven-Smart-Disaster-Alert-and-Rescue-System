# SDARS Scientific & Architectural Codebase Audit

**Date:** October 2026  
**Audit Scope:** Full codebase audit covering `backend/`, `frontend/`, and root architecture documentation (`README.md`, `SDARS_Architecture_Overview.md`).  
**Tone:** Blunt, objective, evidence-based. No claims are softened.

---

## 1. Feature & Claim Verification Matrix

| Claim | Where Claimed (File:Line) | Implemented? | Evidence (File:Function) |
|---|---|---|---|
| **Sentinel-2 NDVI/NDWI Ingestion** | `README.md:15-18`<br>`SDARS_Architecture_Overview.md:9`<br>`backend/README.md:31, 39, 208-212` | **No** | `backend/data_collectors/satellite_collector.py:225-275`<br>The function `_process_real_satellite_data` containing Sentinel-2 L2A band logic is completely dead code and is never invoked anywhere in the repository. In `get_modis_imagery_analysis` (`satellite_collector.py:128-149`), "NDVI" and "NDWI" are fabricated from an 8-bit rendered false-color PNG of MODIS land surface temperature using heuristic formulas (`1.0 - (mean_val / 255.0)` and `(std_val / 128.0) - 0.2`) and broadcast across a dummy 16x16 matrix. `satellite_collector.py:375` explicitly notes: *"This is a placeholder for actual satellite imagery retrieval"*. |
| **NASA FIRMS Hotspot Ingestion** | `README.md:16, 40`<br>`backend/README.md:19, 31, 198` | **Yes** (with fallback) | `backend/data_collectors/satellite_collector.py:277-338` (`get_nasa_firms_data`)<br>Queries `https://firms.modaps.eosdis.nasa.gov/api/area/csv` using `NASA_API_KEY`, parses CSV coordinates and Fire Radiative Power (FRP), and caches results. If the FIRMS query fails, falls back to NASA EONET wildfire events (`satellite_collector.py:340-363`). |
| **OSRM Hazard-Aware Routing** | `SDARS_Architecture_Overview.md:24`<br>`SDARS_Project_Poster.svg:52` | **Partial** | `backend/services/route_optimizer.py:180-264` (`find_multiple_routes`)<br>Queries public OSRM API (`https://router.project-osrm.org/route/v1`) for standard driving routes. OSRM itself does NOT support dynamic hazard avoidance. Hazard evaluation occurs entirely post-hoc in `calculate_route_safety_score` (`route_optimizer.py:20-158`), which penalizes routes based on proximity to disaster coordinates or road blockages. If fewer than 3 routes return, it synthesizes an alternative by injecting an arbitrary midpoint offset (`lat+0.05, lon+0.05`) into OSRM (`route_optimizer.py:238-243`). |
| **90-Degree Escape Cone** | Prompt audit requirement | **Yes** | `backend/services/route_optimizer.py:266-325` (`calculate_evacuation_route`)<br>Calculates vector bearing away from disaster epicenter (`away_bearing = _calculate_bearing(disaster, current)`). Filters shelters by checking `bearing_diff = abs(shelter_bearing - away_bearing)` with `bearing_diff <= 90 or bearing_diff >= 270`, strictly restricting evacuation targets to the 90° departure cone away from the hazard. |
| **SMS Alerts** | `SDARS_Architecture_Overview.md:25`<br>`backend/README.md:60`<br>`backend/config.py:21-23` | **No** | `backend/services/alert_manager.py:69-74` (`_send_mock_sms`) and `backend/services/advanced_alert_system.py:561-574` (`_send_sms_notification`)<br>Both functions exclusively print mock strings to stdout (`[MOCK SMS SENT]` and `[SMS NOTIFICATION - MOCK]`). Twilio credentials exist in `config.py` and `requirements.txt`, but the Twilio REST client is never initialized or called anywhere in the executable logic. |
| **Email Alerts** | `SDARS_Architecture_Overview.md:25`<br>`backend/README.md:60`<br>`backend/config.py:16-19` | **Yes** | `backend/services/email_service.py:86-102` (`_send_email`) and `backend/services/advanced_alert_system.py:476-511` (`_send_email_notification`)<br>Both services configure Python's standard `smtplib.SMTP`, establish STARTTLS connections to `smtp.gmail.com:587`, authenticate via credentials, and dispatch multi-part HTML/plaintext alert templates. If credentials are unset, they gracefully catch exceptions and log mock warnings. |
| **WebSocket Alerts** | `SDARS_Architecture_Overview.md:21` ("Real-time Analytics Dashboard") | **No** | `backend/api/server.py:1-1286`<br>Zero WebSocket endpoints exist across the entire backend (no `@app.websocket` in `server.py` or any router). In `frontend/js/alert-system.js:85`, `frontend/js/alerts-page.js:60`, and `frontend/js/map.js:1357`, "real-time" alerts are executed purely via client-side `setInterval` HTTP polling cycles (15 to 30 second intervals). |
| **"Neural Network" Wording** | `SDARS_Architecture_Overview.md:1, 13-15, 30`<br>`SDARS_Architecture_Diagram.svg:46-49`<br>`SDARS_Project_Poster.svg:38, 48, 71`<br>`frontend/prediction.html:121, 130-136`<br>`frontend/js/alerts-page.js:485-511` | **No** | `backend/ai_models/train_xgboost_models.py:98`<br>`backend/ai_models/train_models.py`<br>`backend/ai_models/multi_modal_predictor.py:53-81`<br>The AI core consists solely of decision-tree ensembles: `xgboost.XGBClassifier` and `sklearn.ensemble.RandomForestClassifier`. No artificial neural network (PyTorch, TensorFlow, Keras, or MLP) is implemented or run. The claimed "Neural Reasoning Engine" in `frontend/js/alerts-page.js:486` is a static simulated array (`const neuralThoughts = [...]`). |
| **"1km Resolution" Wording** | `backend/data_collectors/weather_collector.py:3, 25`<br>`backend/data_collectors/satellite_collector.py:152` | **No** | `backend/data_collectors/weather_collector.py:49`<br>The collector calls Open-Meteo's standard forecast API. Global numerical weather prediction models underpinning Open-Meteo operate on horizontal resolutions between ~9 km (ECMWF IFS) and ~13-25 km (GFS, ICON). There is no 1 km raw physical resolution. In `satellite_collector.py:152`, `'resolution': '1km'` is a hardcoded metadata dictionary string returned with downscaled 256x256 MODIS image tiles. |
| **"99.5% Accuracy"** | `README.md:130`<br>`frontend/prediction.html:182, 428` | **No** (Fabricated) | `backend/models/model_performance_summary.json`<br>`backend/models/*_metrics.json`<br>`backend/ai_models/train_xgboost_models.py:88-163`<br>The 99.5% figure was derived solely from evaluating models on synthetic datasets with severe class imbalance. Actual validation F1 scores across individual hazards are: Storm Surge: **0.125**, Landslide: **0.2299**, Flood: **0.4812**, Cyclone: **0.5246**, Fire: **0.5263**, Drought: **0.5734**. The headline 99.5% metric is ungrounded in real-world observations. |
| **"<50ms Inference"** | `README.md:131` | **Partial / Misleading** | `backend/ai_models/multi_modal_predictor.py:365-420`<br>`backend/api/prediction_routes.py:53-150`<br>Pure in-memory evaluation of pre-computed feature vectors through XGBoost trees takes ~2-5 ms. However, the end-to-end `/api/predict` pipeline synchronously executes network requests to Open-Meteo (`timeout=4s`), NASA GIBS (`timeout=1.5s`), and NASA FIRMS (`timeout=1.5s`). Real-world uncached inference response time ranges from **1,200 ms to 4,500 ms+**. |
| **USGS Earthquake Feed** | `SDARS_Architecture_Overview.md:11` ("Seismic Activity Streamers: Real-time feeds for earthquake and tectonic monitoring") | **No** | Search for `usgs` / `earthquake` across repository.<br>Zero network calls to USGS or any seismic streaming API exist. "Earthquake" appears only as an unused string literal in default alert preferences (`backend/services/advanced_alert_system.py:156`) and an option in the mobile UI report dropdown (`frontend/mobile_app.html:438`). |
| **CWC River Gauge Data (Live vs Seeded)** | `frontend/mobile_app.html:168-171, 995`<br>`frontend/map.html:78-79`<br>`frontend/js/map.js:1001` | **No** (100% Seeded Demo Data) | `backend/api/disaster_management_routes.py:85-96` (`seed_default_data_if_empty`)<br>There is no integration with the Central Water Commission (CWC). The database contains exactly 6 static river stations hardcoded at boot (Yamuna at Old Delhi Railway Bridge, Mithi at Kurla, Hooghly at Howrah, Brahmaputra at Guwahati, Godavari at Rajahmundry, Mahanadi at Cuttack). All river readings come from SQLite records. |
| **Citizen Crowd Reports** | `backend/api/disaster_management_routes.py:152-246`<br>`frontend/mobile_app.html:430-480` | **Yes** | `backend/api/disaster_management_routes.py:155` (`submit_crowd_report`), `:186` (`list_crowd_reports`), `:227` (`verify_crowd_report`)<br>Complete working system backed by SQLite table `crowd_reports`. Citizens submit incident reports (location, hazard type, description, severity), and authorities can verify or reject them. |
| **Japan L1-L5 Alert Levels** | `backend/api/server.py:49`<br>`backend/api/command_routes.py:53`<br>`frontend/mobile_app.html:1912`<br>`frontend/js/prediction.js:53-77` | **Yes** | `backend/ai_models/multi_modal_predictor.py:314-337` (`predict_comprehensive`)<br>Explicitly maps hazard risk level and model confidence to Japan's JMA 5-stage evacuation alert scale (`L1 NORMAL`, `L2 WATCH`, `L3 PREPARE`, `L4 EVACUATE`, `L5 EXTREME`). The output is serialized in API responses and rendered as badges in the frontend. |
| **3D CesiumJS Globe** | `SDARS_Architecture_Overview.md:19`<br>`frontend/3d-view.html` | **Yes** | `frontend/3d-view.html:739-1250` (`initCesium`)<br>Imports CesiumJS 1.114 via CDN, loads an Ellipsoid / WorldTerrain provider with OpenStreetMap and Sentinel imagery overlays, plots 3D extruded risk beacons, and supports camera flight paths. |
| **ISS Tracking** | Prompt audit requirement | **No** | Search for `iss` / `orbit` across repository.<br>No ISS tracking, TLE satellite propagation, or Space-Track/Open-Notify APIs exist. Satellite pass times in `frontend/mobile_app.html:2130-2156` are hardcoded static HTML elements. |

---

## 2. Contradictions Between Documentation and Code

1. **Neural Network vs. Decision Trees / Random Forests / Keras .h5**
   - *Documentation:* `SDARS_Architecture_Overview.md:14` states: *"Hazard Prediction Model: A multi-layered neural network that calculates risk levels..."*
   - *Configuration:* `backend/config.py:39-41` specifies Keras file paths: `fire_detection_model.h5`, `flood_detection_model.h5`, `cyclone_prediction_model.h5`.
   - *Codebase Reality:* No neural networks or `.h5` model files exist. `backend/ai_models/multi_modal_predictor.py` exclusively loads Scikit-Learn Random Forests (`*_risk_model.joblib`) and XGBoost classifiers (`*_model.joblib`).

2. **Claimed 99.5% Model Accuracy vs. Real Validation Metrics**
   - *Documentation:* `README.md:130` claims: `Model Accuracy: ~99.5% (Physics-Calibrated validation)`. `frontend/prediction.html:182` renders hardcoded text `Acc: 99.5% | F1: 98.5%`.
   - *Codebase Reality:* Real test metrics in `backend/models/model_performance_summary.json` reveal that several hazard models perform exceptionally poorly:
     - Storm Surge: F1 score of **0.125** (Recall: 0.0769)
     - Landslide: F1 score of **0.2299** (Recall: 0.1370)
     - Flood: F1 score of **0.4812**
     - Cyclone: F1 score of **0.5246**
     - Fire: F1 score of **0.5263**
     The 99.5% figure was fabricated from trivial true-negative accuracy on heavily imbalanced synthetic sets.

3. **Sentinel-2 Satellite Integration vs. Unimplemented Placeholder**
   - *Documentation:* `backend/README.md:31` and `SDARS_Architecture_Overview.md:9` claim live Sentinel Hub satellite image ingestion.
   - *Documentation Contradiction:* `README.md:139` contradicts this under Future Contributions: *"1. Real Sentinel-2 satellite imagery API integration [needed]"*.
   - *Codebase Reality:* `backend/data_collectors/satellite_collector.py` contains unused Sentinel credentials. Function `_process_real_satellite_data` is uncalled dead code. Line 375 admits it is an unintegrated placeholder.

4. **Seismic Monitoring vs. Zero Implementation**
   - *Documentation:* `SDARS_Architecture_Overview.md:11` claims: *"Seismic Activity Streamers: Real-time feeds for earthquake and tectonic monitoring."*
   - *Codebase Reality:* No seismic API or USGS feed exists anywhere in the repository.

5. **MongoDB vs. SQLite**
   - *Documentation:* `backend/config.py:29-30` configures `MONGODB_URI = 'mongodb://localhost:27017/'` and `DATABASE_NAME = 'sdars_db'`. `backend/README.md:283` lists MongoDB integration as a future feature.
   - *Codebase Reality:* The application relies entirely on SQLite (`sdars_database.db`) accessed via SQLAlchemy in `backend/db/database.py`. MongoDB is never connected.

6. **Automated 15-Minute Data Ingestion vs. On-Demand Polling**
   - *Documentation:* `SDARS_Architecture_Overview.md:29` claims: *"Raw satellite and weather data are pulled every 15 minutes."*
   - *Codebase Reality:* No background cron job, Celery worker, or scheduled task exists to ingest data every 15 minutes. Ingestion happens strictly on-demand when a user initiates a request.

7. **AI Evacuation Router vs. Heuristic Post-Scoring of OSRM**
   - *Documentation:* `SDARS_Architecture_Overview.md:24` claims: *"AI-Powered Safety Router: A custom routing engine that analyzes disaster risk along paths and avoids hazard zones."*
   - *Documentation Contradiction:* `README.md:141` lists *"Evacuation route optimization AI"* under Contributing / Future Work.
   - *Codebase Reality:* `route_optimizer.py` does not contain a custom AI pathfinder. It fetches default driving paths from public OSRM and evaluates waypoint safety post-hoc using Euclidean distance checks against active hazard zones.

8. **"Neural Reasoning Engine" vs. Static Mock Array**
   - *Documentation:* `SDARS_Architecture_Overview.md:15` claims: *"Neural Reasoning Engine: Generates the 'Reasoning Log' which translates complex AI weights into human-readable logical steps for responders."*
   - *Codebase Reality:* `frontend/js/alerts-page.js:486` populates the log using a static, hardcoded array of mock strings (`const neuralThoughts = [...]`). In `multi_modal_predictor.py`, reasoning output is produced by standard procedural `if/elif` string concatenation.

---

## 3. Analysis of the 13 Multi-Modal Model Features

The unified feature extraction schema in `backend/ai_models/multi_modal_predictor.py:82-118` builds a 13-feature vector:
`['temp', 'hum', 'wind', 'wind_gusts', 'pressure', 'soil_moisture', 'rain_1h', 'forecast_rain_24h', 'elevation', 'slope', 'ndvi', 'ndwi', 'hotspots']`

| # | Feature Name | Source During Live Inference | Status | Implementation Details & Fallback Behavior |
|---|---|---|---|---|
| 1 | `temp` | Open-Meteo API | **Live** | Fetched from `current.temperature_2m` (`weather_collector.py:70`). Falls back to `25.0`°C if API fails. |
| 2 | `hum` | Open-Meteo API | **Live** | Fetched from `current.relative_humidity_2m` (`weather_collector.py:73`). Falls back to `50.0`% if API fails. |
| 3 | `wind` | Open-Meteo API | **Live** | Fetched from `current.wind_speed_10m` (`weather_collector.py:74`). Falls back to `10.0` km/h if API fails. |
| 4 | `wind_gusts` | Open-Meteo API | **Live** | Fetched from `current.wind_gusts_10m` (`weather_collector.py:76`). Falls back to current `wind_speed` or `10.0` km/h. |
| 5 | `pressure` | Open-Meteo API | **Live** | Fetched from `current.pressure_msl` (`weather_collector.py:72`). Falls back to `1013.0` hPa. |
| 6 | `soil_moisture` | Open-Meteo API | **Live** | Fetched from `current.soil_moisture_0_to_1cm` (`weather_collector.py:78`) via ECMWF land-surface model. Falls back to `0.25` m³/m³. |
| 7 | `rain_1h` | Open-Meteo API | **Live** | Fetched from `current.rain` (`weather_collector.py:87`). Falls back to `0.0` mm. |
| 8 | `forecast_rain_24h` | Open-Meteo API | **Live** | Sum of first 24 hours of `hourly.precipitation` (`weather_collector.py:62, 81`). Falls back to `0.0` mm. |
| 9 | `elevation` | Open-Meteo API | **Live** | Fetched from Open-Meteo response metadata `data.get('elevation')` (`weather_collector.py:65, 80`). Falls back to `50.0` m. |
| 10 | `slope` | **Hardcoded Placeholder** | **Placeholder** | `multi_modal_predictor.py:98` reads `slope = float(current_weather.get('slope', 5.0))`. `weather_collector.py` never computes or returns `slope`. Therefore, **`slope` is permanently hardcoded to `5.0`** across all live predictions, rendering mountain slope differentiation inert. |
| 11 | `ndvi` | NASA GIBS (Proxy) | **Proxy / Synthetic** | `satellite_collector.py:128` computes `ndvi_stat = float(np.clip(1.0 - (mean_val / 255.0), -1.0, 1.0))` using the mean pixel value of an 8-bit rendered MODIS surface temperature PNG tile. It does not use Red and Near-Infrared bands. If the GIBS tile fetch fails, it defaults to `[0.45]`. |
| 12 | `ndwi` | NASA GIBS (Proxy) | **Proxy / Synthetic** | `satellite_collector.py:129` computes `ndwi_stat = float(np.clip((std_val / 128.0) - 0.2, -1.0, 1.0))` from the standard deviation of MODIS temperature pixels. It does not use Green and NIR reflectance bands. If GIBS fails, it defaults to `[0.0]`. |
| 13 | `hotspots` | NASA GIBS / FIRMS | **Partial Live** | Extracted from `thermal.get('hotspot_count', 0)` based on pixels exceeding `mean + 2*std` in the MODIS temperature tile, or active fire counts from FIRMS/EONET. Falls back to `0`. |

---

## 4. External API Catalog, Timeouts, and Failure Behavior

| API Endpoint | Where Called (File:Line) | Purpose | Timeout | Failure & Error Handling Behavior |
|---|---|---|---|---|
| `https://api.open-meteo.com/v1/forecast` | `backend/data_collectors/weather_collector.py:49` | Current weather, hourly rain, soil moisture, elevation | `4.0s` | Catches exceptions; attempts secondary fallback to OpenWeatherMap. If OpenWeatherMap fails or has no key, falls back to neutral hardcoded defaults (`temp=25.0`, `pressure=1013.0`, `humidity=50.0`, `wind=10.0`). |
| `https://api.openweathermap.org/data/2.5/weather` | `backend/data_collectors/weather_collector.py:99` | Secondary weather fallback | `5.0s` | Catches exceptions silently; falls back to hardcoded neutral dictionary. |
| `https://archive-api.open-meteo.com/v1/archive` | `backend/data_collectors/weather_collector.py:164` | Historical 7-day weather time-series | `10.0s` | Catches exceptions; generates a fully synthetic randomized Pandas DataFrame using `25 + np.random.randn()`. |
| `https://api.open-meteo.com/v1/elevation` | `backend/services/exposure_vulnerability.py:315` | Elevation query for vulnerability indexing | `1.2s` | Catches exceptions silently; falls back to `None` and assumes baseline elevation of 100m. |
| `https://geocoding-api.open-meteo.com/v1/search` | `backend/services/geocoder.py:347` | Place name to coordinate geocoding | `4.0s` | Catches exceptions; proceeds to next tier (Nominatim). |
| `https://gibs.earthdata.nasa.gov/wms/epsg4326/best/wms.cgi` | `backend/data_collectors/satellite_collector.py:100` | NASA GIBS WMS MODIS land surface temp raster tiles | `1.5s` | Catches exceptions; returns dictionary with `'status': 'SENSOR_BLACKOUT'`, `'data_quality': 'ZERO_SIGNAL'`. |
| `https://eonet.gsfc.nasa.gov/api/v3/events` | `backend/data_collectors/satellite_collector.py:45` | NASA EONET natural disaster event feed | `1.5s` | Catches exceptions; logs warning and returns an empty list `[]`. |
| `https://firms.modaps.eosdis.nasa.gov/api/area/csv` | `backend/data_collectors/satellite_collector.py:304` | Active VIIRS/MODIS fire hotspot CSV data | `1.5s` | Catches exceptions; initiates fallback query to NASA EONET wildfire events. If EONET fails, returns `[]`. |
| `https://router.project-osrm.org/route/v1` | `backend/services/route_optimizer.py:210, 246` | Driving routes and navigation steps | `10.0s` (async) | Catches exceptions; logs error message; returns whatever routes succeeded, or attempts single alternative midpoint waypoint detour. |
| `https://overpass-api.de/api/interpreter` | `backend/services/real_shelters.py:53`<br>`backend/services/exposure_vulnerability.py:91` | OpenStreetMap emergency shelter & hospital queries | `1.5s` | Catches exceptions; initiates Tier 2 Nominatim search. If Nominatim fails, generates synthetic mock facilities with offset coordinates (`_get_fallback_facilities`). |
| `https://nominatim.openstreetmap.org/search` | `backend/services/real_shelters.py:143`<br>`backend/services/geocoder.py:381`<br>`backend/api/server.py:463` | Location search and secondary facility fallback | `1.2s` (geocoder)<br>`10.0s` (shelters) | Catches exceptions; returns `None` or falls back to synthetic mock facility generation. |
| `https://nominatim.openstreetmap.org/reverse` | `backend/services/exposure_vulnerability.py:123, 232` | Reverse geocoding for country/city boundary detection | `1.2s` | Catches exceptions silently; falls back to default national population density heuristics. |
| `https://geocode.arcgis.com/.../findAddressCandidates` | `backend/services/geocoder.py:323` | ArcGIS World Geocoding for Indian village/street search | `5.0s` | Catches exceptions; falls back to Open-Meteo Geocoding. |
| `https://ipinfo.io/json` | `backend/api/server.py:236` | Client public IP network geolocation detection | `3.5s` | Catches exceptions; logs warning and falls back to default coordinates for Bhubaneswar, Odisha (`20.2961, 85.8245`). |

---

## 5. Database Audit: `sdars_database.db` (Seed vs. Live Data)

The system maintains two SQLite database files: `sdars_database.db` (root) and `backend/sdars_database.db`. Both share identical schemas managed by SQLAlchemy in `backend/db/database.py`.

| Table Name | Row Count (Root / Backend) | Classification | Analysis: Demo Seed vs. Live Data |
|---|---|---|---|
| `river_gauges` | 6 / 6 | **100% Demo Seed Data** | All 6 records are hardcoded in `backend/api/disaster_management_routes.py:85-96` (`seed_default_data_if_empty`). Stations: Yamuna (Delhi), Mithi (Mumbai), Hooghly (Kolkata), Brahmaputra (Guwahati), Godavari (Rajahmundry), Mahanadi (Cuttack). No live CWC connection exists. Data updates occur only if `/gauges/simulate_reading` is triggered manually. |
| `resources` | 7 / 7 | **100% Demo Seed Data** | All 7 emergency facilities and fleets (e.g., Central Flood Evacuation Shelter, AIIMS Trauma Hub, NDRF 8th Battalion) are hardcoded in `disaster_management_routes.py:99-110`. |
| `historical_disasters` | 6 / 6 | **100% Static Benchmark Data** | 6 curated historical disaster events (Cyclone Fani 2019, Kerala Floods 2018, Wayanad Landslides 2024, Maharashtra Heatwave 2022, Cyclone Amphan 2020, Chennai Floods 2015) seeded in `disaster_management_routes.py:113-123`. Used as static reference benchmarks. |
| `crowd_reports` | 3 / 6 | **Mixed (Seed + Local User Tests)** | The first 3 rows (Kashmere Gate, BKC Junction, Park Street) are hardcoded demo seed records created by `seed_default_data_if_empty`. Remaining records represent local user submissions during testing of `/crowd/report`. |
| `predictions` | 322 / 1,137 | **Logged Execution Runs** | Contains historical logs from testing the `/api/predict` endpoint or running `realtime_monitor.py`. While the underlying weather snapshots represent live data captured at query time from Open-Meteo, the accompanying disaster probability scores were generated by models trained exclusively on synthetic data. |
| `zones` | 1 / 12 | **User-Created Interactive Data** | Polygons created and stored by users using the interactive drawing tools on `frontend/zones.html` via `/api/zones`. |
| `users` | 0 / 0 | **Empty Table** | Authentication in `backend/api/auth_routes.py` uses ephemeral mock OTP codes (`123456`). No user accounts are persisted. |
| `system_settings` | 0 / 0 | **Empty Table** | System settings are read from environment variables (`.env`) or default configuration dicts. The table is never written to. |
| `alerts` | 0 / 0 | **Empty Table** | Runtime alert instances generated by `advanced_alert_system.py` are retained in-memory or logged to stdout; they are not committed to SQLite. |
