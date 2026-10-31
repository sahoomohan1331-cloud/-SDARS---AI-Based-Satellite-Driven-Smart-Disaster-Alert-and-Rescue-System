# PROJECT_STATE.md — Full Project State Snapshot

**Snapshot Timestamp:** 2026-10-24 21:48:00 IST  
**Repository:** SDARS — AI-Based Satellite-Driven Smart Disaster Alert and Rescue System  
**Nature:** Read-Only Factual Audit & State Snapshot (Direct Command Outputs)

---

## 1. GIT HISTORY

### Command: `git log --oneline -40`
```text
47f7526 Follow-up 4: add resilient 429 rate limit backoff and launch 1990-2025 pull
e39825b Follow-up 3: verify terrain generation, row count, and regional slope samples
c28aeea Follow-up 2: add --force-point flag and detailed network request logging
d0b52f2 Follow-up 1: verify slope constant, fix bathymetry clamping, and add physical sanity check
c5eb3e1 Item 8: append final verification block to data/README.md
d77f31a Item 7: add automated tests for data pipeline
6b4fdb6 Item 6: update .env.example with HOURLY, FIRMS_MAP_KEY, and OPEN_METEO_BASE_URL
8525ec3 Item 5: document lightning archive deferral in BLOCKERS.md
ae3a21c Item 4: create data/README.md
3e7c921 Item 3: create data/DATASETS.md
9be6b63 Item 2: create backend/data_pipeline/fetch_terrain.py
db3b008 Item 1: create backend/data_pipeline/fetch_history.py
f8883af Item 9b: correct honesty report and inventory models
404e76e Item 5b: move Cesium Ion token to env var
5288fd3 Item 6b: verify pinned requirements in clean venv
3e43d2b test(hygiene): add automated tests for env, auth security, db anchoring, and health check
28ea06e chore(render): configure /api/health check path and note ephemeral sqlite storage
7dd72e6 fix(cli): restrict start.py --reload and host 0.0.0.0 behind --dev flag
4aaee75 chore(deps): pin requirements.txt to active versions and extract dev dependencies to requirements-dev.txt
68ac128 fix(auth): secure OTP authentication with SHA-256 hashing, rate limiting, and DEMO_MODE flag
6071c62 refactor(config): remove unused MongoDB settings and dead Keras .h5 model paths
f4efa4d fix(db): anchor sqlite database path to repository root with DATABASE_URL override
bb90d1c docs(env): document all environment variables in .env.example with placeholders
eabd183 fix(hygiene): untrack binary model joblib files and update gitignore
c517f9d docs: add scientific integrity rules and audit reports
8bc4aad chore: manual user removals
7c7f2b9 chore: clean up scratch files, remove old mobile project, update README with 8-hazard model and datasets info
b13d551 feat(ml): add xgboost to cloud requirements for disaster prediction models
8ed792f fix(mobile): resolve map popup touch response, pin anchors, and drawer sync
da04b3f chore(mobile): commit eas projectId in app.json
a438d4d build(mobile): install eas-cli locally to enable direct npx eas build execution
11489cd feat(server): add direct cloud routing for mobile_app and set https://sdars.onrender.com as default mobile endpoint
661270d feat(mobile): configure standalone APK build with eas.json, dynamic server endpoint, and render.yaml deployment
73c0bdf feat(3d-view): add vector symbols and labels to map base imagery buttons
bf8c4b0 fix(cesium): resolve Invalid array length in createPotentiallyVisibleSet by fixing point pixelSize, flood geometry, and error panel recovery
6c15d5f fix(frontend): resolve map popup freeze and Cesium 3d render crash; add animated collapsible tactical terrain switcher
b6082df feat(web): apply anti-ai design principles and vector iconography across entire desktop web suite
4e76cb9 feat(ui): eliminate AI-generated design tells across mobile and web interfaces
ac762d8 feat(mobile): add full mobile app suite, native expo location bridge, and resilient server-side geolocation
ef50b6b fix: resolve 3D war room layout and restore floating nav
```

### Command: `git status`
```text
On branch main
Your branch is ahead of 'origin/main' by 25 commits.
  (use "git push" to publish your local commits)

Untracked files:
  (use "git add <file>..." to include in what will be committed)
	CB_PPT_Template original.pptx

nothing added to commit but untracked files present (use "git add" to track)
```

### Command: `git diff --stat HEAD~10..HEAD`
```text
 .env.example                           |   9 ++
 BLOCKERS.md                            |  36 +++++
 backend/.env.example                   |   9 ++
 backend/data_pipeline/fetch_history.py |  58 +++++++-
 backend/data_pipeline/fetch_terrain.py |  14 +-
 data/DATASETS.md                       |  76 +++++++++++
 data/README.md                         | 235 +++++++++++++++++++++++++++++++++
 tests/test_data_pipeline.py            | 167 +++++++++++++++++++++++
 8 files changed, 596 insertions(+), 8 deletions(-)
```

---

## 2. INTEGRITY & AUDIT DOCS

### A. AGENTS.md ("Scientific Integrity Rules" section)
- **Status:** File exists.
- **Section Content:**
```markdown
## 3. Scientific Integrity Rules
1. **Never fabricate, estimate, or hardcode metrics, accuracy, or performance numbers.** Every number in docs must come from a script that writes it to `reports/metrics.json`.
2. **Never train or evaluate models on synthetic data.** Synthetic data is allowed only in `tests/fixtures/` for pipeline smoke tests.
3. **If a data source is unavailable or labels for a hazard are too sparse, STOP and describe the problem in `BLOCKERS.md`.** Do not substitute fake or proxy data silently.
4. **All train/test splits must be temporal** (train on earlier years, test on later years). No random splits.
5. **Features at time t may only use information available at or before t.** Every feature needs a leakage test.
6. **Report PR-AUC, recall, precision, false-alarm rate, and Brier score per hazard.** Never report plain accuracy as a headline metric.
7. **If a hazard performs poorly, label it "experimental" in docs and UI.** Do not hide it.
8. **Docs must match code.** Remove any claim that is not implemented.
```

### B. AUDIT.md
- **Status:** File exists.
- **Full Contents:**
```markdown
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
```

### C. BLOCKERS.md
- **Status:** File exists.
- **Full Contents:**
```markdown
# SDARS Technical & Data Blockers Log

In accordance with SDARS Scientific Integrity Rule 3:
> *"If a data source is unavailable or labels for a hazard are too sparse, STOP and describe the problem in BLOCKERS.md. Do not substitute fake or proxy data silently."*

This file documents data unavailability, archived feed gaps, and technical constraints encountered in the historical pipeline.

---

## 1. Lightning Hazard Archive (v1 Deferred)

**Status:** BLOCKED / DEFERRED  
**Impacted Hazard:** Lightning (Hazard 6 of 8)  
**Date Logged:** 2026-10-24  

### Problem Description
Lightning (all 8 hazards, v1): no open, India-wide, hourly lightning archive is accessible. Blitzortung is volunteer-partial. Options for a future version: (a) pay for a commercial feed, (b) use IMD gridded lightning once available, (c) drop the hazard. Marking lightning as deferred for v1, not faked.

### Detail & Investigation
- Ground-based optical/RF detection networks such as Blitzortung rely on enthusiast stations and suffer from severe spatial bias and low detection efficiency across rural and coastal Odisha.
- Satellite optical lightning data (e.g. INSAT-3D/3DR Lightning Detection or MTG LI) is either not published in an open programmatic bulk archive for 1990–2024 or lacks verified ground calibration.
- Rather than training on synthetic lightning strikes or fabricating proxy labels, lightning hazard modeling is explicitly deferred in v1.

---

## 2. Convective Available Potential Energy (CAPE) in Open-Meteo ERA5

**Status:** SKIPPED / LOGGED  
**Impacted Variable:** Atmospheric Instability (`cape`)  
**Date Logged:** 2026-10-24  

### Problem Description
Open-Meteo Historical Weather API (`/v1/archive`) queries for variable `cape` return all `null` values across the entire Odisha bounding box (lat 17.8°N to 22.6°N, lon 81.3°E to 87.5°E) for ERA5 / ERA5-Land reanalysis.

### Resolution
In strict accordance with project rules against proxy or estimated substitutions, CAPE is omitted from the historical weather feature schema in `weather_6h.parquet` rather than substituting an arbitrary proxy. If thermodynamic soundings or regional mesoscale reanalysis (e.g. IMD NCUM reanalysis) become programmatically accessible, convective instability metrics will be incorporated.
```

### D. HYGIENE_REPORT.md
- **Status:** File exists.
- **Last 100 lines (Lines 411–510):**
```markdown
### V3. No Cesium token literal remains in tracked frontend files.
**Status:** PASSED  
**Command:** `git grep -nE "eyJ[A-Za-z0-9_-]{20,}" frontend/`  
**Output:**
```text
(no matches)
```

### V4. CESIUM_ION_TOKEN present in .env.example.
**Status:** PASSED  
**Command:** `grep -n "CESIUM_ION_TOKEN" .env.example`  
**Output:**
```text
88:CESIUM_ION_TOKEN=your_cesium_ion_access_token_here
```

### V5. Secrets-to-rotate section exists in HYGIENE_REPORT.md and does NOT contain the token value.
**Status:** PASSED  
**Command:** `grep -nA3 "Secrets to rotate" HYGIENE_REPORT.md`  
**Output:**
```text
53:### Secrets to rotate
54-
55-- **Location:** `frontend/3d-view.html:661`
56-- **Type:** Cesium Ion Access Token (JWT)
```

### V6. All 16 joblib files inventoried with classification.
**Status:** PASSED  
| File Path | Size (Bytes / KB) | Last Modified (mtime) | Producing Script | Runtime Status | Classification |
|---|---|---|---|---|---|
| `backend/models/cyclone_model.joblib` | 258,115 B (252.07 KB) | 2026-10-08 16:59:11 | `backend/ai_models/train_xgboost_models.py` | Active Primary | Runtime model loaded by `multi_modal_predictor.py:54` |
| `backend/models/cyclone_risk_model.joblib` | 2,481,737 B (2,423.57 KB) | 2026-10-02 04:17:21 | `backend/ai_models/train_models.py` | Dormant Fallback | Stale checkpoint (RandomForest 100-tree ensemble) |
| `backend/models/drought_model.joblib` | 284,159 B (277.50 KB) | 2026-10-08 16:59:11 | `backend/ai_models/train_xgboost_models.py` | Active Primary | Runtime model loaded by `multi_modal_predictor.py:56` |
| `backend/models/drought_risk_model.joblib` | 2,776,297 B (2,711.23 KB) | 2026-10-02 04:17:29 | `backend/ai_models/train_models.py` | Dormant Fallback | Stale checkpoint (RandomForest 100-tree ensemble) |
| `backend/models/fire_model.joblib` | 258,117 B (252.07 KB) | 2026-10-08 16:59:10 | `backend/ai_models/train_xgboost_models.py` | Active Primary | Runtime model loaded by `multi_modal_predictor.py:61` |
| `backend/models/fire_risk_model.joblib` | 2,149,417 B (2,099.04 KB) | 2026-10-02 04:17:50 | `backend/ai_models/train_models.py` | Dormant Fallback | Stale checkpoint (RandomForest 100-tree ensemble) |
| `backend/models/flood_model.joblib` | 246,357 B (240.58 KB) | 2026-10-08 16:59:11 | `backend/ai_models/train_xgboost_models.py` | Active Primary | Runtime model loaded by `multi_modal_predictor.py:55` |
| `backend/models/flood_risk_model.joblib` | 2,220,617 B (2,168.57 KB) | 2026-10-02 04:17:25 | `backend/ai_models/train_models.py` | Dormant Fallback | Stale checkpoint (RandomForest 100-tree ensemble) |
| `backend/models/heatwave_model.joblib` | 241,797 B (236.13 KB) | 2026-10-08 16:59:12 | `backend/ai_models/train_xgboost_models.py` | Active Primary | Runtime model loaded by `multi_modal_predictor.py:57` |
| `backend/models/heatwave_risk_model.joblib` | 2,271,337 B (2,218.10 KB) | 2026-10-02 04:17:33 | `backend/ai_models/train_models.py` | Dormant Fallback | Stale checkpoint (RandomForest 100-tree ensemble) |
| `backend/models/landslide_model.joblib` | 240,709 B (235.07 KB) | 2026-10-08 16:59:11 | `backend/ai_models/train_xgboost_models.py` | Active Primary | Runtime model loaded by `multi_modal_predictor.py:59` |
| `backend/models/landslide_risk_model.joblib` | 2,843,497 B (2,776.85 KB) | 2026-10-02 04:17:41 | `backend/ai_models/train_models.py` | Dormant Fallback | Stale checkpoint (RandomForest 100-tree ensemble) |
| `backend/models/lightning_model.joblib` | 290,355 B (283.55 KB) | 2026-10-08 16:59:12 | `backend/ai_models/train_xgboost_models.py` | Active Primary | Runtime model loaded by `multi_modal_predictor.py:58` |
| `backend/models/lightning_risk_model.joblib` | 2,929,897 B (2,861.23 KB) | 2026-10-02 04:17:37 | `backend/ai_models/train_models.py` | Dormant Fallback | Stale checkpoint (RandomForest 100-tree ensemble) |
| `backend/models/storm_surge_model.joblib` | 180,127 B (175.91 KB) | 2026-10-08 16:59:12 | `backend/ai_models/train_xgboost_models.py` | Active Primary | Runtime model loaded by `multi_modal_predictor.py:60` |
| `backend/models/storm_surge_risk_model.joblib` | 2,759,817 B (2,695.13 KB) | 2026-10-02 04:17:46 | `backend/ai_models/train_models.py` | Dormant Fallback | Stale checkpoint (RandomForest 100-tree ensemble) |

### V7. The old "None unverified" line is gone; UNVERIFIED / OPEN section exists.
**Status:** PASSED  
**Command:** `grep -nE "None unverified|UNVERIFIED|OPEN" HYGIENE_REPORT.md`  
**Output:**
```text
345:## 8. UNVERIFIED / OPEN
```

### V8. 24 unused packages actually removed from requirements.
**Status:** PASSED  
**Command:** `grep -iE 'tensorflow|keras|torch|torchvision|opencv|rasterio|gdal|sentinelsat|openweathermap|meteostat|earthengine|planet|pystac|matplotlib|seaborn|plotly|statsmodels|prophet|pmdarima|twilio|telegram|pymongo|scipy|tqdm' requirements.txt backend/requirements.txt`  
**Output:**
```text
(no matches)
```

### V9. Only the intended files changed.
**Status:** PASSED  
**Command:** `git diff --stat HEAD~3..HEAD`  
**Output:**
```text
 .env.example          |   4 +
 .gitignore            |   3 +
 HYGIENE_REPORT.md     | 386 +++++++++++++++++++++++++++++++++++++++++++++++++-
 backend/.env.example  |   4 +
 backend/api/server.py |  13 +-
 frontend/3d-view.html |   4 +-
 start.py              |  24 ++
 tests/test_hygiene.py |   6 +-
 8 files changed, 436 insertions(+), 8 deletions(-)
```

### V10. Tests still pass after all three corrections.
**Status:** PASSED  
**Command:** `pytest`  
**Output:**
```text
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-7.4.3, pluggy-1.6.0
rootdir: D:\SDARS map
configfile: pytest.ini
testpaths: tests, backend/tests
plugins: anyio-4.14.2
collected 12 items

tests\test_hygiene.py .....                                              [ 41%]
backend\tests\test_command_api.py ...                                    [ 66%]
backend\tests\test_prediction_api.py ....                                [100%]

====================== 12 passed, 15 warnings in 16.34s =======================
```
```

### E. data/DATASETS.md
- **Status:** File exists.
- **Full Contents:**
```markdown
# SDARS Dataset Provenance & Registry

This document records the exact provenance, cryptographic checksums, schemas, and source licenses for all processed dataset files generated by the SDARS real data pipeline. Every dataset documented below is produced directly from authoritative historical archives without synthetic or proxy data substitution.

---

## Processed Datasets

### 1. `data/processed/weather_6h.parquet`
- **File Path:** `data/processed/weather_6h.parquet`
- **Producing Script:** `backend/data_pipeline/fetch_history.py`
- **Source Data:** Open-Meteo Historical Weather API (Copernicus ECMWF ERA5 & ERA5-Land Reanalysis)
- **Source Data License:** Creative Commons Attribution 4.0 International (CC BY 4.0) / Copernicus ECMWF License
- **Row Count:** 201480
- **Column Count:** 16
- **Column List:**
  1. `timestamp_utc` (datetime64[ns, UTC])
  2. `grid_id` (string)
  3. `lat` (float64)
  4. `lon` (float64)
  5. `temperature_2m` (float64, °C)
  6. `relative_humidity_2m` (float64, %)
  7. `dew_point_2m` (float64, °C)
  8. `surface_pressure` (float64, hPa)
  9. `wind_speed_10m` (float64, km/h)
  10. `wind_gusts_10m` (float64, km/h)
  11. `precipitation` (float64, mm)
  12. `cloud_cover` (float64, %)
  13. `soil_moisture_0_to_7cm` (float64, m³/m³)
  14. `soil_moisture_7_to_28cm` (float64, m³/m³)
  15. `soil_moisture_28_to_100cm` (float64, m³/m³)
  16. `elevation` (float64, metres above sea level)
- **Date Range:** `1990-01-01 00:00:00+00:00` to `1990-12-31 18:00:00+00:00` (UTC)
- **Temporal Frequency:** 6-hourly (00:00, 06:00, 12:00, 18:00 UTC)
- **Spatial Coverage:** 138 points across Odisha, India (130 regular 0.5° grid cells + 8 named urban centers)
- **SHA-256 Checksum:** `42d9a8a038763bccf306fefd0299a92160d270c29ed049fbd2d5a89b3aca1f1b`

---

### 2. `data/processed/grid_metadata.parquet`
- **File Path:** `data/processed/grid_metadata.parquet`
- **Producing Script:** `backend/data_pipeline/fetch_history.py`
- **Source Data:** SDARS Monitoring Grid Specification & Open-Meteo Elevation Metadata
- **Source Data License:** Creative Commons Attribution 4.0 International (CC BY 4.0)
- **Row Count:** 138
- **Column Count:** 6
- **Column List:**
  1. `grid_id` (string)
  2. `lat` (float64)
  3. `lon` (float64)
  4. `elevation` (float64, metres)
  5. `is_city` (bool)
  6. `city_name` (string, nullable)
- **Date Range:** Static spatial reference (N/A)
- **Spatial Coverage:** Odisha bounding box (lat 17.8°N to 22.6°N, lon 81.3°E to 87.5°E)
- **SHA-256 Checksum:** `1b806bdb43bc3d2e9670ee89ef183c0adfeed1c793be242a3dbbdd0de600901f`

---

### 3. `data/processed/terrain.parquet`
- **File Path:** `data/processed/terrain.parquet`
- **Producing Script:** `backend/data_pipeline/fetch_terrain.py`
- **Source Data:** NASA Shuttle Radar Topography Mission (SRTM GL1 1-arc-second / 30 m) via AWS Skadi
- **Source Data License:** Public Domain (US Government work, NASA)
- **Row Count:** 138
- **Column Count:** 5
- **Column List:**
  1. `grid_id` (string)
  2. `mean_elevation_m` (float64, mean elevation in metres within 0.5° cell)
  3. `max_elevation_m` (float64, peak elevation in metres within 0.5° cell)
  4. `min_elevation_m` (float64, base elevation in metres within 0.5° cell)
  5. `max_slope_deg` (float64, maximum slope in degrees derived from 30 m DEM gradients)
- **Date Range:** Static topographic reference (N/A)
- **Spatial Coverage:** 138 grid points across Odisha
- **Methodology Note:** Slope is derived directly from SRTM 30 m sub-cell elevation gradients (`np.gradient` at ~30 m spacing) aggregated across the 0.5-degree cell window, NOT from coarse cell centres.
- **SHA-256 Checksum:** `279f5a362a5999f33bb941b96319a93714fbaf7a3db76d59be05523838774280`
```

### F. data/README.md
- **Status:** File exists.
- **Last 100 lines (Lines 136–235):**
```markdown
def compute_terrain_metrics_from_30m_dem(
    cell_lat: float,
    cell_lon: float,
    tile_manager: TileManager,
    cell_step: float = DEFAULT_STEP,
) -> dict[str, float]:
    """Compute terrain elevation and slope metrics from 30 m SRTM DEM within a 0.5-degree cell.

    IMPORTANT: Slope is computed from high-resolution 30 m DEM gradients within the cell,
    NOT from neighbouring 0.5-degree cell centres. This captures true sub-cell terrain variability.
    """
    half_step = cell_step / 2.0
    cell_min_lat = cell_lat - half_step
    cell_max_lat = cell_lat + half_step
    cell_min_lon = cell_lon - half_step
    cell_max_lon = cell_lon + half_step

    # Extract 30 m DEM patch covering the ~0.5 x 0.5 degree window (~1800 x 1800 pixels)
    dem_patch = tile_manager.extract_patch(cell_min_lat, cell_max_lat, cell_min_lon, cell_max_lon)

    # Elevation metrics
    mean_el = float(np.nanmean(dem_patch))
    max_el = float(np.nanmax(dem_patch))
    min_el = float(np.nanmin(dem_patch))

    # Compute slope at 30 m resolution
    # dy = spacing along latitude in metres
    # dx = spacing along longitude in metres at given latitude
    dy = METRES_PER_ARCSEC_LAT
    dx = METRES_PER_ARCSEC_LAT * math.cos(math.radians(cell_lat))
    dx = max(dx, 1.0)  # Avoid division by zero

    # 30 m gradients
    gy, gx = np.gradient(dem_patch, dy, dx)
    slope_rad = np.arctan(np.sqrt(gy**2 + gx**2))
    slope_deg = np.degrees(slope_rad)
    max_slope = float(np.nanmax(slope_deg))

    return {
        "mean_elevation_m": round(mean_el, 2),
        "max_elevation_m": round(max_el, 2),
        "min_elevation_m": round(min_el, 2),
        "max_slope_deg": round(max(max_slope, 0.0), 2),
    }
```

### V5. data/DATASETS.md exists and lists the output files
**Status:** PASSED  
**Command:** `cat data/DATASETS.md`  
**Output:** Verified present and documents `data/processed/weather_6h.parquet`, `data/processed/grid_metadata.parquet`, and `data/processed/terrain.parquet` with row counts, columns, schemas, date ranges, and SHA-256 hashes.

### V6. Lightning is in BLOCKERS.md, not in code
**Status:** PASSED  
**Command:** `grep -n "lightning" BLOCKERS.md; grep -rn "lightning" backend/data_pipeline/`  
**Output:**
```text
17:Lightning (all 8 hazards, v1): no open, India-wide, hourly lightning archive is accessible. Blitzortung is volunteer-partial. Options for a future version: (a) pay for a commercial feed, (b) use IMD gridded lightning once available, (c) drop the hazard. Marking lightning as deferred for v1, not faked.
21:- Satellite optical lightning data (e.g. INSAT-3D/3DR Lightning Detection or MTG LI) is either not published in an open programmatic bulk archive for 1990–2024 or lacks verified ground calibration.
22:- Rather than training on synthetic lightning strikes or fabricating proxy labels, lightning hazard modeling is explicitly deferred in v1.
(backend/data_pipeline/ produced no matches)
```

### V7. Tests pass
**Status:** PASSED  
**Command:** `pytest tests/test_data_pipeline.py -v`  
**Output:**
```text
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-7.4.3, pluggy-1.6.0 -- C:\Users\Mohan\AppData\Local\Programs\Python\Python312\python.exe
cachedir: .pytest_cache
rootdir: D:\SDARS map
configfile: pytest.ini
plugins: anyio-4.14.2
collecting ... collected 5 items

tests/test_data_pipeline.py::test_grid_generation PASSED                 [ 20%]
tests/test_data_pipeline.py::test_no_synthetic_fallback PASSED           [ 40%]
tests/test_data_pipeline.py::test_parquet_schema PASSED                  [ 60%]
tests/test_data_pipeline.py::test_terrain_schema PASSED                  [ 80%]
tests/test_data_pipeline.py::test_datasets_md_exists PASSED              [100%]

============================== 5 passed in 3.71s ==============================
```

### V8. Only intended files touched
**Status:** PASSED  
**Command:** `git diff --stat HEAD~7..HEAD`  
**Output:**
```text
 .env.example                           |   9 +
 .gitignore                             |   6 +
 BLOCKERS.md                            |  36 +++
 backend/.env.example                   |   9 +
 backend/data_pipeline/__init__.py      |   1 +
 backend/data_pipeline/fetch_history.py | 518 +++++++++++++++++++++++++++++++++
 backend/data_pipeline/fetch_terrain.py | 405 ++++++++++++++++++++++++++
 data/DATASETS.md                       |  76 +++++
 data/README.md                         | 216 ++++++++++++++++
 tests/test_data_pipeline.py            | 150 ++++++++++
 10 files changed, 1426 insertions(+)
```
*(Parquet data in `data/raw/` and `data/processed/` is verified gitignored.)*
```

---

## 3. SECURITY STATE

### a. `grep -rn "123456" --include="*.py" --include="*.js" --include="*.html"`
```text
backend/api/auth_routes.py:53:    - DEMO_MODE=true: Allows fixed test code 123456 and returns demo_mode: true
backend/api/auth_routes.py:88:        demo_code = "123456"
backend/api/auth_routes.py:96:            "message": "[DEMO MODE] Verification code is 123456",
backend/services/advanced_alert_system.py:116:                    'phone': os.getenv('ALERT_PHONE', '+1234567890'),
backend/services/advanced_alert_system.py:152:                'phone': os.getenv('ALERT_PHONE', '+1234567890'),
frontend/js/auth.js:85:                    hintEl.innerText = `[DEMO MODE] use code ${data.demo_otp || '123456'}`;
tests/test_hygiene.py:73:    """Verify that when DEMO_MODE is false, no response returns the demo OTP code 123456."""
tests/test_hygiene.py:84:        assert "123456" not in str(resp_json)
```
*Verification:* The fixed OTP string `123456` appears solely inside the `DEMO_MODE=true` branch in `backend/api/auth_routes.py`, in a frontend UI helper text string when `DEMO_MODE` is returned by the server, in test assertions enforcing that `123456` is NEVER returned when `DEMO_MODE=false`, and as an arbitrary placeholder phone number `+1234567890`.

### b. `grep -n "DEMO_MODE" backend/api/auth_routes.py backend/services/email_service.py`
```text
backend/api/auth_routes.py:46:    """Checks if DEMO_MODE is actively enabled via environment"""
backend/api/auth_routes.py:47:    return os.getenv("DEMO_MODE", "false").lower() == "true"
backend/api/auth_routes.py:53:    - DEMO_MODE=true: Allows fixed test code 123456 and returns demo_mode: true
backend/api/auth_routes.py:54:    - DEMO_MODE=false: Requires active SMTP, generates 6-digit secret OTP, stores SHA-256 hash
backend/api/auth_routes.py:104:        logger.warning(f"Login rejected for {email}: SMTP credentials unconfigured and DEMO_MODE=false.")
```

### c. `git grep -nE "eyJ[A-Za-z0-9_-]{20,}"` across tracked repo
```text
(no matches — command exited with returncode 1)
```

### d. `grep -n "CESIUM_ION_TOKEN" .env.example`
```text
.env.example:88:CESIUM_ION_TOKEN=your_cesium_ion_access_token_here
```

---

## 4. DATABASE STATE

### a. List every `.db` file found (excluding node_modules), with size:
```text
sdars_database.db: 425984 bytes
archive_local\sdars_database_old_root.db: 192512 bytes
```

### b. Canonical DB table and row-count output (`sdars_database.db`):
Command: `python -c "import sqlite3; c=sqlite3.connect('sdars_database.db'); tables=[r[0] for r in c.execute('SELECT name FROM sqlite_master WHERE type=\'table\'').fetchall()]; [print(t, c.execute('SELECT COUNT(*) FROM ' + t).fetchone()[0]) for t in tables]"`
```text
predictions 1145
zones 12
users 0
system_settings 0
alerts 0
crowd_reports 6
river_gauges 6
resources 7
historical_disasters 6
```

---

## 5. DEPENDENCY STATE

### a. `cat requirements.txt`
```text
# SDARS Production Requirements (Pinned to Active Installed Environment)
aiohttp==3.14.3
fastapi==0.141.1
joblib==1.5.3
numpy==2.5.3
pandas==3.0.5
Pillow==12.2.0
pydantic==2.13.5
python-dotenv==1.2.3
python-multipart==0.0.32
requests==2.34.2
schedule==1.2.2
scikit-learn==1.9.0
sqlalchemy==2.0.54
uvicorn[standard]==0.51.0
xgboost==3.4.1
```

### b. `cat requirements-dev.txt`
```text
# SDARS Development & Testing Requirements
-r requirements.txt
pytest==7.4.3
ruff>=0.1.0
httpx>=0.27.0
```

### c. `grep -iE "tensorflow|keras|torch|pymongo|twilio" requirements.txt`
```text
(no matches — command exited with returncode 1)
```

---

## 6. MODEL ARTIFACTS

### a. Model files list (*.joblib, *.pkl, *.h5, *.pt, *.onnx) with path, size, and mtime:
```text
backend\models\cyclone_model.joblib | 258115 bytes (252.07 KB) | mtime=2026-10-08 16:59:11
backend\models\cyclone_risk_model.joblib | 2481737 bytes (2423.57 KB) | mtime=2026-10-02 04:17:21
backend\models\drought_model.joblib | 284159 bytes (277.50 KB) | mtime=2026-10-08 16:59:11
backend\models\drought_risk_model.joblib | 2776297 bytes (2711.23 KB) | mtime=2026-10-02 04:17:29
backend\models\fire_model.joblib | 258117 bytes (252.07 KB) | mtime=2026-10-08 16:59:10
backend\models\fire_risk_model.joblib | 2149417 bytes (2099.04 KB) | mtime=2026-10-02 04:17:50
backend\models\flood_model.joblib | 246357 bytes (240.58 KB) | mtime=2026-10-08 16:59:11
backend\models\flood_risk_model.joblib | 2220617 bytes (2168.57 KB) | mtime=2026-10-02 04:17:25
backend\models\heatwave_model.joblib | 241797 bytes (236.13 KB) | mtime=2026-10-08 16:59:12
backend\models\heatwave_risk_model.joblib | 2271337 bytes (2218.10 KB) | mtime=2026-10-02 04:17:33
backend\models\landslide_model.joblib | 240709 bytes (235.07 KB) | mtime=2026-10-08 16:59:11
backend\models\landslide_risk_model.joblib | 2843497 bytes (2776.85 KB) | mtime=2026-10-02 04:17:41
backend\models\lightning_model.joblib | 290355 bytes (283.55 KB) | mtime=2026-10-08 16:59:12
backend\models\lightning_risk_model.joblib | 2929897 bytes (2861.23 KB) | mtime=2026-10-02 04:17:37
backend\models\storm_surge_model.joblib | 180127 bytes (175.91 KB) | mtime=2026-10-08 16:59:12
backend\models\storm_surge_risk_model.joblib | 2759817 bytes (2695.13 KB) | mtime=2026-10-02 04:17:46
```
*(No *.pkl, *.h5, *.pt, or *.onnx files exist in the repository).*

### b. Runtime Loading State (Grep `joblib.load`):
Command: `git grep -n "joblib.load" backend/`
```text
backend/ai_models/multi_modal_predictor.py:68:                    self.models[k] = joblib.load(path)
```
- In `backend/ai_models/multi_modal_predictor.py:53-74`, the active primary models loaded at runtime are the 8 XGBoost models:
  - `backend/models/cyclone_model.joblib`
  - `backend/models/flood_model.joblib`
  - `backend/models/drought_model.joblib`
  - `backend/models/heatwave_model.joblib`
  - `backend/models/lightning_model.joblib`
  - `backend/models/landslide_model.joblib`
  - `backend/models/storm_surge_model.joblib`
  - `backend/models/fire_model.joblib`
- The 8 `*_risk_model.joblib` files are legacy RandomForest checkpoints used only as fallback if the `*_model.joblib` files are deleted.

### c. Training Provenance (Synthetic vs. Real):
- **100% of currently existing models were trained on synthetic data.**
- The 8 `*_model.joblib` files were produced by `backend/ai_models/train_xgboost_models.py` which trains on `generate_realistic_hazard_dataset()` (synthetic Gaussian noise around threshold equations).
- The 8 `*_risk_model.joblib` files were produced by `backend/ai_models/train_models.py` which trains on `backend/ai_models/training_data_generator.py` (synthetic disaster scenarios).
- Zero models have been trained on real data yet (the historical data pipeline in Step 3 was built for raw data ingestion; model training in Step 5+ has not commenced).

---

## 7. DATA PIPELINE STATE (Step 3)

### a. `find data/processed -type f` (files and sizes):
```text
data\processed\grid_metadata.parquet: 5646 bytes
data\processed\terrain.parquet: 7044 bytes
data\processed\weather_6h.parquet: 2206629 bytes
```

### b. `weather_6h.parquet` Summary:
Command: `python -c "import pandas as pd; df = pd.read_parquet('data/processed/weather_6h.parquet'); print('rows:', len(df)); print('date range:', df.timestamp_utc.min(), 'to', df.timestamp_utc.max()); print('unique hours:', sorted(df.timestamp_utc.dt.hour.unique())); print('unique grid points:', df.grid_id.nunique())"`
```text
rows: 201480
date range: 1990-01-01 00:00:00+00:00 to 1990-12-31 18:00:00+00:00
unique hours: [np.int32(0), np.int32(6), np.int32(12), np.int32(18)]
unique grid points: 138
```

### c. `terrain.parquet` Summary:
Command: `python -c "import pandas as pd; df = pd.read_parquet('data/processed/terrain.parquet'); print(df.describe())"`
```text
       mean_elevation_m  max_elevation_m  min_elevation_m  max_slope_deg
count        138.000000       138.000000        138.00000     138.000000
mean         233.467174       659.666667         97.00000      27.503406
std          221.608588       477.773139        116.79316      17.490242
min            0.000000         0.000000          0.00000       0.000000
25%            4.520000       111.250000          0.00000       5.875000
50%          226.995000       748.000000         45.50000      34.155000
75%          359.382500       977.750000        185.00000      41.022500
max          961.430000      1677.000000        542.00000      52.650000
```

### d. Cache directory structure (`data/raw`):
Command: `find data/raw -type d | head -20`
```text
data\raw\open_meteo
data\raw\srtm
data\raw\open_meteo\city_angul
data\raw\open_meteo\city_balasore
data\raw\open_meteo\city_berhampur
data\raw\open_meteo\city_bhubaneswar
data\raw\open_meteo\city_cuttack
data\raw\open_meteo\city_puri
data\raw\open_meteo\city_rourkela
data\raw\open_meteo\city_sambalpur
data\raw\open_meteo\grid_17.8_81.3
data\raw\open_meteo\grid_17.8_81.8
data\raw\open_meteo\grid_17.8_82.3
data\raw\open_meteo\grid_17.8_82.8
data\raw\open_meteo\grid_17.8_83.3
data\raw\open_meteo\grid_17.8_83.8
data\raw\open_meteo\grid_17.8_84.3
data\raw\open_meteo\grid_17.8_84.8
data\raw\open_meteo\grid_17.8_85.3
data\raw\open_meteo\grid_17.8_85.8
```

### e. Explicit Date Range Statement:
`data/processed/weather_6h.parquet` currently covers **ONLY a partial range**:
- **Start:** `1990-01-01 00:00:00+00:00`
- **End:** `1990-12-31 18:00:00+00:00`
It does NOT yet cover through 2025 or the most recent complete month. In the underlying raw cache (`data/raw/open_meteo/`), year 1990 has 138 points, year 2024 has 138 points, and year 1991 has 30 points. The full 1990–2025 multi-year pull paused when Open-Meteo's hourly API rate limit window was reached (`"reason":"Hourly API request limit exceeded. Please try again in the next hour."`).

---

## 8. LABELS STATE (Step 4 — may not have started)

### a. `find data/processed -name "labels_*.parquet"`
```text
(no matches)
```

### b. Step 4 Status:
Step 4 has not produced any label files yet.

### c. `grep -n "FIRMS_MAP_KEY" .env.example`
```text
.env.example:94:FIRMS_MAP_KEY=your_firms_map_key_here
```

---

## 9. TEST SUITE

### Full Pytest Output (`pytest -v`):
```text
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-7.4.3, pluggy-1.6.0 -- C:\Users\Mohan\AppData\Local\Programs\Python\Python312\python.exe
cachedir: .pytest_cache
rootdir: D:\SDARS map
configfile: pytest.ini
testpaths: tests, backend/tests
plugins: anyio-4.14.2
collecting ... collected 17 items

tests/test_data_pipeline.py::test_grid_generation PASSED                 [  5%]
tests/test_data_pipeline.py::test_no_synthetic_fallback PASSED           [ 11%]
tests/test_data_pipeline.py::test_parquet_schema PASSED                  [ 17%]
tests/test_data_pipeline.py::test_terrain_schema PASSED                  [ 23%]
tests/test_data_pipeline.py::test_datasets_md_exists PASSED              [ 29%]
tests/test_hygiene.py::test_env_example_contains_every_env_var PASSED    [ 35%]
tests/test_hygiene.py::test_no_demo_otp_when_demo_mode_false PASSED      [ 41%]
tests/test_hygiene.py::test_smtp_failure_returns_503_and_stores_no_otp PASSED [ 47%]
tests/test_hygiene.py::test_db_path_identical_regardless_of_working_dir PASSED [ 52%]
tests/test_hygiene.py::test_api_health_endpoint PASSED                   [ 58%]
backend/tests/test_command_api.py::test_command_status PASSED            [ 64%]
backend/tests/test_command_api.py::test_command_impact PASSED            [ 70%]
backend/tests/test_command_api.py::test_command_dispatch PASSED          [ 76%]
backend/tests/test_prediction_api.py::test_health_check PASSED           [ 82%]
backend/tests/test_prediction_api.py::test_api_status PASSED             [ 88%]
backend/tests/test_prediction_api.py::test_prediction_endpoint PASSED    [ 94%]
backend/tests/test_prediction_api.py::test_predictions_history PASSED    [100%]

============================== warnings summary ===============================
backend\db\database.py:19
  D:\SDARS map\backend\db\database.py:19: MovedIn20Warning: The ``declarative_base()`` function is now available as sqlalchemy.orm.declarative_base(). (deprecated since: 2.0) (Background on SQLAlchemy 2.0 at: https://sqlalche.me/e/b8d9)
    Base = declarative_base()

backend\api\command_routes.py:32
  D:\SDARS map\backend\api\command_routes.py:32: PydanticDeprecatedSince20: Using extra keyword arguments on `Field` is deprecated and will be removed. Use `json_schema_extra` instead. (Extra keys: 'example'). Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.13/migration/
    action_type: str = Field(..., example="BROADCAST_L4_ALERT")

backend\api\command_routes.py:33
  D:\SDARS map\backend\api\command_routes.py:33: PydanticDeprecatedSince20: Using extra keyword arguments on `Field` is deprecated and will be removed. Use `json_schema_extra` instead. (Extra keys: 'example'). Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.13/migration/
    target_zone: str = Field(..., example="Bhubaneswar Coastal Sector 4")

backend\api\command_routes.py:34
  D:\SDARS map\backend\api\command_routes.py:34: PydanticDeprecatedSince20: Using extra keyword arguments on `Field` is deprecated and will be removed. Use `json_schema_extra` instead. (Extra keys: 'example'). Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.13/migration/
    latitude: float = Field(..., example=20.2961)

backend\api\command_routes.py:35
  D:\SDARS map\backend\api\command_routes.py:35: PydanticDeprecatedSince20: Using extra keyword arguments on `Field` is deprecated and will be removed. Use `json_schema_extra` instead. (Extra keys: 'example'). Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.13/migration/
    longitude: float = Field(..., example=85.8245)

backend\api\command_routes.py:36
  D:\SDARS map\backend\api\command_routes.py:36: PydanticDeprecatedSince20: Using extra keyword arguments on `Field` is deprecated and will be removed. Use `json_schema_extra` instead. (Extra keys: 'example'). Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.13/migration/
    commander_id: Optional[str] = Field("CMD-ALPHA-01", example="CMD-ALPHA-01")

backend\api\command_routes.py:37
  D:\SDARS map\backend\api\command_routes.py:37: PydanticDeprecatedSince20: Using extra keyword arguments on `Field` is deprecated and will be removed. Use `json_schema_extra` instead. (Extra keys: 'example'). Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.13/migration/
    notes: Optional[str] = Field("Immediate Level 4 Evacuation Broadcast", example="Deploy 2 units")

backend\api\command_routes.py:40
  D:\SDARS map\backend\api\command_routes.py:40: PydanticDeprecatedSince20: Using extra keyword arguments on `Field` is deprecated and will be removed. Use `json_schema_extra` instead. (Extra keys: 'example'). Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.13/migration/
    latitude: float = Field(..., example=20.2961)

backend\api\command_routes.py:41
  D:\SDARS map\backend\api\command_routes.py:41: PydanticDeprecatedSince20: Using extra keyword arguments on `Field` is deprecated and will be removed. Use `json_schema_extra` instead. (Extra keys: 'example'). Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.13/migration/
    longitude: float = Field(..., example=85.8245)

backend\api\command_routes.py:42
  D:\SDARS map\backend\api\command_routes.py:42: PydanticDeprecatedSince20: Using extra keyword arguments on `Field` is deprecated and will be removed. Use `json_schema_extra` instead. (Extra keys: 'example'). Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.13/migration/
    hazard_type: str = Field(..., example="flood")

backend\api\command_routes.py:43
  D:\SDARS map\backend\api\command_routes.py:43: PydanticDeprecatedSince20: Using extra keyword arguments on `Field` is deprecated and will be removed. Use `json_schema_extra` instead. (Extra keys: 'example'). Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.13/migration/
    risk_score: float = Field(..., example=0.82)

backend\api\command_routes.py:44
  D:\SDARS map\backend\api\command_routes.py:44: PydanticDeprecatedSince20: Using extra keyword arguments on `Field` is deprecated and will be removed. Use `json_schema_extra` instead. (Extra keys: 'example'). Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.13/migration/
    radius_km: Optional[float] = Field(5.0, example=5.0)

backend\api\server.py:74
  D:\SDARS map\backend\api\server.py:74: DeprecationWarning: 
          on_event is deprecated, use lifespan event handlers instead.
  
          Read more about it in the
          [FastAPI docs for Lifespan Events](https://fastapi.tiangolo.com/advanced/events/).
          
    @app.on_event("startup")

C:\Users\Mohan\AppData\Local\Programs\Python\Python312\Lib\site-packages\fastapi\applications.py:4681
  C:\Users\Mohan\AppData\Local\Programs\Python\Python312\Lib\site-packages\fastapi\applications.py:4681: DeprecationWarning: 
          on_event is deprecated, use lifespan event handlers instead.
  
          Read more about it in the
          [FastAPI docs for Lifespan Events](https://fastapi.tiangolo.com/advanced/events/).
          
    return self.router.on_event(event_type)  # ty: ignore[deprecated]

backend/tests/test_prediction_api.py::test_prediction_endpoint
  C:\Users\Mohan\AppData\Local\Programs\Python\Python312\Lib\site-packages\sqlalchemy\sql\schema.py:3627: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
    return util.wrap_callable(lambda ctx: fn(), fn)  # type: ignore

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
====================== 17 passed, 15 warnings in 26.91s =======================
```
- **Passed:** 17
- **Failed:** 0
- **Errors:** 0

---

## 10. CODE INVENTORY — WHAT EXISTS VS WHAT'S CLAIMED

### `backend/data_pipeline/`
- `__init__.py`: Package init file (complete, exports modules).
- `fetch_history.py`: Complete (571 lines; real Open-Meteo ERA5 / ERA5-Land ingestion, checkpointing, exponential backoff, coordinate batching, and Parquet aggregation).
- `fetch_terrain.py`: Complete (405 lines; NASA SRTM GL1 30 m DEM tile fetching, ocean bathymetry clamping, Gaussian smoothing, 30 m gradient calculation, and sub-cell slope aggregation).

### `backend/ai_models/`
- `__init__.py`: Package init file (complete).
- `multi_modal_predictor.py`: Complete (901 lines; 13-feature vector extraction, in-memory model inference, JMA alert scale classification, and procedural reasoning log generation).
- `training_data_generator.py`: Complete (265 lines; synthetic disaster scenario dataset generator, deprecated per integrity rules).
- `train_models.py`: Complete (167 lines; RandomForest training pipeline on synthetic CSV data, deprecated per integrity rules).
- `train_xgboost_models.py`: Complete (194 lines; XGBoost classifier training on synthetic Gaussian-noise dataset, deprecated per integrity rules).

### `backend/evaluation/`
- **Does not exist.**

### `reports/`
- **Does not exist.**

---

## 11. OPEN BLOCKERS

Verbatim contents of `BLOCKERS.md`:
```markdown
# SDARS Technical & Data Blockers Log

In accordance with SDARS Scientific Integrity Rule 3:
> *"If a data source is unavailable or labels for a hazard are too sparse, STOP and describe the problem in BLOCKERS.md. Do not substitute fake or proxy data silently."*

This file documents data unavailability, archived feed gaps, and technical constraints encountered in the historical pipeline.

---

## 1. Lightning Hazard Archive (v1 Deferred)

**Status:** BLOCKED / DEFERRED  
**Impacted Hazard:** Lightning (Hazard 6 of 8)  
**Date Logged:** 2026-10-24  

### Problem Description
Lightning (all 8 hazards, v1): no open, India-wide, hourly lightning archive is accessible. Blitzortung is volunteer-partial. Options for a future version: (a) pay for a commercial feed, (b) use IMD gridded lightning once available, (c) drop the hazard. Marking lightning as deferred for v1, not faked.

### Detail & Investigation
- Ground-based optical/RF detection networks such as Blitzortung rely on enthusiast stations and suffer from severe spatial bias and low detection efficiency across rural and coastal Odisha.
- Satellite optical lightning data (e.g. INSAT-3D/3DR Lightning Detection or MTG LI) is either not published in an open programmatic bulk archive for 1990–2024 or lacks verified ground calibration.
- Rather than training on synthetic lightning strikes or fabricating proxy labels, lightning hazard modeling is explicitly deferred in v1.

---

## 2. Convective Available Potential Energy (CAPE) in Open-Meteo ERA5

**Status:** SKIPPED / LOGGED  
**Impacted Variable:** Atmospheric Instability (`cape`)  
**Date Logged:** 2026-10-24  

### Problem Description
Open-Meteo Historical Weather API (`/v1/archive`) queries for variable `cape` return all `null` values across the entire Odisha bounding box (lat 17.8°N to 22.6°N, lon 81.3°E to 87.5°E) for ERA5 / ERA5-Land reanalysis.

### Resolution
In strict accordance with project rules against proxy or estimated substitutions, CAPE is omitted from the historical weather feature schema in `weather_6h.parquet` rather than substituting an arbitrary proxy. If thermodynamic soundings or regional mesoscale reanalysis (e.g. IMD NCUM reanalysis) become programmatically accessible, convective instability metrics will be incorporated.
```

---

## 12. SELF-ASSESSMENT

### 1. Which of Steps 0-3 are fully complete with evidence on disk?
- **Step 0 (Scientific Integrity Rules):** Fully complete. `AGENTS.md` contains the 8 immutable rules.
- **Step 1 (Audit):** Fully complete. `AUDIT.md` documents every feature, documentation contradiction, 13-feature source, external API failure mode, and SQLite demo seed vs live classification.
- **Step 2 (Hygiene & Security):** Fully complete.
  - Hardcoded OTP `123456` is strictly gated behind `DEMO_MODE=true` in `backend/api/auth_routes.py` and tested by `test_hygiene.py::test_no_demo_otp_when_demo_mode_false`.
  - Cesium Ion token literal was removed from tracked frontend code and dynamically injected via environment variable; 0 JWT literals remain in git tracking.
  - 24 unused dependencies removed from `requirements.txt` (zero occurrences of torch, keras, tensorflow, pymongo, twilio).
  - Isolated clean virtual environment `.venv-pinned-check` verified cleanly with all tests passing.
  - All 16 model binary files untracked from Git and inventoried in `HYGIENE_REPORT.md`.
  - Canonical DB path anchored to repository root via `DATABASE_URL` override in `backend/db/database.py`.

### 2. Which are partially complete, and exactly what's missing?
- **Step 3 (Historical Data Pipeline):** Partially complete.
  - **What exists on disk:**
    - `fetch_history.py` (571 lines) and `fetch_terrain.py` (405 lines) are fully implemented, tested (`tests/test_data_pipeline.py` all 5 tests pass), and documented in `data/DATASETS.md` and `data/README.md`.
    - `data/processed/terrain.parquet` is 100% complete (138 points, 30 m SRTM DEM gradients, bathymetry clamped, Gaussian smoothed, physical slope benchmarks verified: Puri 4.02°, Koraput 42.76°).
    - `data/processed/grid_metadata.parquet` is 100% complete (138 points).
    - `data/processed/weather_6h.parquet` exists on disk with 201,480 rows covering year 1990 for all 138 points. In addition, raw Parquet cache on disk contains year 2024 (138 points) and year 1991 (30 points).
  - **What is missing:**
    - The complete 36-year continuous multi-decade pull (1990–2025). The fetch paused when Open-Meteo returned `{"error":true,"reason":"Hourly API request limit exceeded. Please try again in the next hour."}`. Pulling all 4,968 point-years sequentially on Open-Meteo's public free tier takes ~3.5 hours across separate hourly quota windows.

### 3. Which haven't started?
- **Step 4 (Disaster Event Labels):** Not started (zero `labels_*.parquet` files exist).
- **Step 5 (Temporal Feature Engineering):** Not started.
- **Step 6 (Model Training on Real Data):** Not started (current models remain 100% synthetic).
- **Step 7 (Evaluation & Benchmark Metrics):** Not started (`reports/` does not exist).
- **Step 8 (Runtime Serving Integration):** Not started.
- **Step 9 (Distributional Skew Benchmarking):** Not started.

### 4. Is there anything in the repo that contradicts an earlier "done" claim?
- **No.** `HYGIENE_REPORT.md` Section 8 explicitly documents the open technical debts:
  1. The active runtime ML models in `backend/models/` were trained on synthetic data and must be replaced in Step 6.
  2. The full 1990–2025 weather dataset was not marked complete due to API hourly quota constraints, and was transparently reported as partial with checkpoints enabled.
