
from fastapi import APIRouter, Depends, HTTPException, Body, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from datetime import datetime, timedelta
import logging

from db.database import get_db, User
from services.email_service import EmailService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

class OTPManager:
    """Helper to manage OTP generation and validation"""
    @staticmethod
    def generate_otp():
        return "123456" # For Demo/Dev simplicity. Real app uses random.randint(100000, 999999)

@router.post("/login")
async def login(payload: dict = Body(...), db: Session = Depends(get_db)):
    """
    Step 1: User enters email. System sends OTP.
    Creates user if not exists.
    """
    email = payload.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")

    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        user = User(email=email)
        db.add(user)
        db.commit()
        db.refresh(user)

    # Generate OTP
    try:
        # Use EmailService to send real OTP if configured, or it returns mock
        otp_data = EmailService.send_otp(email)
        otp_code = otp_data['otp']
        expiry = otp_data['expiry']
        
        # Save to DB
        user.otp_code = otp_code
        user.otp_expiry = expiry
        db.commit()
        
        logger.info(f"OTP generated for {email}: {otp_code}")
        
        return {
            "message": "OTP sent successfully", 
            "demo_hint": "Check server logs or email" 
        }
    except Exception as e:
        logger.error(f"Login failed: {e}")
        # Fallback for resiliency
        user.otp_code = "123456"
        user.otp_expiry = datetime.utcnow() + timedelta(minutes=10)
        db.commit()
        return {"message": "Email service error. Use dev code 123456.", "dev_mode": True}

@router.post("/verify")
async def verify_otp(payload: dict = Body(...), db: Session = Depends(get_db)):
    """
    Step 2: User enters OTP. System verifies and logs them in.
    """
    email = payload.get("email")
    otp = payload.get("otp")
    
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    if not user.otp_code:
        raise HTTPException(status_code=400, detail="No OTP request found. Please login again.")
        
    # Check expiry
    if user.otp_expiry and datetime.utcnow() > user.otp_expiry:
        raise HTTPException(status_code=400, detail="OTP expired. Please request a new one.")
        
    if user.otp_code != otp:
        raise HTTPException(status_code=400, detail="Invalid OTP code")
        
    # Success
    user.is_verified = 1
    user.otp_code = None # Clear OTP for security
    db.commit()
    
    # Return user profile
    # Ensure current subscribed zones is list
    user_zones = user.subscribed_zones if user.subscribed_zones else []
    
    return {
        "message": "Login successful",
        "user_id": user.id,
        "email": user.email,
        "subscribed_zones": user_zones
    }

@router.post("/subscribe")
async def subscribe_zone(
    payload: dict = Body(...),
    db: Session = Depends(get_db)
):
    """
    Subscribe user to a specific zone.
    """
    try:
        email = payload.get("email")
        zone_name = payload.get("zone_name") # Using Name as ID for now
        
        logger.info(f"Subscription request: {email} for {zone_name}")
        
        user = db.query(User).filter(User.email == email).first()
        if not user:
            logger.warning(f"User not found: {email}")
            raise HTTPException(status_code=404, detail="User not found")
            
        # JSON columns in SQL Alchemy sometimes need explicit reassignment to trigger update
        current_zones = list(user.subscribed_zones) if user.subscribed_zones else []
        
        if zone_name not in current_zones:
            current_zones.append(zone_name)
            user.subscribed_zones = current_zones
            flag_modified(user, "subscribed_zones") # Important for JSON tracking
            db.commit()
            logger.info(f"User {email} subscribed to {zone_name}")
            
        return {"message": f"Subscribed to {zone_name}", "zones": current_zones}
    except Exception as e:
        logger.error(f"CRITICAL SUBSCRIPTION ERROR: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/unsubscribe")
async def unsubscribe_zone(
    payload: dict = Body(...),
    db: Session = Depends(get_db)
):
    """
    Unsubscribe user from a zone.
    """
    email = payload.get("email")
    zone_name = payload.get("zone_name") 
    
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    current_zones = list(user.subscribed_zones) if user.subscribed_zones else []
    
    if zone_name in current_zones:
        current_zones.remove(zone_name)
        user.subscribed_zones = current_zones
        flag_modified(user, "subscribed_zones")
        db.commit()
        
    return {"message": f"Unsubscribed from {zone_name}", "zones": current_zones}

@router.post("/test-alert")
async def send_test_alert(
    payload: dict = Body(...),
    db: Session = Depends(get_db)
):
    """
    Trigger a sample alert for a specific zone.
    """
    email = payload.get("email")
    zone_name = payload.get("zone_name")

    if not email or not zone_name:
        raise HTTPException(status_code=400, detail="Email and Zone Name are required")

    try:
        # Simulate a disaster alert
        EmailService.send_alert(
            to_email=email,
            zone_name=zone_name,
            risk_level="HIGH",
            details=f"This is a TEST ALERT for {zone_name}. No actual disaster detected."
        )
        return {"message": f"Test alert sent to {email} for {zone_name}"}
    except Exception as e:
        logger.error(f"Test Alert Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to send test alert")
@router.post("/promote-alert")
async def promote_alert(background_tasks: BackgroundTasks, payload: dict = Body(...)):
    """
    Promote a prediction to a full alert (Async Notification).
    """
    try:
        from services.advanced_alert_system import advanced_alert_system
        
        # Extract user email if provided
        user_email = payload.get('user_email')
        recipients = [user_email] if user_email else None
        
        # Create alert with override recipients
        alert = advanced_alert_system.create_alert(payload, recipients=recipients)
        
        # Schedule notification in background
        background_tasks.add_task(advanced_alert_system._send_notifications, alert)
        
        return {"message": f"Alert promoted. Notification queued for {user_email or 'subscribers'}", "alert_id": alert.alert_id}
    except Exception as e:
        logger.error(f"Promote Alert Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
