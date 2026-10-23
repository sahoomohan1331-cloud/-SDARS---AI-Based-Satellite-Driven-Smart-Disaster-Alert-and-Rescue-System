# SDARS Repository Hygiene & Provenance Report

**Date:** October 2026  
**Scope:** Repository security, file tracking, secrets inspection, model provenance, and data-generator auditing.

---

## 1. Tracked Files Audit (`git ls-files`)

- **Database Files (`*.db`):** **None tracked.** Both `sdars_database.db` and `backend/sdars_database.db` are untracked on the filesystem and ignored by `.gitignore`.
- **Environment Files (`.env`):** **None tracked.** Only `backend/.env.example` is tracked. The local `backend/.env` file containing developer keys is untracked and ignored by `.gitignore`.
- **Model Binary Artifacts (`*.joblib`):** **16 files tracked.** The following 16 binary model files are tracked in git history under `backend/models/`:
  1. `backend/models/cyclone_model.joblib` (258 KB)
  2. `backend/models/cyclone_risk_model.joblib` (2.48 MB)
  3. `backend/models/drought_model.joblib` (284 KB)
  4. `backend/models/drought_risk_model.joblib` (2.77 MB)
  5. `backend/models/fire_model.joblib` (258 KB)
  6. `backend/models/fire_risk_model.joblib` (2.15 MB)
  7. `backend/models/flood_model.joblib` (246 KB)
  8. `backend/models/flood_risk_model.joblib` (2.22 MB)
  9. `backend/models/heatwave_model.joblib` (241 KB)
  10. `backend/models/heatwave_risk_model.joblib` (2.27 MB)
  11. `backend/models/landslide_model.joblib` (240 KB)
  12. `backend/models/landslide_risk_model.joblib` (2.84 MB)
  13. `backend/models/lightning_model.joblib` (290 KB)
  14. `backend/models/lightning_risk_model.joblib` (2.93 MB)
  15. `backend/models/storm_surge_model.joblib` (180 KB)
  16. `backend/models/storm_surge_risk_model.joblib` (2.76 MB)
- **Tracked presentation binaries:** `CB_PPT_Template.pptx` (8.1 MB) is tracked.

---

## 2. Git Ignore File Confirmation

The ignore file is correctly named **`.gitignore`** in the repository root (not `_gitignore`).  
Existing ignore rules cover `*.db`, `*.sqlite`, and `.env`, but missing rules for `*.joblib` and `archive_local/` must be added.

---

## 3. Git History Secrets Audit

An automated scan of the full Git history (`git log -p --all`) revealed:

- **Cesium Ion Access Token (JWT):** Detected in tracked file `frontend/3d-view.html` at line 661 (`Cesium.Ion.defaultAccessToken`).
- **OpenWeatherMap API Keys:** No active production keys committed to git history.
- **NASA API Keys:** No production keys committed to git history (`DEMO_KEY` in tracked documentation/config).
- **Twilio Tokens & SIDs:** None found in git history (only placeholder strings like `your_twilio_account_sid`).
- **SMTP Passwords:** None found in git history.
- **MongoDB Credentials:** None found in git history (`mongodb://localhost:27017/` local default only).

*(Note: Active developer keys and SMTP passwords exist on the local filesystem in untracked `backend/.env`, but have never been committed into the Git repository).*

### Secrets to rotate

- **Location:** `frontend/3d-view.html:661`
- **Type:** Cesium Ion Access Token (JWT)
- **Token Classification & Risk:** This token is a Cesium-provided public demo token from initial prototyping (not owned or managed by an organizational account). Hardcoding it in client-side markup poses a severe quota exhaustion and abuse risk: if scraped by third parties or if Cesium revokes public tutorial/demo credentials, 3D digital-twin terrain, photogrammetry, and 3D Tiles streaming will immediately fail with HTTP 401/429 errors.
- **Rotation Instruction:**
  1. Register for an official Cesium Ion account at https://ion.cesium.com/tokens and create a dedicated access token with domain restrictions set to your application origin (e.g., `*.onrender.com` or custom domain).
  2. Set `CESIUM_ION_TOKEN=<new_token>` in your local `.env` file and within the hosting deployment configuration (e.g., Render Dashboard Environment Variables).
  3. Never commit token literals into frontend HTML or JavaScript files. The application now loads this secret at runtime via server-side injection into `window.SDARS_CONFIG.CESIUM_ION_TOKEN`.

---

## 4. Usage of Mock OTP "123456"

The hardcoded mock OTP `"123456"` was detected in 4 distinct code locations:

1. `backend/api/auth_routes.py:21`: `return "123456"` in `OTPManager.generate_otp()`.
2. `backend/api/auth_routes.py:62`: `user.otp_code = "123456"` in `login` exception handler.
3. `backend/api/auth_routes.py:65`: Return payload `"message": "Email service error. Use dev code 123456."` in `login` exception handler.
4. `backend/services/email_service.py:37`: `return {'otp': '123456', ...}` inside `send_otp()` fallback when SMTP credentials are unconfigured.

---

## 5. Model Provenance & Runtime Inventory

| Model File | Producing Script | Loaded at Runtime by `multi_modal_predictor.py`? | Training Data Status |
|---|---|---|---|
| `backend/models/cyclone_model.joblib` | `backend/ai_models/train_xgboost_models.py` | **Yes (Primary)** | **Trained on synthetic data** |
| `backend/models/cyclone_risk_model.joblib` | `backend/ai_models/train_models.py` | No (Fallback) | Trained on synthetic data |
| `backend/models/drought_model.joblib` | `backend/ai_models/train_xgboost_models.py` | **Yes (Primary)** | **Trained on synthetic data** |
| `backend/models/drought_risk_model.joblib` | `backend/ai_models/train_models.py` | No (Fallback) | Trained on synthetic data |
| `backend/models/fire_model.joblib` | `backend/ai_models/train_xgboost_models.py` | **Yes (Primary)** | **Trained on synthetic data** |
| `backend/models/fire_risk_model.joblib` | `backend/ai_models/train_models.py` | No (Fallback) | Trained on synthetic data |
| `backend/models/flood_model.joblib` | `backend/ai_models/train_xgboost_models.py` | **Yes (Primary)** | **Trained on synthetic data** |
| `backend/models/flood_risk_model.joblib` | `backend/ai_models/train_models.py` | No (Fallback) | Trained on synthetic data |
| `backend/models/heatwave_model.joblib` | `backend/ai_models/train_xgboost_models.py` | **Yes (Primary)** | **Trained on synthetic data** |
| `backend/models/heatwave_risk_model.joblib` | `backend/ai_models/train_models.py` | No (Fallback) | Trained on synthetic data |
| `backend/models/landslide_model.joblib` | `backend/ai_models/train_xgboost_models.py` | **Yes (Primary)** | **Trained on synthetic data** |
| `backend/models/landslide_risk_model.joblib` | `backend/ai_models/train_models.py` | No (Fallback) | Trained on synthetic data |
| `backend/models/lightning_model.joblib` | `backend/ai_models/train_xgboost_models.py` | **Yes (Primary)** | **Trained on synthetic data** |
| `backend/models/lightning_risk_model.joblib` | `backend/ai_models/train_models.py` | No (Fallback) | Trained on synthetic data |
| `backend/models/storm_surge_model.joblib` | `backend/ai_models/train_xgboost_models.py` | **Yes (Primary)** | **Trained on synthetic data** |
| `backend/models/storm_surge_risk_model.joblib` | `backend/ai_models/train_models.py` | No (Fallback) | Trained on synthetic data |

*Conclusion:* Every model loaded at runtime by `multi_modal_predictor.py:53-74` is an XGBoost model trained entirely on synthetic data produced by `train_xgboost_models.py`.

---

## 6. Training-Data Generators Inventory

1. **`backend/ai_models/training_data_generator.py`**
   - *Status:* **DEPRECATED_SYNTHETIC**
   - *Mechanism:* Simulates 16,000 synthetic records across 8 scenarios and outputs `backend/data/training/disaster_data.csv`. Used by `train_models.py` (RandomForest).
2. **`generate_realistic_hazard_dataset()` in `backend/ai_models/train_xgboost_models.py:19-86`**
   - *Status:* **DEPRECATED_SYNTHETIC**
   - *Mechanism:* Independent random variable generation (6,000 samples) with Gaussian noise $N(0, 0.15)$ applied to linear threshold equations. Directly trains the active runtime XGBoost models.
3. **`generate_synthetic_satellite_image()` in `backend/data_collectors/satellite_collector.py:455-500`**
   - *Status:* **DEPRECATED_SYNTHETIC**
   - *Mechanism:* Generates random numpy multi-spectral matrices (`red`, `green`, `blue`, `nir`, `thermal`) for fallback testing when live NASA satellites are unavailable.
4. **`get_historical_weather()` fallback in `backend/data_collectors/weather_collector.py:179-188`**
   - *Status:* **DEPRECATED_SYNTHETIC**
   - *Mechanism:* Generates synthetic hourly weather time-series via `25 + np.random.randn()` when the Open-Meteo archive API fails.

---

## 7. Clean-venv verification

An isolated virtual environment `.venv-pinned-check` was created and verified against pinned `requirements.txt` and `requirements-dev.txt`.

### Full Pip Install Output (`pip install -r requirements.txt -r requirements-dev.txt`):
```text
Collecting aiohttp==3.14.3 (from -r requirements.txt (line 2))
  Using cached aiohttp-3.14.3-cp312-cp312-win_amd64.whl.metadata (8.5 kB)
Collecting fastapi==0.141.1 (from -r requirements.txt (line 3))
  Using cached fastapi-0.141.1-py3-none-any.whl.metadata (27 kB)
Collecting joblib==1.5.3 (from -r requirements.txt (line 4))
  Using cached joblib-1.5.3-py3-none-any.whl.metadata (5.5 kB)
Collecting numpy==2.5.3 (from -r requirements.txt (line 5))
  Using cached numpy-2.5.3-cp312-cp312-win_amd64.whl.metadata (6.6 kB)
Collecting pandas==3.0.5 (from -r requirements.txt (line 6))
  Using cached pandas-3.0.5-cp312-cp312-win_amd64.whl.metadata (19 kB)
Collecting Pillow==12.2.0 (from -r requirements.txt (line 7))
  Using cached pillow-12.2.0-cp312-cp312-win_amd64.whl.metadata (9.0 kB)
Collecting pydantic==2.13.5 (from -r requirements.txt (line 8))
  Using cached pydantic-2.13.5-py3-none-any.whl.metadata (110 kB)
Collecting python-dotenv==1.2.3 (from -r requirements.txt (line 9))
  Using cached python_dotenv-1.2.3-py3-none-any.whl.metadata (29 kB)
Collecting python-multipart==0.0.32 (from -r requirements.txt (line 10))
  Using cached python_multipart-0.0.32-py3-none-any.whl.metadata (2.1 kB)
Collecting requests==2.34.2 (from -r requirements.txt (line 11))
  Using cached requests-2.34.2-py3-none-any.whl.metadata (4.8 kB)
Collecting schedule==1.2.2 (from -r requirements.txt (line 12))
  Using cached schedule-1.2.2-py3-none-any.whl.metadata (3.8 kB)
Collecting scikit-learn==1.9.0 (from -r requirements.txt (line 13))
  Using cached scikit_learn-1.9.0-cp312-cp312-win_amd64.whl.metadata (11 kB)
Collecting sqlalchemy==2.0.54 (from -r requirements.txt (line 14))
  Using cached sqlalchemy-2.0.54-cp312-cp312-win_amd64.whl.metadata (9.9 kB)
Collecting uvicorn==0.51.0 (from uvicorn[standard]==0.51.0->-r requirements.txt (line 15))
  Using cached uvicorn-0.51.0-py3-none-any.whl.metadata (6.6 kB)
Collecting xgboost==3.4.1 (from -r requirements.txt (line 16))
  Using cached xgboost-3.4.1-py3-none-win_amd64.whl.metadata (2.0 kB)
Collecting pytest==7.4.3 (from -r requirements-dev.txt (line 3))
  Using cached pytest-7.4.3-py3-none-any.whl.metadata (7.9 kB)
Collecting ruff>=0.1.0 (from -r requirements-dev.txt (line 4))
  Downloading ruff-0.17.2-py3-none-win_amd64.whl.metadata (21 kB)
Collecting httpx>=0.27.0 (from -r requirements-dev.txt (line 5))
  Using cached httpx-0.28.1-py3-none-any.whl.metadata (7.1 kB)
Collecting aiohappyeyeballs>=2.5.0 (from aiohttp==3.14.3->-r requirements.txt (line 2))
  Using cached aiohappyeyeballs-2.7.1-py3-none-any.whl.metadata (5.9 kB)
Collecting aiosignal>=1.4.0 (from aiohttp==3.14.3->-r requirements.txt (line 2))
  Using cached aiosignal-1.4.0-py3-none-any.whl.metadata (3.7 kB)
Collecting attrs>=17.3.0 (from aiohttp==3.14.3->-r requirements.txt (line 2))
  Using cached attrs-26.1.0-py3-none-any.whl.metadata (8.8 kB)
Collecting frozenlist>=1.1.1 (from aiohttp==3.14.3->-r requirements.txt (line 2))
  Using cached frozenlist-1.8.0-cp312-cp312-win_amd64.whl.metadata (21 kB)
Collecting multidict<7.0,>=4.5 (from aiohttp==3.14.3->-r requirements.txt (line 2))
  Using cached multidict-6.9.1-cp312-cp312-win_amd64.whl.metadata (5.4 kB)
Collecting propcache>=0.2.0 (from aiohttp==3.14.3->-r requirements.txt (line 2))
  Using cached propcache-0.5.4-cp312-cp312-win_amd64.whl.metadata (25 kB)
Collecting typing_extensions>=4.4 (from aiohttp==3.14.3->-r requirements.txt (line 2))
  Using cached typing_extensions-4.16.0-py3-none-any.whl.metadata (3.3 kB)
Collecting yarl<2.0,>=1.17.0 (from aiohttp==3.14.3->-r requirements.txt (line 2))
  Using cached yarl-1.25.1-cp312-cp312-win_amd64.whl.metadata (115 kB)
Collecting starlette>=0.46.0 (from fastapi==0.141.1->-r requirements.txt (line 3))
  Using cached starlette-1.9.0-py3-none-any.whl.metadata (6.6 kB)
Collecting typing-inspection>=0.4.2 (from fastapi==0.141.1->-r requirements.txt (line 3))
  Using cached typing_inspection-0.4.4-py3-none-any.whl.metadata (2.6 kB)
Collecting annotated-doc>=0.0.2 (from fastapi==0.141.1->-r requirements.txt (line 3))
  Using cached annotated_doc-0.0.5-py3-none-any.whl.metadata (6.5 kB)
Collecting python-dateutil>=2.8.2 (from pandas==3.0.5->-r requirements.txt (line 6))
  Downloading python_dateutil-3.0.0-py2.py3-none-any.whl.metadata (8.2 kB)
Collecting tzdata (from pandas==3.0.5->-r requirements.txt (line 6))
  Downloading tzdata-2026.5-py2.py3-none-any.whl.metadata (1.4 kB)
Collecting annotated-types>=0.6.0 (from pydantic==2.13.5->-r requirements.txt (line 8))
  Using cached annotated_types-0.8.0-py3-none-any.whl.metadata (15 kB)
Collecting pydantic-core==2.46.5 (from pydantic==2.13.5->-r requirements.txt (line 8))
  Using cached pydantic_core-2.46.5-cp312-cp312-win_amd64.whl.metadata (6.7 kB)
Collecting charset_normalizer<4,>=2 (from requests==2.34.2->-r requirements.txt (line 11))
  Downloading charset_normalizer-3.5.2-cp312-win_amd64.whl.metadata (47 kB)
Collecting idna<4,>=2.5 (from requests==2.34.2->-r requirements.txt (line 11))
  Using cached idna-3.20-py3-none-any.whl.metadata (7.2 kB)
Collecting urllib3<3,>=1.26 (from requests==2.34.2->-r requirements.txt (line 11))
  Downloading urllib3-2.8.0-py3-none-any.whl.metadata (7.4 kB)
Collecting certifi>=2023.5.7 (from requests==2.34.2->-r requirements.txt (line 11))
  Downloading certifi-2026.10.23-py3-none-any.whl.metadata (2.5 kB)
Collecting scipy>=1.10.0 (from scikit-learn==1.9.0->-r requirements.txt (line 13))
  Downloading scipy-1.18.1-cp312-cp312-win_amd64.whl.metadata (61 kB)
Collecting narwhals>=2.0.1 (from scikit-learn==1.9.0->-r requirements.txt (line 13))
  Downloading narwhals-2.27.1-py3-none-any.whl.metadata (15 kB)
Collecting threadpoolctl>=3.5.0 (from scikit-learn==1.9.0->-r requirements.txt (line 13))
  Downloading threadpoolctl-3.7.0-py3-none-any.whl.metadata (24 kB)
Collecting greenlet>=1 (from sqlalchemy==2.0.54->-r requirements.txt (line 14))
  Using cached greenlet-3.5.6-cp312-cp312-win_amd64.whl.metadata (3.9 kB)
Collecting click>=7.0 (from uvicorn==0.51.0->uvicorn[standard]==0.51.0->-r requirements.txt (line 15))
  Using cached click-8.5.0-py3-none-any.whl.metadata (2.6 kB)
Collecting h11>=0.8 (from uvicorn==0.51.0->uvicorn[standard]==0.51.0->-r requirements.txt (line 15))
  Using cached h11-0.16.0-py3-none-any.whl.metadata (8.3 kB)
Collecting iniconfig (from pytest==7.4.3->-r requirements-dev.txt (line 3))
  Using cached iniconfig-2.3.1-py3-none-any.whl.metadata (2.8 kB)
Collecting packaging (from pytest==7.4.3->-r requirements-dev.txt (line 3))
  Using cached packaging-26.3-py3-none-any.whl.metadata (3.5 kB)
Collecting pluggy<2.0,>=0.12 (from pytest==7.4.3->-r requirements-dev.txt (line 3))
  Using cached pluggy-1.7.0-py3-none-any.whl.metadata (5.0 kB)
Collecting colorama (from pytest==7.4.3->-r requirements-dev.txt (line 3))
  Using cached colorama-0.4.6-py2.py3-none-any.whl.metadata (17 kB)
Collecting httptools>=0.8.0 (from uvicorn[standard]==0.51.0->-r requirements.txt (line 15))
  Downloading httptools-0.9.0-cp312-cp312-win_amd64.whl.metadata (3.7 kB)
Collecting pyyaml>=5.1 (from uvicorn[standard]==0.51.0->-r requirements.txt (line 15))
  Using cached pyyaml-6.0.3-cp312-cp312-win_amd64.whl.metadata (2.4 kB)
Collecting watchfiles>=0.20 (from uvicorn[standard]==0.51.0->-r requirements.txt (line 15))
  Using cached watchfiles-1.3.0-cp310-abi3-win_amd64.whl.metadata (5.0 kB)
Collecting websockets>=13.0 (from uvicorn[standard]==0.51.0->-r requirements.txt (line 15))
  Downloading websockets-17.3-cp312-cp312-win_amd64.whl.metadata (6.5 kB)
Collecting anyio (from httpx>=0.27.0->-r requirements-dev.txt (line 5))
  Using cached anyio-4.15.1-py3-none-any.whl.metadata (4.7 kB)
Collecting httpcore==1.* (from httpx>=0.27.0->-r requirements-dev.txt (line 5))
  Using cached httpcore-1.0.9-py3-none-any.whl.metadata (21 kB)
Collecting six>=1.6 (from python-dateutil>=2.8.2->pandas==3.0.5->-r requirements.txt (line 6))
  Using cached six-1.17.0-py2.py3-none-any.whl.metadata (1.7 kB)
Installing collected packages: websockets, urllib3, tzdata, typing_extensions, threadpoolctl, six, schedule, ruff, pyyaml, python-multipart, python-dotenv, propcache, pluggy, Pillow, packaging, numpy, narwhals, multidict, joblib, iniconfig, idna, httptools, h11, greenlet, frozenlist, colorama, click, charset_normalizer, certifi, attrs, annotated-types, annotated-doc, aiohappyeyeballs, yarl, uvicorn, typing-inspection, sqlalchemy, scipy, requests, python-dateutil, pytest, pydantic-core, httpcore, anyio, aiosignal, xgboost, watchfiles, starlette, scikit-learn, pydantic, pandas, httpx, aiohttp, fastapi
Successfully installed Pillow-12.2.0 aiohappyeyeballs-2.7.1 aiohttp-3.14.3 aiosignal-1.4.0 annotated-doc-0.0.5 annotated-types-0.8.0 anyio-4.15.1 attrs-26.1.0 certifi-2026.10.23 charset_normalizer-3.5.2 click-8.5.0 colorama-0.4.6 fastapi-0.141.1 frozenlist-1.8.0 greenlet-3.5.6 h11-0.16.0 httpcore-1.0.9 httptools-0.9.0 httpx-0.28.1 idna-3.20 iniconfig-2.3.1 joblib-1.5.3 multidict-6.9.1 narwhals-2.27.1 numpy-2.5.3 packaging-26.3 pandas-3.0.5 pluggy-1.7.0 propcache-0.5.4 pydantic-2.13.5 pydantic-core-2.46.5 pytest-7.4.3 python-dateutil-3.0.0 python-dotenv-1.2.3 python-multipart-0.0.32 pyyaml-6.0.3 requests-2.34.2 ruff-0.17.2 schedule-1.2.2 scikit-learn-1.9.0 scipy-1.18.1 six-1.17.0 sqlalchemy-2.0.54 starlette-1.9.0 threadpoolctl-3.7.0 typing-inspection-0.4.4 typing_extensions-4.16.0 tzdata-2026.5 urllib3-2.8.0 uvicorn-0.51.0 watchfiles-1.3.0 websockets-17.3 xgboost-3.4.1 yarl-1.25.1
```

### Full Pytest Output (`.venv-pinned-check/Scripts/pytest -v`):
```text
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-7.4.3, pluggy-1.7.0 -- D:\SDARS map\.venv-pinned-check\Scripts\python.exe
cachedir: .pytest_cache
rootdir: D:\SDARS map
configfile: pytest.ini
testpaths: tests, backend/tests
plugins: anyio-4.15.1
collecting ... collected 12 items

tests/test_hygiene.py::test_env_example_contains_every_env_var PASSED    [  8%]
tests/test_hygiene.py::test_no_demo_otp_when_demo_mode_false PASSED      [ 16%]
tests/test_hygiene.py::test_smtp_failure_returns_503_and_stores_no_otp PASSED [ 25%]
tests/test_hygiene.py::test_db_path_identical_regardless_of_working_dir PASSED [ 33%]
tests/test_hygiene.py::test_api_health_endpoint PASSED                   [ 41%]
backend/tests/test_command_api.py::test_command_status PASSED            [ 50%]
backend/tests/test_command_api.py::test_command_impact PASSED            [ 58%]
backend/tests/test_command_api.py::test_command_dispatch PASSED          [ 66%]
backend/tests/test_prediction_api.py::test_health_check PASSED           [ 75%]
backend/tests/test_prediction_api.py::test_api_status PASSED             [ 83%]
backend/tests/test_prediction_api.py::test_prediction_endpoint PASSED    [ 91%]
backend/tests/test_prediction_api.py::test_predictions_history PASSED    [100%]

============================== warnings summary ===============================
.venv-pinned-check\Lib\site-packages\fastapi\testclient.py:1
  D:\SDARS map\.venv-pinned-check\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

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

backend\api\server.py:73
  D:\SDARS map\backend\api\server.py:73: DeprecationWarning: 
          on_event is deprecated, use lifespan event handlers instead.
  
          Read more about it in the
          [FastAPI docs for Lifespan Events](https://fastapi.tiangolo.com/advanced/events/).
          
    @app.on_event("startup")

.venv-pinned-check\Lib\site-packages\fastapi\applications.py:4681
  D:\SDARS map\.venv-pinned-check\Lib\site-packages\fastapi\applications.py:4681: DeprecationWarning: 
          on_event is deprecated, use lifespan event handlers instead.
  
          Read more about it in the
          [FastAPI docs for Lifespan Events](https://fastapi.tiangolo.com/advanced/events/).
          
    return self.router.on_event(event_type)  # ty: ignore[deprecated]

backend/tests/test_prediction_api.py::test_prediction_endpoint
  D:\SDARS map\.venv-pinned-check\Lib\site-packages\sqlalchemy\sql\schema.py:3627: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
    return util.wrap_callable(lambda ctx: fn(), fn)  # type: ignore

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
====================== 12 passed, 16 warnings in 16.09s =======================
```

