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
