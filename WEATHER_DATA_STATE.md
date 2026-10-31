# Historical Weather Data State Snapshot

Snapshot generated at: `2026-10-25T23:28:00+05:30`
Repository: `D:\SDARS map`

---

## 1. PROCESSED DATA (the actual usable output)

Command:
```bash
python -c "
import pandas as pd
df = pd.read_parquet('data/processed/weather_6h.parquet')
print('rows:', len(df))
print('date range:', df.timestamp_utc.min(), 'to', df.timestamp_utc.max())
print('unique hours:', sorted(df.timestamp_utc.dt.hour.unique().tolist()))
print('unique grid points:', df.grid_id.nunique())
print('columns:', df.columns.tolist())
print('source (if a source column exists):', df['source'].unique().tolist() if 'source' in df.columns else 'no source column')
"
```

Output:
```text
rows: 201480
date range: 1990-01-01 00:00:00+00:00 to 1990-12-31 18:00:00+00:00
unique hours: [0, 6, 12, 18]
unique grid points: 138
columns: ['timestamp_utc', 'grid_id', 'lat', 'lon', 'temperature_2m', 'relative_humidity_2m', 'dew_point_2m', 'surface_pressure', 'wind_speed_10m', 'wind_gusts_10m', 'precipitation', 'cloud_cover', 'soil_moisture_0_to_7cm', 'soil_moisture_7_to_28cm', 'soil_moisture_28_to_100cm', 'elevation']
source (if a source column exists): no source column
```

---

## 2. ALL weather_6h*.parquet VARIANTS ON DISK

Command:
```powershell
Get-ChildItem -Recurse -Filter "weather_6h*.parquet" | Select-Object FullName, Length, LastWriteTime
```

Output:
```text
FullName                                             Length LastWriteTime      
--------                                             ------ -------------      
D:\SDARS map\data\processed\weather_6h.parquet      2206629 24-10-2026 20:41:21
D:\SDARS map\data\processed\weather_6h_2024.parquet   38649 25-10-2026 23:18:50
```

---

## 3. RAW CACHE STATE — PER SOURCE

### Source A: `data/raw/open_meteo/`

Command:
```powershell
Get-ChildItem -Recurse "data/raw/open_meteo" | Measure-Object -Property Length -Sum
```

Output:
```text
Count    : 839
Average  : 
Sum      : 141996297
Maximum  : 
Minimum  : 
Property : Length
```

Breakdown of points and years covered:
Command:
```bash
python -c "
from pathlib import Path
om_dir = Path('data/raw/open_meteo')
points = [p.name for p in om_dir.iterdir() if p.is_dir()]
all_files = list(om_dir.glob('*/*.parquet'))
years = sorted(list(set(f.stem for f in all_files)))
print('Points count:', len(points))
print('Total parquet files:', len(all_files))
print('Years covered:', years)
print('Files per year:', {y: len(list(om_dir.glob(f'*/{y}.parquet'))) for y in years})
"
```

Output:
```text
Points count: 138
Total parquet files: 838
Years covered: ['1990', '1991', '1992', '1993', '1994', '1995', '2024']
Files per year: {'1990': 138, '1991': 138, '1992': 138, '1993': 138, '1994': 138, '1995': 10, '2024': 138}
```
*(Note: 838 parquet files + 1 `checkpoints.json` = 839 items totaling 141,996,297 bytes).*

### Source B: `data/raw/cds/`

Command:
```powershell
Get-ChildItem -Recurse "data/raw/cds" | Measure-Object -Property Length -Sum
```

Output:
```text
(Directory exists, 0 items returned)
```

Inspection:
Command:
```bash
python -c "from pathlib import Path; print('Exists:', Path('data/raw/cds').exists(), 'Files:', list(Path('data/raw/cds').glob('**/*')))"
```

Output:
```text
Exists: True Files: []
```

### Source C: `data/raw/era5_google/`

Command:
```powershell
Get-ChildItem -Recurse "data/raw/era5_google" | Measure-Object -Property Length -Sum
```

Output:
```text
Count    : 1
Average  : 
Sum      : 116189
Maximum  : 
Minimum  : 
Property : Length
```

Inspection:
Command:
```bash
python -c "
from pathlib import Path
g_files = list(Path('data/raw/era5_google').glob('**/*.nc'))
print('NetCDF files count:', len(g_files))
for f in g_files:
    print('File:', f, 'size:', f.stat().st_size)
"
```

Output:
```text
NetCDF files count: 1
File: data\raw\era5_google\2024\era5_odisha_20240101.nc size: 116189
```

---

## 4. WHICH SCRIPT PRODUCED THE CURRENT weather_6h.parquet

### File Properties
Command:
```powershell
Get-Item "data/processed/weather_6h.parquet" | Format-List CreationTimeUtc, LastWriteTimeUtc, LastWriteTime
```

Output:
```text
CreationTimeUtc  : 24-10-2026 14:05:50
LastWriteTimeUtc : 24-10-2026 15:11:21
LastWriteTime    : 24-10-2026 20:41:21
```

### Script Last Modified Timestamps
Command:
```powershell
Get-Item "backend/data_pipeline/fetch_history.py", "backend/data_pipeline/fetch_era5_cds.py", "backend/data_pipeline/fetch_era5_google.py" | Select-Object Name, LastWriteTime
```

Output:
```text
Name                 LastWriteTime      
----                 -------------      
fetch_history.py     24-10-2026 20:32:52
fetch_era5_cds.py    25-10-2026 21:02:28
fetch_era5_google.py 25-10-2026 23:13:32
```

### Git Log Around Write Time
Command:
```bash
git log -n 5 --date=iso-local --format="%h %ad %s"
```

Output:
```text
5b33338 2026-10-24 22:05:31 +0530 Item 4: test p95_slope_deg bounds, ordering, and regional sanity
a5a884d 2026-10-24 22:04:07 +0530 Item 3: add p95_slope_deg robust slope metric, regenerate terrain.parquet, update docs
47f7526 2026-10-24 20:40:13 +0530 Follow-up 4: add resilient 429 rate limit backoff and launch 1990-2025 pull
e39825b 2026-10-24 20:22:34 +0530 Follow-up 3: verify terrain generation, row count, and regional slope samples
c28aeea 2026-10-24 20:17:50 +0530 Follow-up 2: add --force-point flag and detailed network request logging
```

### Conclusion
**`backend/data_pipeline/fetch_history.py` (Open-Meteo)** produced the current `data/processed/weather_6h.parquet` on `2026-10-24 20:41:21 IST`.

Evidence:
1. `data/processed/weather_6h.parquet` was written at `20:41:21 IST` on 2026-10-24, immediately following commit `47f7526` (`2026-10-24 20:40:13 IST`) where `fetch_history.py` compiled year 1990.
2. Neither `fetch_era5_cds.py` (created `2026-10-25 21:02:28 IST`) nor `fetch_era5_google.py` (created `2026-10-25 23:13:32 IST`) existed when `data/processed/weather_6h.parquet` was written.
3. Both `fetch_era5_cds.py` and `fetch_era5_google.py` target `weather_6h_{year}.parquet`, not `weather_6h.parquet`.

---

## 5. ALL THREE SCRIPTS — DO THEY EXIST AND WHAT STATE ARE THEY IN

Command:
```bash
python -c "
from pathlib import Path
import datetime

scripts = [
    'backend/data_pipeline/fetch_history.py',
    'backend/data_pipeline/fetch_era5_cds.py',
    'backend/data_pipeline/fetch_era5_google.py'
]

for s in scripts:
    p = Path(s)
    exists = p.exists()
    lines = len(p.read_text(encoding='utf-8').splitlines()) if exists else 0
    mtime = datetime.datetime.fromtimestamp(p.stat().st_mtime) if exists else None
    print(f'{s}:')
    print(f'  Exists: {exists}')
    print(f'  Lines: {lines}')
    print(f'  Last Modified: {mtime}')
"
```

Output:
```text
backend/data_pipeline/fetch_history.py:
  Exists: True
  Lines: 570
  Last Modified: 2026-10-24 20:32:52.335889
backend/data_pipeline/fetch_era5_cds.py:
  Exists: True
  Lines: 472
  Last Modified: 2026-10-25 21:02:28.175876
backend/data_pipeline/fetch_era5_google.py:
  Exists: True
  Lines: 502
  Last Modified: 2026-10-25 23:13:32.600671
```

Script function summaries:
1. `backend/data_pipeline/fetch_history.py`: Fetches historical hourly weather data via the Open-Meteo Historical Archive API across coordinates in batches, caches per-point annual parquets, and compiles 6-hourly datasets.
2. `backend/data_pipeline/fetch_era5_cds.py`: Submits bounding-box requests to the Copernicus Climate Data Store (CDS) API for ERA5 single levels, downloads a unified yearly NetCDF, and evaluates parity against Open-Meteo cache.
3. `backend/data_pipeline/fetch_era5_google.py`: Uses `era5-downloader` to retrieve daily single-level ERA5 NetCDFs from Google Cloud Public Datasets (`gs://gcp-public-data-arco-era5`), post-processes variables to SDARS schema, interpolates to 138 points, and tests parity.

---

## 6. LOG FILES

Command:
```powershell
Get-ChildItem -Recurse -Filter "*.log" | Select-Object FullName, Length, LastWriteTime
```

Output:
```text
FullName                                 Length LastWriteTime      
--------                                 ------ -------------      
D:\SDARS map\data\logs\fetch_history.log 224728 25-10-2026 13:02:46
D:\SDARS map\data\logs\fetch_terrain.log   6244 24-10-2026 21:59:36
```

Most recently modified log file: `D:\SDARS map\data\logs\fetch_history.log`.

Command:
```powershell
Get-Content -Tail 15 "data/logs/fetch_history.log"
```

Output:
```text
[2026-10-25 12:56:31] [INFO] Request started: sending HTTP GET to Open-Meteo (https://archive-api.open-meteo.com/v1/archive) for 10 coordinates (range: 1995-01-01 to 1995-12-31)...
[2026-10-25 12:56:31] [WARNING] HTTP 429 from Open-Meteo ({"reason":"Hourly API request limit exceeded. Please try again in the next hour.","error":true}). Backing off for 61.74s (attempt 2/8)...
[2026-10-25 12:57:33] [INFO] Request started: sending HTTP GET to Open-Meteo (https://archive-api.open-meteo.com/v1/archive) for 10 coordinates (range: 1995-01-01 to 1995-12-31)...
[2026-10-25 12:57:33] [WARNING] HTTP 429 from Open-Meteo ({"error":true,"reason":"Hourly API request limit exceeded. Please try again in the next hour."}). Backing off for 62.46s (attempt 3/8)...
[2026-10-25 12:58:36] [INFO] Request started: sending HTTP GET to Open-Meteo (https://archive-api.open-meteo.com/v1/archive) for 10 coordinates (range: 1995-01-01 to 1995-12-31)...
[2026-10-25 12:58:36] [WARNING] HTTP 429 from Open-Meteo ({"error":true,"reason":"Hourly API request limit exceeded. Please try again in the next hour."}). Backing off for 62.97s (attempt 4/8)...
[2026-10-25 12:59:39] [INFO] Request started: sending HTTP GET to Open-Meteo (https://archive-api.open-meteo.com/v1/archive) for 10 coordinates (range: 1995-01-01 to 1995-12-31)...
[2026-10-25 12:59:39] [WARNING] HTTP 429 from Open-Meteo ({"reason":"Hourly API request limit exceeded. Please try again in the next hour.","error":true}). Backing off for 61.37s (attempt 5/8)...
[2026-10-25 13:00:40] [INFO] Request started: sending HTTP GET to Open-Meteo (https://archive-api.open-meteo.com/v1/archive) for 10 coordinates (range: 1995-01-01 to 1995-12-31)...
[2026-10-25 13:00:41] [WARNING] HTTP 429 from Open-Meteo ({"error":true,"reason":"Hourly API request limit exceeded. Please try again in the next hour."}). Backing off for 63.08s (attempt 6/8)...
[2026-10-25 13:01:44] [INFO] Request started: sending HTTP GET to Open-Meteo (https://archive-api.open-meteo.com/v1/archive) for 10 coordinates (range: 1995-01-01 to 1995-12-31)...
[2026-10-25 13:01:44] [WARNING] HTTP 429 from Open-Meteo ({"error":true,"reason":"Hourly API request limit exceeded. Please try again in the next hour."}). Backing off for 61.28s (attempt 7/8)...
[2026-10-25 13:02:45] [INFO] Request started: sending HTTP GET to Open-Meteo (https://archive-api.open-meteo.com/v1/archive) for 10 coordinates (range: 1995-01-01 to 1995-12-31)...
[2026-10-25 13:02:46] [ERROR] Open-Meteo returned status 429 on final attempt 8: {"error":true,"reason":"Hourly API request limit exceeded. Please try again in the next hour."}
[2026-10-25 13:02:46] [ERROR] Network error fetching batch from Open-Meteo: 429 Client Error: Too Many Requests for url: https://archive-api.open-meteo.com/v1/archive?latitude=17.8%2C17.8%2C17.8%2C18.3%2C18.3%2C18.3%2C18.3%2C18.3%2C18.3%2C18.3&longitude=86.3%2C86.8%2C87.3%2C81.3%2C81.8%2C82.3%2C82.8%2C83.3%2C83.8%2C84.3&start_date=1995-01-01&end_date=1995-12-31&hourly=temperature_2m%2Crelative_humidity_2m%2Cdew_point_2m%2Csurface_pressure%2Cwind_speed_10m%2Cwind_gusts_10m%2Cprecipitation%2Ccloud_cover%2Csoil_moisture_0_to_7cm%2Csoil_moisture_7_to_28cm%2Csoil_moisture_28_to_100cm&timezone=UTC
```

---

## 7. GIT STATE

Command:
```bash
git log --oneline -15
```

Output:
```text
5b33338 Item 4: test p95_slope_deg bounds, ordering, and regional sanity
a5a884d Item 3: add p95_slope_deg robust slope metric, regenerate terrain.parquet, update docs
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
```

Command:
```bash
git status
```

Output:
```text
On branch main
Your branch is ahead of 'origin/main' by 27 commits.
  (use "git push" to publish your local commits)

Changes not staged for commit:
  (use "git add <file>..." to update what will be committed)
  (use "git restore <file>..." to discard changes in working directory)
	modified:   .env.example
	modified:   data/DATASETS.md
	modified:   frontend/map.html

Untracked files:
  (use "git add <file>..." to include in what will be committed)
	CB_PPT_Template original.pptx
	PROJECT_STATE.md
	WEATHER_DATA_STATE.md
	backend/data_pipeline/fetch_era5_cds.py
	backend/data_pipeline/fetch_era5_google.py
	era5_downloader_tmp/
	test_nasa_sources.py

no changes added to commit (use "git add" and/or "git commit -a")
```

---

## 8. CONTRADICTIONS OR RISKS

### 1. Is there more than one weather_6h.parquet-equivalent file that could be confused for "the" dataset?
**Yes.**
- `data/processed/weather_6h.parquet`: 201,480 rows, covers 138 grid points for the single year 1990 (from Open-Meteo).
- `data/processed/weather_6h_2024.parquet`: 552 rows, covers 138 grid points for 1 single day (`2024-01-01`) with 17 columns (from Google Cloud ERA5).
- In addition, `data/raw/open_meteo/` contains complete 138-point raw caches for years 1990, 1991, 1992, 1993, 1994, and 2024, but only 1990 has been compiled into `weather_6h.parquet`.

### 2. Does data/DATASETS.md accurately describe what's currently in data/processed/, or is it stale/wrong?
**It accurately describes what is currently on disk.**
Command:
```bash
python -c "
import hashlib
from pathlib import Path

for p in sorted(Path('data/processed').glob('*.parquet')):
    h = hashlib.sha256(p.read_bytes()).hexdigest()
    print(f'{p.name}: {h}')
"
```
Output:
```text
grid_metadata.parquet: 1b806bdb43bc3d2e9670ee89ef183c0adfeed1c793be242a3dbbdd0de600901f
terrain.parquet: 0e9cc996012d093b2494b1b5f7f05f6de5484b73f04ce89642176cf9b797c8ef
weather_6h.parquet: 42d9a8a038763bccf306fefd0299a92160d270c29ed049fbd2d5a89b3aca1f1b
weather_6h_2024.parquet: 189b3dc77bac8db5597ab2585c94b7025f79427744080987591325581f10553c
```
All four SHA-256 hashes, column counts, row counts, and date ranges in `data/processed/` match their documentation in `data/DATASETS.md`.

### 3. Is there any risk that a future script run could silently overwrite good data with partial/test data?
**Yes, in two specific ways:**
1. **`fetch_history.py` output path collision**: When `backend/data_pipeline/fetch_history.py` completes a run with a restricted year range (e.g. `--years 2024 2024`), line 384 unconditionally overwrites `data/processed/weather_6h.parquet` with only that year's data rather than appending or checking existing coverage:
   ```python
   # backend/data_pipeline/fetch_history.py:384
   full_weather.to_parquet(weather_out, index=False, engine="pyarrow")
   ```
2. **`fetch_era5_google.py` default parquet name**: When run without `--days-limit`, `fetch_era5_google.py` writes to `data/processed/weather_6h_{year}.parquet`. If invoked with `--days-limit 1` for smoke tests, it writes the 1-day (552-row) file directly to `weather_6h_2024.parquet`, replacing any full-year 2024 file that may have existed.
