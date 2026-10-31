# STATE_AUDIT.md — Factual, Unfiltered State Audit

**Audit Timestamp:** 2026-10-31 19:54:00 IST  
**Repository:** SDARS (`d:\SDARS map`)  
**Audit Type:** Strict Read-Only State Inspection

---

## 1. GIT STATUS

### Command 1: `git status`
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
	PROJECT_STATE_2.md
	WEATHER_DATA_STATE.md
	backend/data_pipeline/fetch_era5_cds.py
	backend/data_pipeline/fetch_era5_google.py
	backend/data_pipeline/global_fetcher.py
	backend/data_pipeline/global_gee_fetcher.py
	era5_downloader_tmp/
	test_nasa_sources.py

no changes added to commit (use "git add" and/or "git commit -a")
```

### Command 2: `git log --oneline -10`
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
```

### Analysis
- **Uncommitted changes:** **YES**. 3 tracked files have unstaged modifications (`.env.example`, `data/DATASETS.md`, `frontend/map.html`).
- **Untracked files:** 10 items, including 4 separate pipeline scripts (`fetch_era5_cds.py`, `fetch_era5_google.py`, `global_fetcher.py`, `global_gee_fetcher.py`), an experiment scratch dir (`era5_downloader_tmp/`), and 3 state documents.
- **Last 10 committed changes:** Ranged from commit `8525ec3` to `5b33338`, focused exclusively on Odisha terrain generation, p95 slope metric, and Open-Meteo test harnesses. None of the subsequent ERA5, CDS, Zarr, or GEE experiments were ever committed.

---

## 2. PIPELINE SCRIPTS INVENTORY

### Command: `ls backend/data_pipeline/`
```powershell
Get-ChildItem backend/data_pipeline | Select-Object Name, Length, LastWriteTime
```
```text
Name                  Length LastWriteTime      
----                  ------ -------------      
__pycache__                  26-10-2026 01:47:15
fetch_era5_cds.py     17223  25-10-2026 21:02:28
fetch_era5_google.py  18219  25-10-2026 23:13:32
fetch_history.py      19737  24-10-2026 20:32:52
fetch_terrain.py      15687  24-10-2026 21:58:31
global_fetcher.py     14470  26-10-2026 00:49:27
global_gee_fetcher.py 8430   26-10-2026 01:23:07
__init__.py           35     24-10-2026 19:21:44
```

### Script Status Breakdown

| Script | Lines | Status | Detailed Explanation |
|---|---|---|---|
| `__init__.py` | 1 | **Working** | Package marker. |
| `fetch_terrain.py` | 413 | **Working (Complete)** | Successfully fetched Open-Elevation SRTM tiles, computed slope & `p95_slope_deg`, generated `data/processed/terrain.parquet` (138 rows). |
| `fetch_history.py` | 570 | **Working (Partially Executed, Inactive)** | Odisha 138-point Open-Meteo fetcher. Works, but was stopped at year 1995 point 10. Processed file only contains 1990; years 1995–2025 uncompleted. |
| `fetch_era5_cds.py` | 472 | **Abandoned** | Copernicus CDS API client. Hit severe queuing latency and Windows file lock issues (`PermissionError: [Errno 13]`). Never finished; left untracked. |
| `fetch_era5_google.py` | 502 | **Abandoned** | Direct NetCDF downloader from Google Cloud ARCO-ERA5. Downloaded 1 day of data (`20240101.nc`) before being abandoned due to memory/chunk bloat. |
| `global_fetcher.py` | 374 | **Abandoned / Inactive** | ARCO-ERA5 Zarr store lazy chunk fetcher via `xarray`/`gcsfs`. Verified on 10 points in 5.69 min, then pivoted away from in favor of GEE export. |
| `global_gee_fetcher.py` | 254 | **Broken (CLI Auth Failure, Untracked)** | Fails on `ee.Initialize(project='orion-sdars-geo')` with HTTP 403 `Caller does not have required permission to use project orion-sdars-geo`. Cannot run from Python. |

---

## 3. DATA ON DISK

### Command 1: `ls -lh data/processed/`
```powershell
Get-ChildItem data/processed | Select-Object Name, Length, LastWriteTime
```
```text
Name                     Length LastWriteTime      
----                     ------ -------------      
grid_metadata.parquet      5646 24-10-2026 20:41:21
terrain.parquet            8355 24-10-2026 21:59:36
weather_6h.parquet      2206629 24-10-2026 20:41:21
weather_6h_2024.parquet   38649 25-10-2026 23:18:50
```

### Command 2: `ls -lh data/raw/`
```powershell
Get-ChildItem data/raw | Select-Object Name, Length, LastWriteTime
```
```text
Name        Length LastWriteTime      
----        ------ -------------      
cds                25-10-2026 21:03:27
era5_google        25-10-2026 22:59:22
open_meteo         25-10-2026 12:55:25
srtm               24-10-2026 19:41:17
```

### Exact Parquet Metadata & Row Counts
```python
import os
from pathlib import Path
import pandas as pd

proc_dir = Path('data/processed')
for p in sorted(proc_dir.glob('*.parquet')):
    df = pd.read_parquet(p)
    print(f'FILE: {p.name} ({p.stat().st_size} bytes)')
    print(f'  rows: {len(df)}, columns: {len(df.columns)}')
    print(f'  column names: {df.columns.tolist()[:6]}... (total {len(df.columns)})')
    if 'timestamp_utc' in df.columns:
        print(f'  date range: {df.timestamp_utc.min()} to {df.timestamp_utc.max()}')
        print(f'  unique years: {sorted(df.timestamp_utc.dt.year.unique().tolist())}')
    elif 'grid_id' in df.columns:
        print(f'  unique grid_ids: {df.grid_id.nunique()}')
```
```text
FILE: grid_metadata.parquet (5646 bytes)
  rows: 138, columns: 6
  column names: ['grid_id', 'lat', 'lon', 'elevation', 'is_city', 'city_name']... (total 6)
  unique grid_ids: 138
FILE: terrain.parquet (8355 bytes)
  rows: 138, columns: 6
  column names: ['grid_id', 'mean_elevation_m', 'max_elevation_m', 'min_elevation_m', 'max_slope_deg', 'p95_slope_deg']... (total 6)
  unique grid_ids: 138
FILE: weather_6h.parquet (2206629 bytes)
  rows: 201480, columns: 16
  column names: ['timestamp_utc', 'grid_id', 'lat', 'lon', 'temperature_2m', 'relative_humidity_2m']... (total 16)
  date range: 1990-01-01 00:00:00+00:00 to 1990-12-31 18:00:00+00:00
  unique years: [1990]
FILE: weather_6h_2024.parquet (38649 bytes)
  rows: 552, columns: 17
  column names: ['timestamp_utc', 'grid_id', 'lat', 'lon', 'temperature_2m', 'relative_humidity_2m']... (total 17)
  date range: 2024-01-01 00:00:00+00:00 to 2024-01-01 18:00:00+00:00
  unique years: [2024]
```

### Raw Directory Contents
- `data/raw/cds/`: **Empty** (0 files, 0 bytes).
- `data/raw/era5_google/`: **1 file** (`2024/era5_odisha_20240101.nc`, 116 KB).
- `data/raw/open_meteo/`: **969 files** (135.42 MB total). Contains 138 points for years 1990, 1991, 1992, 1993, 1994, and 2024; and 10 points for year 1995.
- `data/raw/srtm/`: **42 files** (294.37 MB total, complete SRTM elevation GeoTIFFs for Odisha).

---

## 4. MODELS

### Command: `ls -lh backend/models/`
```powershell
Get-ChildItem backend/models | Select-Object Name, Length, LastWriteTime
```
```text
Name                             Length LastWriteTime      
----                             ------ -------------      
cyclone_metrics.json                627 08-10-2026 16:59:11
cyclone_model.joblib             258115 08-10-2026 16:59:11
cyclone_model_metrics.json         1841 02-10-2026 04:17:21
cyclone_risk_model.joblib       2481737 02-10-2026 04:17:21
drought_metrics.json                632 08-10-2026 16:59:11
drought_model.joblib             284159 08-10-2026 16:59:11
drought_model_metrics.json         1842 02-10-2026 04:17:29
drought_risk_model.joblib       2776297 02-10-2026 04:17:29
fire_metrics.json                   603 08-10-2026 16:59:10
fire_model.joblib                258117 08-10-2026 16:59:10
fire_model_metrics.json            1826 02-10-2026 04:17:50
fire_risk_model.joblib          2149417 02-10-2026 04:17:50
flood_metrics.json                  633 08-10-2026 16:59:11
flood_model.joblib               246357 08-10-2026 16:59:11
flood_model_metrics.json           1843 02-10-2026 04:17:25
flood_risk_model.joblib         2220617 02-10-2026 04:17:25
heatwave_metrics.json               609 08-10-2026 16:59:12
heatwave_model.joblib            241797 08-10-2026 16:59:12
heatwave_model_metrics.json        1845 02-10-2026 04:17:33
heatwave_risk_model.joblib      2271337 02-10-2026 04:17:33
landslide_metrics.json              629 08-10-2026 16:59:11
landslide_model.joblib           240709 08-10-2026 16:59:11
landslide_model_metrics.json       1832 02-10-2026 04:17:41
landslide_risk_model.joblib     2843497 02-10-2026 04:17:41
lightning_metrics.json              612 08-10-2026 16:59:12
lightning_model.joblib           290355 08-10-2026 16:59:12
lightning_model_metrics.json       1826 02-10-2026 04:17:37
lightning_risk_model.joblib     2929897 02-10-2026 04:17:37
model_performance_summary.json      760 08-10-2026 16:59:12
storm_surge_metrics.json            622 08-10-2026 16:59:12
storm_surge_model.joblib         180127 08-10-2026 16:59:12
storm_surge_model_metrics.json     1836 02-10-2026 04:17:46
storm_surge_risk_model.joblib   2759817 02-10-2026 04:17:46
```

### Model Status Verdict
- **Did we retrain any models on new data?** **NO**.
- **Are we still using the old synthetic 99% models?** **YES**.
- Every single `.joblib` model file in `backend/models/` is dated **08-10-2026** (or **02-10-2026**). They were generated by `backend/ai_models/train_xgboost_models.py` using synthetic random data from `training_data_generator.py`. Not a single line of real weather or terrain data has been used in model training.

---

## 5. TESTS

### Command: `pytest`
```text
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-7.4.3, pluggy-1.6.0
rootdir: D:\SDARS map
configfile: pytest.ini
testpaths: tests, backend/tests
plugins: anyio-4.14.2, zarr-3.4.1
collected 17 items

tests\test_data_pipeline.py .....                                        [ 29%]
tests\test_hygiene.py F....                                              [ 58%]
backend\tests\test_command_api.py ...                                    [ 76%]
backend\tests\test_prediction_api.py ....                                [100%]

================================== FAILURES ===================================
___________________ test_env_example_contains_every_env_var ___________________

    def test_env_example_contains_every_env_var():
        """Verify that .env.example documents every environment variable referenced in code."""
        env_example_file = REPO_ROOT / ".env.example"
        assert env_example_file.exists(), ".env.example must exist in repo root"
    
        documented_vars = set()
        with open(env_example_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                match = re.match(r"^([A-Z0-9_]+)\s*=", line)
                if match:
                    documented_vars.add(match.group(1))
    
        # Pattern to find os.getenv("VAR") or os.environ.get("VAR") or os.environ["VAR"]
        pattern = re.compile(
            r'os\.(?:getenv|environ\.get)\s*\(\s*["\']([A-Z0-9_]+)["\']|os\.environ\s*\[\s*["\']([A-Z0-9_]+)["\']'
        )
        used_vars = set()
        for root, dirs, files in os.walk(REPO_ROOT):
            # Exclude hidden directories (.git, .venv*, etc.) and local non-code folders
            dirs[:] = [
                d for d in dirs
                if not d.startswith((".", "venv"))
                and d not in {"archive_local", "node_modules", "__pycache__", "build", "dist"}
            ]
            for file in files:
                if file.endswith(".py") and not file.startswith("test_hygiene"):
                    filepath = os.path.join(root, file)
                    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                    for match in pattern.finditer(content):
                        var_name = match.group(1) or match.group(2)
                        # Filter out standard Python environment control variables
                        if var_name not in {"PYTHONUTF8", "PYTHONIOENCODING"}:
                            used_vars.add(var_name)
    
        missing = used_vars - documented_vars
>       assert not missing, f"Variables used in code but missing from .env.example: {sorted(list(missing))}"
E       AssertionError: Variables used in code but missing from .env.example: ['EARTHENGINE_PROJECT', 'EE_PROJECT', 'GOOGLE_CLOUD_PROJECT']
E       assert not {'EARTHENGINE_PROJECT', 'EE_PROJECT', 'GOOGLE_CLOUD_PROJECT'}

tests\test_hygiene.py:69: AssertionError
============================== warnings summary ===============================
...
=========================== short test summary info ===========================
FAILED tests/test_hygiene.py::test_env_example_contains_every_env_var - AssertionError: Variables used in code but missing from .env.example: ['EARTHENGINE_PROJECT', 'EE_PROJECT', 'GOOGLE_CLOUD_PROJECT']
assert not {'EARTHENGINE_PROJECT', 'EE_PROJECT', 'GOOGLE_CLOUD_PROJECT'}
================= 1 failed, 16 passed, 15 warnings in 17.87s ==================
```

### Explanation of Failure
- `test_env_example_contains_every_env_var` scans the entire repository for `os.environ.get(...)` calls to verify that every environment variable is documented in `.env.example`.
- When `global_gee_fetcher.py` was authored, it introduced checks for `EE_PROJECT`, `EARTHENGINE_PROJECT`, and `GOOGLE_CLOUD_PROJECT`.
- Because these were never added to `.env.example`, the test immediately failed.

---

## 6. GEE STATUS

1. **Did you successfully initialize Google Earth Engine in `global_gee_fetcher.py`?**
   - **NO**. Running `python -u -m backend.data_pipeline.global_gee_fetcher --project orion-sdars-geo --test-run` from the command line repeatedly failed with:
     ```text
     ee.ee_exception.EEException: Caller does not have required permission to use project orion-sdars-geo. Grant the caller the roles/serviceusage.serviceUsageConsumer role, or a custom role with the serviceusage.services.use permission, by visiting https://console.developers.google.com/iam-admin/iam?project=orion-sdars-geo and then retry.
     ```
   - The local Python script has **never** successfully initialized Earth Engine without error.

2. **Did you submit the 100-point test task?**
   - **YES, but manually via the browser, not via the Python script.**
   - The export JavaScript was pasted into the Earth Engine Web Code Editor (`code.earthengine.google.com`), and the user clicked "RUN" on the Tasks tab.

3. **What is the Task ID?**
   - Task ID: **`EEBZXOBCSPZRO6BYIWBRM2BF`**
   - Task Name: `era5_global_100pts_jan2024`
   - Destination: Google Drive folder `SDARS_ERA5_Exports/era5_global_100pts_jan2024.csv`

---

## RUTHLESS VERDICT

We are **NOT** ready to pull global data from GEE today; this project is currently a mess of half-finished, uncommitted scripts. While a single 100-point 1-month test task (`EEBZXOBCSPZRO6BYIWBRM2BF`) was triggered by hand in the web browser, the automated Python extraction pipeline (`global_gee_fetcher.py`) cannot even initialize locally due to failing Google Cloud IAM permissions—breaking the repository's test suite in the process. Meanwhile, four separate abandoned fetching experiments (`fetch_era5_cds.py`, `fetch_era5_google.py`, `global_fetcher.py`, and NetCDF scratch files) litter the directory; the original Odisha Open-Meteo pipeline was abandoned mid-run with only year 1990 compiled and 1995–2025 missing; not a single machine learning model has ever touched real data (every `.joblib` model on disk remains the synthetic artifact from October 8); and zero hazard label parquets exist. Attempting to orchestrate 36 years of global data across 64,000 points today without working local API authentication, without an automated Drive-to-disk download mechanism, and without a verified feature pipeline will simply pile more unverified, uncommitted chaos onto an already stalled codebase.
