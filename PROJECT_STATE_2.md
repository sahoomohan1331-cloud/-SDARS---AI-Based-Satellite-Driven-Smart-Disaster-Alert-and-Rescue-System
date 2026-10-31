# PROJECT_STATE_2.md — Full Project State Snapshot

**Snapshot Timestamp:** 2026-10-31 19:35:00 IST  
**Repository:** SDARS — AI-Based Satellite-Driven Smart Disaster Alert and Rescue System  
**Nature:** Read-Only Factual Audit & State Snapshot (Direct Command Outputs)

---

## 1. STEP COMPLETION STATUS

| Step | Scope | Status | Evidence Summary |
|---|---|---|---|
| **Step 0** | Scientific Integrity Rules in `AGENTS.md` | **YES** | Rule header verified at line 40 in `AGENTS.md` |
| **Step 1** | Audit Documentation (`AUDIT.md`) | **YES** | `AUDIT.md` exists and contains 136 lines |
| **Step 2** | Hygiene / Security (`HYGIENE_REPORT.md` & OTP Fix) | **YES** | `HYGIENE_REPORT.md` exists (509 lines); `DEMO_MODE` verified in `backend/api/auth_routes.py` |
| **Step 3** | Historical Weather Pipeline (`data/processed/weather_6h.parquet`) | **PARTIAL** | 201,480 rows compiled for year 1990 only; years 1991–2025 not compiled into processed file |

### Evidence Commands & Output

#### Step 0: `git grep -n "Scientific Integrity Rules" AGENTS.md`
```text
AGENTS.md:40:## 3. Scientific Integrity Rules
```

#### Step 1: `AUDIT.md` existence and line count
```powershell
if (Test-Path AUDIT.md) { (Get-Content AUDIT.md).Length } else { 'AUDIT.md does not exist' }
```
```text
136
```

#### Step 2: `HYGIENE_REPORT.md` existence & `DEMO_MODE` in `backend/api/auth_routes.py`
```powershell
Test-Path HYGIENE_REPORT.md; if (Test-Path HYGIENE_REPORT.md) { (Get-Content HYGIENE_REPORT.md).Length }
```
```text
True
509
```
```bash
git grep -n "DEMO_MODE" backend/api/auth_routes.py
```
```text
backend/api/auth_routes.py:46:    """Checks if DEMO_MODE is actively enabled via environment"""
backend/api/auth_routes.py:47:    return os.getenv("DEMO_MODE", "false").lower() == "true"
backend/api/auth_routes.py:53:    - DEMO_MODE=true: Allows fixed test code 123456 and returns demo_mode: true
backend/api/auth_routes.py:54:    - DEMO_MODE=false: Requires active SMTP, generates 6-digit secret OTP, stores SHA-256 hash
backend/api/auth_routes.py:104:        logger.warning(f"Login rejected for {email}: SMTP credentials unconfigured and DEMO_MODE=false.")
```

#### Step 3: Current State of `data/processed/weather_6h.parquet`
```text
rows: 201480
date range: 1990-01-01 00:00:00+00:00 to 1990-12-31 18:00:00+00:00
unique years: [1990]
unique hours: [0, 6, 12, 18]
```

---

## 2. WEATHER DATA — CURRENT COMPILED STATE

### Command
```python
import pandas as pd
df = pd.read_parquet('data/processed/weather_6h.parquet')
print('rows:', len(df))
print('date range:', df.timestamp_utc.min(), 'to', df.timestamp_utc.max())
print('unique years:', sorted(df.timestamp_utc.dt.year.unique().tolist()))
print('unique hours:', sorted(df.timestamp_utc.dt.hour.unique().tolist()))
```

### Output
```text
rows: 201480
date range: 1990-01-01 00:00:00+00:00 to 1990-12-31 18:00:00+00:00
unique years: [1990]
unique hours: [0, 6, 12, 18]
```

---

## 3. RAW CACHE — WHAT'S AVAILABLE TO COMPILE RIGHT NOW

### Command
```python
from pathlib import Path
om_dir = Path('data/raw/open_meteo')
all_files = list(om_dir.glob('*/*.parquet'))
from collections import Counter
year_counts = Counter(f.stem for f in all_files)
print('Years with point counts:', dict(sorted(year_counts.items())))
print('Years with all 138 points cached:', [y for y, c in year_counts.items() if c == 138])
```

### Output
```text
Years with point counts: {'1990': 138, '1991': 138, '1992': 138, '1993': 138, '1994': 138, '1995': 10, '2024': 138}
Years with all 138 points cached: ['1990', '1991', '1992', '1993', '1994', '2024']
```

---

## 4. TERRAIN DATA

### Command
```python
import pandas as pd
df = pd.read_parquet('data/processed/terrain.parquet')
print('rows:', len(df))
print('columns:', df.columns.tolist())
print(df[['max_slope_deg','p95_slope_deg']].describe())
```

### Output
```text
rows: 138
columns: ['grid_id', 'mean_elevation_m', 'max_elevation_m', 'min_elevation_m', 'max_slope_deg', 'p95_slope_deg']
       max_slope_deg  p95_slope_deg
count     138.000000     138.000000
mean       27.503406       9.556014
std        17.490242       8.537074
min         0.000000       0.000000
25%         5.875000       0.910000
50%        34.155000       8.970000
75%        41.022500      16.665000
max        52.650000      26.840000
```

---

## 5. LABELS (STEP 4) — HAS THIS STARTED AT ALL

### Command 1: Check for label parquets under `data/processed/`
```powershell
Get-ChildItem -Path data/processed -Filter 'labels_*.parquet' -Recurse -ErrorAction SilentlyContinue | Select-Object FullName
```
### Output
```text
(No files found - output empty)
```

### Command 2: Verify `FIRMS_MAP_KEY` placeholder in `.env.example`
```bash
git grep -n "FIRMS_MAP_KEY" .env.example
```
### Output
```text
.env.example:94:FIRMS_MAP_KEY=your_firms_map_key_here
```

---

## 6. DEAD EXPERIMENT CLEANUP STATUS

### Command
```powershell
Write-Host '--- data/raw/cds ---'
if (Test-Path 'data/raw/cds') { Get-ChildItem 'data/raw/cds' -Force } else { Write-Host 'data/raw/cds does not exist' }
Write-Host '--- data/raw/era5_google ---'
if (Test-Path 'data/raw/era5_google') { Get-ChildItem 'data/raw/era5_google' -Force -Recurse } else { Write-Host 'data/raw/era5_google does not exist' }
Write-Host '--- data/processed/weather_6h_2024.parquet ---'
if (Test-Path 'data/processed/weather_6h_2024.parquet') { Get-ChildItem 'data/processed/weather_6h_2024.parquet' } else { Write-Host 'data/processed/weather_6h_2024.parquet does not exist' }
```

### Output
```text
--- data/raw/cds ---
--- data/raw/era5_google ---


    Directory: D:\SDARS map\data\raw\era5_google


Mode                 LastWriteTime         Length Name                                                                 
----                 -------------         ------ ----                                                                 
d-----        25-10-2026     22:59                2024                                                                 


    Directory: D:\SDARS map\data\raw\era5_google\2024


Mode                 LastWriteTime         Length Name                                                                 
----                 -------------         ------ ----                                                                 
-a----        25-10-2026     22:59         116189 era5_odisha_20240101.nc                                              
--- data/processed/weather_6h_2024.parquet ---


    Directory: D:\SDARS map\data\processed


Mode                 LastWriteTime         Length Name                                                                 
----                 -------------         ------ ----                                                                 
-a----        25-10-2026     23:18          38649 weather_6h_2024.parquet                                              
```

### Cleanup Status Summary
- **`data/raw/cds/`**: Directory exists in tree, currently empty (0 items). Not archived.
- **`data/raw/era5_google/`**: Directory exists in tree containing `2024/era5_odisha_20240101.nc` (116,189 bytes). Still sitting in main tree, not archived.
- **`data/processed/weather_6h_2024.parquet`**: File exists in tree (38,649 bytes, modified 25-10-2026 23:18). Still present, not archived or removed.

---

## 7. SCRIPTS INVENTORY

### Command 1: `Get-ChildItem backend/data_pipeline/*.py | Select-Object Name, Length, LastWriteTime`
```text
Name                  Length LastWriteTime      
----                  ------ -------------      
fetch_era5_cds.py      17223 25-10-2026 21:02:28
fetch_era5_google.py   18219 25-10-2026 23:13:32
fetch_history.py       19737 24-10-2026 20:32:52
fetch_terrain.py       15687 24-10-2026 21:58:31
global_fetcher.py      14470 26-10-2026 00:49:27
global_gee_fetcher.py   8430 26-10-2026 01:23:07
__init__.py               35 24-10-2026 19:21:44
```

### Command 2: Detailed Line Count Inventory
```python
import os, datetime
base = 'backend/data_pipeline'
for f in sorted(os.listdir(base)):
    if f.endswith('.py'):
        p = os.path.join(base, f)
        stat = os.stat(p)
        mtime = datetime.datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
        with open(p, 'rb') as fp:
            lines = sum(1 for _ in fp)
        print(f'{f:25} {lines:6} lines {stat.st_size:8} bytes {mtime}')
```

### Output
```text
__init__.py                    1 lines       35 bytes 2026-10-24 19:21:44
fetch_era5_cds.py            472 lines    17223 bytes 2026-10-25 21:02:28
fetch_era5_google.py         502 lines    18219 bytes 2026-10-25 23:13:32
fetch_history.py             570 lines    19737 bytes 2026-10-24 20:32:52
fetch_terrain.py             413 lines    15687 bytes 2026-10-24 21:58:31
global_fetcher.py            374 lines    14470 bytes 2026-10-26 00:49:27
global_gee_fetcher.py        254 lines     8430 bytes 2026-10-26 01:23:07
```

---

## 8. GIT STATE

### Command 1: `git log --oneline -10`
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

### Command 2: `git status`
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

---

## 9. TEST SUITE

### Command: `pytest -v`

### Full Output
```text
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-7.4.3, pluggy-1.6.0 -- C:\Users\Mohan\AppData\Local\Programs\Python\Python312\python.exe
cachedir: .pytest_cache
rootdir: D:\SDARS map
configfile: pytest.ini
testpaths: tests, backend/tests
plugins: anyio-4.14.2, zarr-3.4.1
collecting ... collected 17 items

tests/test_data_pipeline.py::test_grid_generation PASSED                 [  5%]
tests/test_data_pipeline.py::test_no_synthetic_fallback PASSED           [ 11%]
tests/test_data_pipeline.py::test_parquet_schema PASSED                  [ 17%]
tests/test_data_pipeline.py::test_terrain_schema PASSED                  [ 23%]
tests/test_data_pipeline.py::test_datasets_md_exists PASSED              [ 29%]
tests/test_hygiene.py::test_env_example_contains_every_env_var FAILED    [ 35%]
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
=========================== short test summary info ===========================
FAILED tests/test_hygiene.py::test_env_example_contains_every_env_var - AssertionError: Variables used in code but missing from .env.example: ['EARTHENGINE_PROJECT', 'EE_PROJECT', 'GOOGLE_CLOUD_PROJECT']
assert not {'EARTHENGINE_PROJECT', 'EE_PROJECT', 'GOOGLE_CLOUD_PROJECT'}
================= 1 failed, 16 passed, 15 warnings in 32.31s ==================
```

### Pass/Fail Count
- **Passed:** 16
- **Failed:** 1 (`tests/test_hygiene.py::test_env_example_contains_every_env_var` due to untracked env vars referenced in newly added `global_gee_fetcher.py`)
- **Total:** 17

---

## 10. SELF-ASSESSMENT

### 1. Is the compile-step fix from the last session applied?
* **Answer:** **NO**.
* **Evidence:** Checking CLI arguments in `backend/data_pipeline/fetch_history.py` via `git grep -n "compile-only" backend/data_pipeline/fetch_history.py` yields zero matches. The script only defines `--years`, `--batch-size`, `--cities-only`, `--data-dir`, and `--force-point`. While the Python function `compile_processed_datasets` exists in the module, no `--compile-only` CLI switch is implemented.

### 2. Is the Open-Meteo pull currently running in any background process?
* **Answer:** **NO**.
* **Evidence:** Running `tasklist | findstr -i python` and PowerShell `Get-Process python*` returned 0 active Python processes.

### 3. What is the single next action needed to make `weather_6h.parquet` cover 1990-2025?
* **Answer:** Run the historical data pull to fetch the remaining un-cached grid points for years 1995–2025 (1995 has only 10/138 points, and 1996–2023 + 2025 have 0 points), followed by compiling the full set of 138 points × 36 years into `data/processed/weather_6h.parquet`.

### 4. Has anything under `backend/ai_models/` changed since the last audit (should still be untouched/synthetic)?
* **Answer:** **NO**.
* **Evidence:** `git status backend/ai_models/` returns clean working tree. `git log -n 5 backend/ai_models/` confirms the latest commit touching that directory was `66a0e8d` on October 8, 2026, which is prior to the start of the audit. All models under `backend/ai_models/` remain untouched and synthetic.
