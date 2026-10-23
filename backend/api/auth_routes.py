from fastapi import APIRouter, Depends, HTTPException, Body, Request
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from datetime import datetime, timedelta
import logging
import os
import hashlib
import secrets
import time

from db.database import get_db, User
from services.email_service import EmailService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# Rate limiting in-memory storage: key -> list of request timestamps (epoch seconds)
_email_request_history = {}
_ip_request_history = {}
RATE_LIMIT_WINDOW = 600  # 10 minutes
MAX_REQUESTS_PER_EMAIL = 3
MAX_REQUESTS_PER_IP = 5
MAX_OTP_ATTEMPTS = 5

def _is_rate_limited(history_dict: dict, key: str, max_limit: int) -> bool:
    """Checks and updates sliding window rate limit for a key"""
    now = time.time()
    cutoff = now - RATE_LIMIT_WINDOW
    # Clean up old timestamps
    timestamps = [t for t in history_dict.get(key, []) if t > cutoff]
    if len(timestamps) >= max_limit:
        history_dict[key] = timestamps
        return True
    timestamps.append(now)
    history_dict[key] = timestamps
    return False

def _hash_otp(code: str) -> str:
    """Compute SHA-256 hash of plaintext OTP code"""
    return hashlib.sha256(code.strip().encode("utf-8")).hexdigest()

def is_demo_mode() -> bool:
    """Checks if DEMO_MODE is actively enabled via environment"""
    return os.getenv("DEMO_MODE", "false").lower() == "true"

@router.post("/login")
async def login(request: Request, payload: dict = Body(...), db: Session = Depends(get_db)):
    """
    Step 1: User enters email. System validates and sends OTP.
    - DEMO_MODE=true: Allows fixed test code 123456 and returns demo_mode: true
    - DEMO_MODE=false: Requires active SMTP, generates 6-digit secret OTP, stores SHA-256 hash
    - Returns HTTP 503 if SMTP is unconfigured or sending fails, storing NO OTP.
    - Rate limits by email (3 / 10m) and client IP (5 / 10m).
    """
    email = payload.get("email")
    if not email or "@" not in str(email):
        raise HTTPException(status_code=400, detail="A valid email address is required")

    email = str(email).strip().lower()
    client_ip = request.client.host if request.client else "127.0.0.1"

    # Enforce rate limits
    if _is_rate_limited(_email_request_history, email, MAX_REQUESTS_PER_EMAIL):
        raise HTTPException(
            status_code=429,
            detail="Too many verification requests for this email. Please wait 10 minutes."
        )
    if _is_rate_limited(_ip_request_history, client_ip, MAX_REQUESTS_PER_IP):
        raise HTTPException(
            status_code=429,
            detail="Too many verification requests from this IP address. Please wait 10 minutes."
        )

    demo_active = is_demo_mode()

    # DEMO MODE PATH
    if demo_active:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            user = User(email=email)
            db.add(user)
            db.commit()
            db.refresh(user)

        demo_code = "123456"
        user.otp_code = _hash_otp(demo_code)
        user.otp_expiry = datetime.utcnow() + timedelta(minutes=10)
        user.otp_attempts = 0
        db.commit()

        logger.info(f"[DEMO MODE] OTP assigned for {email}: {demo_code}")
        return {
            "message": "[DEMO MODE] Verification code is 123456",
            "demo_mode": True,
            "demo_otp": demo_code
        }

    # REAL MODE PATH
    # 1. Verify SMTP configuration BEFORE creating or modifying user OTP
    if not EmailService.is_configured():
        logger.warning(f"Login rejected for {email}: SMTP credentials unconfigured and DEMO_MODE=false.")
        raise HTTPException(status_code=503, detail="Email provider not configured")

    # 2. Generate secure 6-digit random code
    raw_otp = f"{secrets.randbelow(1000000):06d}"

    # 3. Attempt to dispatch email via SMTP
    try:
        EmailService.send_otp(email, raw_otp)
    except Exception as e:
        logger.error(f"SMTP dispatch failure for {email}: {e}")
        # DO NOT save or create any OTP in the database on sending failure
        raise HTTPException(status_code=503, detail="Email provider not configured")

    # 4. Only after successful dispatch: get/create user and save hashed OTP
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(email=email)
        db.add(user)
        db.commit()
        db.refresh(user)

    user.otp_code = _hash_otp(raw_otp)
    user.otp_expiry = datetime.utcnow() + timedelta(minutes=10)
    user.otp_attempts = 0
    db.commit()

    logger.info(f"Secure OTP dispatched via SMTP to {email}")
    return {
        "message": "OTP sent successfully to your email address.",
        "demo_mode": False
    }

@router.post("/verify")
async def verify_otp(payload: dict = Body(...), db: Session = Depends(get_db)):
    """
    Step 2: User enters OTP. System verifies hashed code, checks expiry, and enforces max 5 attempts.
    """
    email = payload.get("email")
    otp = payload.get("otp")

    if not email or not otp:
        raise HTTPException(status_code=400, detail="Email and OTP are both required")

    email = str(email).strip().lower()
    otp_str = str(otp).strip()

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not user.otp_code:
        raise HTTPException(status_code=400, detail="No active verification code found. Please request a new code.")

    # Check maximum attempt limit
    attempts = getattr(user, 'otp_attempts', 0) or 0
    if attempts >= MAX_OTP_ATTEMPTS:
        user.otp_code = None
        user.otp_expiry = None
        db.commit()
        raise HTTPException(
            status_code=400,
            detail="Too many failed attempts. This code has been invalidated. Please request a new code."
        )

    # Check expiration (10 minutes)
    if user.otp_expiry and datetime.utcnow() > user.otp_expiry:
        user.otp_code = None
        user.otp_expiry = None
        db.commit()
        raise HTTPException(status_code=400, detail="Verification code has expired. Please request a new one.")

    # Validate constant-time hash comparison
    submitted_hash = _hash_otp(otp_str)
    if not secrets.compare_digest(user.otp_code, submitted_hash):
        user.otp_attempts = attempts + 1
        db.commit()
        remaining = MAX_OTP_ATTEMPTS - user.otp_attempts
        if remaining <= 0:
            user.otp_code = None
            user.otp_expiry = None
            db.commit()
            raise HTTPException(
                status_code=400,
                detail="Too many failed attempts. Code has been invalidated. Please request a new code."
            )
        raise HTTPException(
            status_code=400,
            detail=f"Invalid verification code. {remaining} attempt(s) remaining."
        )

    # Success: activate user and clear one-time verification secrets
    user.is_verified = 1
    user.otp_code = None
    user.otp_expiry = None
    user.otp_attempts = 0
    db.commit()

    user_zones = user.subscribed_zones if user.subscribed_zones else []

    return {
        "message": "Login successful",
        "user_id": user.id,
        "email": user.email,
        "subscribed_zones": user_zones,
        "demo_mode": is_demo_mode()
    }

@router.post("/subscribe")
async def subscribe_zone(payload: dict = Body(...), db: Session = Depends(get_db)):
    """Subscribe user to a specific zone."""
    try:
        email = payload.get("email")
        zone_name = payload.get("zone_name")

        if not email or not zone_name:
            raise HTTPException(status_code=400, detail="Email and zone_name are required")

        email = str(email).strip().lower()
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        current_zones = list(user.subscribed_zones) if user.subscribed_zones else []
        if zone_name not in current_zones:
            current_zones.append(zone_name)
            user.subscribed_zones = current_zones
            flag_modified(user, "subscribed_zones")
            db.commit()

        return {"message": f"Subscribed to {zone_name}", "zones": current_zones}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Subscription error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
