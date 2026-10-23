"""
Repository Hygiene and Security Tests.
Covers:
1. .env.example contains every env var used in the code.
2. No code path returns the demo OTP when DEMO_MODE is false.
3. SMTP failure returns 503 and stores no OTP.
4. DB path is identical regardless of the working directory (run from repo root and from backend/).
5. /api/health returns 200 with healthy status and timestamp.
"""
import os
import re
import sys
import subprocess
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

# Ensure backend and repo root are on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = REPO_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from api.server import app
from db.database import get_db, User, DB_URL


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

    ignore_dirs = {".git", ".agents", "venv", "__pycache__", "archive_local", "node_modules", ".tempmediaStorage"}
    used_vars = set()

    for root, dirs, files in os.walk(REPO_ROOT):
        dirs[:] = [d for d in dirs if d not in ignore_dirs]
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
    assert not missing, f"Variables used in code but missing from .env.example: {sorted(list(missing))}"


def test_no_demo_otp_when_demo_mode_false(monkeypatch):
    """Verify that when DEMO_MODE is false, no response returns the demo OTP code 123456."""
    monkeypatch.setenv("DEMO_MODE", "false")
    monkeypatch.delenv("SMTP_EMAIL", raising=False)
    monkeypatch.delenv("SMTP_PASSWORD", raising=False)

    with TestClient(app) as client:
        resp = client.post("/api/auth/login", json={"email": "security_test@sdars.io"})
        # When DEMO_MODE=false and SMTP is unconfigured, it must return 503
        assert resp.status_code == 503
        resp_json = resp.json()
        assert resp_json.get("demo_mode") is not True
        assert "123456" not in str(resp_json)
        assert "demo_otp" not in resp_json


def test_smtp_failure_returns_503_and_stores_no_otp(monkeypatch):
    """Verify that SMTP failure returns HTTP 503 and leaves no OTP in the database."""
    monkeypatch.setenv("DEMO_MODE", "false")
    monkeypatch.delenv("SMTP_EMAIL", raising=False)
    monkeypatch.delenv("SMTP_PASSWORD", raising=False)

    test_email = "smtp_fail_audit@sdars.io"
    # Ensure any previous test record is cleaned
    db = next(get_db())
    existing = db.query(User).filter(User.email == test_email).first()
    if existing:
        db.delete(existing)
        db.commit()

    with TestClient(app) as client:
        resp = client.post("/api/auth/login", json={"email": test_email})
        assert resp.status_code == 503
        assert resp.json().get("detail") == "Email provider not configured"

    # Verify no OTP was created or stored in the database
    user = db.query(User).filter(User.email == test_email).first()
    assert user is None or user.otp_code is None


def test_db_path_identical_regardless_of_working_dir():
    """Verify SQLite DB path resolves to the canonical repo-root file from both root and backend cwd."""
    script = "from db.database import DB_URL; print(DB_URL)"

    # Run from repository root
    p_root = subprocess.run(
        [sys.executable, "-c", "import sys; sys.path.insert(0, 'backend'); " + script],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=True
    )
    url_root = p_root.stdout.strip()

    # Run from backend directory
    p_backend = subprocess.run(
        [sys.executable, "-c", script],
        cwd=str(BACKEND_DIR),
        capture_output=True,
        text=True,
        check=True
    )
    url_backend = p_backend.stdout.strip()

    assert url_root == url_backend, f"DB_URL differs: {url_root} vs {url_backend}"
    assert "sdars_database.db" in url_root


def test_api_health_endpoint():
    """Verify /api/health returns 200 with operational status and timestamp."""
    with TestClient(app) as client:
        resp = client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("status") == "healthy"
        assert "timestamp" in data
