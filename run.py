import os
import sys

# Ensure UTF-8 encoding for standard output
try:
    if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

# Ensure both root and backend directory are at the top of sys.path
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

os.environ["PYTHONUNBUFFERED"] = "1"

if __name__ == "__main__":
    import uvicorn
    # Render provides PORT in the environment (defaulting to 10000 on Render, 8000 locally)
    port = int(os.environ.get("PORT", 8000))
    print(f"[SDARS] Cloud Runner starting on 0.0.0.0:{port}...", flush=True)
    uvicorn.run("backend.api.server:app", host="0.0.0.0", port=port, log_level="info")
