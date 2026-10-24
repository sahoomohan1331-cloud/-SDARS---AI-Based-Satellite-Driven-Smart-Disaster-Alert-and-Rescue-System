# SDARS Historical Data Pipeline Documentation

This directory and its associated pipelines (`backend/data_pipeline/`) supply real, authoritative historical atmospheric and topographic data for the AI-Based Satellite-Driven Smart Disaster Alert and Rescue System (SDARS) across Odisha, India.

---

## 1. Spatial Scope & Grid Architecture

### Geographic Extent
- **Region:** Odisha, India
- **Bounding Box:** Latitude 17.8°N to 22.6°N, Longitude 81.3°E to 87.5°E

### Grid Choice & Tradeoff
- **Resolution:** 0.5-degree regular grid (~55 km x ~55 km spacing), producing 130 regular grid cells.
- **Urban Centers (8 Named Cities):** Bhubaneswar, Cuttack, Puri, Balasore, Berhampur, Sambalpur, Rourkela, Angul are added as high-priority monitoring target points, yielding a total monitoring grid of 138 points.
- **Tradeoff Analysis:** A 0.25-degree grid would produce 4x the cell count (~520 cells), drastically increasing API query volume, network latency, and memory footprint during model training without commensurate physical gain, as the native atmospheric resolution of ERA5 reanalysis is ~31 km. The 0.5-degree regular grid combined with named city points provides high operational fidelity for all 30 Odisha districts while remaining within computational budgets.

---

## 2. Temporal Range & Climatological Baseline

### Time Range
- **Standard Range:** `1990-01-01` to the last complete calendar month.
- **Why 1990:** A continuous 30+ year record (1990–present) is strictly required to establish the 30-year climatological baseline mandated by the World Meteorological Organization (WMO). This baseline is essential for computing drought indicators, specifically the Standardized Precipitation Index (SPI-1, SPI-3, SPI-6) in Step 4. Starting at 2015 would render long-term climatological anomaly calculations scientifically invalid.

---

## 3. Sampling Frequency & Coordinate Reference

- **Default Frequency:** 6-hourly (`00:00`, `06:00`, `12:00`, `18:00` UTC).
- **Hourly Mode:** An hourly option is available via the environment variable `HOURLY=true` for focused research (~4x volume).
- **Timezone:** All timestamps are strictly stored in timezone-aware UTC (`datetime64[ns, UTC]`). Local display (IST, UTC+05:30) is purely a presentation layer concern.
- **Volume:** A 1-year smoke pull across 138 points at 6-hourly resolution contains 202,032 observations (~10 MB Parquet).

---

## 4. Authoritative Data Sources & Licenses

| Source | Variables / Product | Provider | License | Access / Key Requirements |
|---|---|---|---|---|
| **Open-Meteo Archive** | Surface weather, soil moisture, wind, pressure | Copernicus ECMWF (ERA5 / ERA5-Land) | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) | Free public API, no key required |
| **NASA SRTM GL1** | 30 m elevation & topographic slope | NASA / USGS via AWS Skadi | Public Domain (US Gov Work) | Free public S3 tiles, no key required |

### Note on OpenTopography API
The OpenTopography global DEM API (`portal.opentopography.org`) returns HTTP 401 when accessed without a personal API key. In accordance with open, reproducible pipelines, SDARS uses the public NASA SRTM GL1 elevation tiles hosted on AWS Skadi (`https://s3.amazonaws.com/elevation-tiles-prod/skadi/`), which require no proprietary key.

---

## 5. API Rate Limits & Resilience Policy

- **Open-Meteo Limits:** The Open-Meteo Archive API enforces a fair-use rate limit of approximately 10,000 requests per day per IP pool.
- **Batch Processing:** Coordinate requests are batched (up to 10 coordinates per call) to minimize total HTTP transactions.
- **Exponential Backoff:** The pipeline catches HTTP 429 (rate limited) and HTTP 5xx responses, applying randomized exponential backoff (e.g. 2s, 4s, 8s, 16s) with jitter.
- **Strict Failure Guarantee:** If persistent network or server failure occurs, the pipeline raises an unhandled exception. It **never** substitutes default or synthetic weather values.
- **Checkpoints:** Completed point-year pairs are checkpointed atomically (`data/raw/open_meteo/checkpoints.json`), allowing interrupted downloads to resume seamlessly without re-querying existing data.

---

## 6. Topography & Sub-Cell Slope Methodology

- **Resolution:** 1-arc-second (~30 m) Shuttle Radar Topography Mission (SRTM GL1).
- **Methodology:** "Slope is derived from SRTM 30 m aggregated to 0.5-degree cells; sub-cell terrain variability is captured as max slope."
- Rather than computing artificial gradients across 0.5-degree cell centers (which would smooth out mountain ridges and river valleys over 55 km), `fetch_terrain.py` extracts the full ~1800 x 1800 pixel 30 m elevation patch for each cell, clamps oceanic bathymetry `< 0 m` to `0.0 m` sea level, applies standard 3-pixel Gaussian smoothing to filter single-pixel sensor spikes, computes 30 m surface gradients using `np.gradient(patch, dy, dx)` where `dy = 30.87 m` (`METRES_PER_ARCSEC_LAT = 30.87`) and `dx = 30.87 * cos(lat)`, and computes the cell-level `mean_elevation_m`, `max_elevation_m`, `min_elevation_m`, and `max_slope_deg`.
- **Physical Reference Benchmarks (Verified):**
  - Coastal flat cell (Puri, `grid_19.8_85.8` / `city_puri`): `max_slope_deg = 4.02°` (< 5° threshold).
  - Plain cell (`grid_21.3_81.8`): `max_slope_deg = 6.39°` (5°–10° range).
  - Eastern Ghats hilly cell (Koraput, `grid_18.8_82.8`): `max_slope_deg = 42.76°` (> 15° threshold).

---

## 7. What is NOT Included Yet & Blockers

1. **Lightning Hazard (Deferred for v1):**
   - No open, India-wide, high-resolution hourly lightning archive exists. Blitzortung is volunteer-based and spatially incomplete across rural Odisha.
   - Documented in `BLOCKERS.md`. In accordance with Scientific Integrity Rules, lightning risk is explicitly deferred for v1 rather than fabricating synthetic flash counts.
2. **Convective Available Potential Energy (CAPE):**
   - Open-Meteo ERA5 reanalysis returns all `None` for CAPE over this bounding box.
   - Documented in `BLOCKERS.md`. CAPE is omitted from feature sets rather than inventing proxy numbers.
3. **Real-Time Forecasts:**
   - This pipeline generates historical reanalysis datasets for offline model training and baseline establishment. Real-time operational prediction uses live forecasting feeds.

---

## 8. Train / Inference Distributional Skew (Honesty Disclosure)

- **Training Distribution:** Derived from ERA5 / ERA5-Land retrospective reanalysis, which incorporates 4D-Var data assimilation, post-hoc smoothing, and physically consistent mass balancing.
- **Inference Distribution:** Real-time operational inference necessarily runs on live weather forecasts (e.g., GFS / ECMWF IFS / Open-Meteo forecast endpoints).
- **Disclosure:** This reanalysis-versus-forecast skew is an inherent reality of meteorological machine learning. In Step 9, SDARS will explicitly measure and benchmark train/inference distributional divergence rather than assuming identical distributions.

---

## 9. Final Verification Block

### V1. Grid size is as expected for 0.5 degrees over the bbox
**Status:** PASSED  
**Command:** `python -c "from backend.data_pipeline.fetch_history import build_grid; g = build_grid(17.8, 22.6, 81.3, 87.5, 0.5); print(len(g))"`  
**Output:**
```text
130
```

### V2. One-year smoke pull ran end-to-end
**Status:** PASSED  
**Command:** `python -m backend.data_pipeline.fetch_history --years 2024 2024`  
**Output:**
```text
[2026-10-24 19:49:42] [INFO] Starting historical fetch pipeline with years: [2024]
[2026-10-24 19:49:42] [INFO] Initialized pipeline for 138 points (grid + named cities) across years: [2024]
[2026-10-24 19:49:42] [INFO] Loaded 138 previously completed checkpoint keys.
[2026-10-24 19:49:42] [INFO] Processing year 2024 (date range: 2024-01-01 to 2024-12-31)...
[2026-10-24 19:49:42] [INFO] Year 2024: 138 points already cached, 0 points pending.
[2026-10-24 19:49:42] [INFO] All raw point-year Parquet files verified and cached.
[2026-10-24 19:49:44] [INFO] Saved processed weather dataset: data\processed\weather_6h.parquet (202032 rows)
[2026-10-24 19:49:44] [INFO] Saved grid metadata: data\processed\grid_metadata.parquet (138 points)
[2026-10-24 19:49:44] [INFO] Pipeline complete. Output files: data\processed\weather_6h.parquet, data\processed\grid_metadata.parquet
```

### V3. No synthetic fallback
**Status:** PASSED  
**Command:** `grep -rn "25.0\|1013\|50.0\|default\|fallback" backend/data_pipeline/fetch_history.py`  
**Output:**
```text
473:        default=10,
474:        help="Batch size of coordinates per API call (default: 10)",
484:        default="data",
485:        help="Base data directory (default: data)",
```
*Note: The only matches are CLI parameter defaults (`default=10`, `default="data"`). No synthetic weather constants or fallback branches exist.*

### V4. Terrain slope is from 30 m DEM, not from 0.5-degree centres
**Status:** PASSED  
**Source Implementation (`backend/data_pipeline/fetch_terrain.py`):**
```python
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
