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
- Rather than computing artificial gradients across 0.5-degree cell centers (which would smooth out mountain ridges and river valleys over 55 km), `fetch_terrain.py` extracts the full ~1800 x 1800 pixel 30 m elevation patch for each cell, computes 30 m surface gradients using `np.gradient(patch, dy, dx)` where `dy = 30.87 m` and `dx = 30.87 * cos(lat)`, and computes the cell-level `mean_elevation_m`, `max_elevation_m`, `min_elevation_m`, and `max_slope_deg`.

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
