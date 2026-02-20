"""
SDARS Advanced Alert System
Real-time notifications with multi-channel support
"""
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from enum import Enum
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os


class AlertSeverity(Enum):
    """Alert severity levels"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AlertChannel(Enum):
    """Notification channels"""
    SYSTEM = "SYSTEM"
    EMAIL = "EMAIL"
    SMS = "SMS"
    PUSH = "PUSH"
    WEBHOOK = "WEBHOOK"


class Alert:
    """Alert data model"""
    
    def __init__(
        self,
        alert_id: str,
        severity: AlertSeverity,
        title: str,
        message: str,
        location: Dict,
        disaster_type: str,
        channels: List[AlertChannel],
        metadata: Optional[Dict] = None
    ):
        self.alert_id = alert_id
        self.severity = severity
        self.title = title
        self.message = message
        self.location = location
        self.disaster_type = disaster_type
        self.channels = channels
        self.metadata = metadata or {}
        self.created_at = datetime.now()
        self.acknowledged = False
        self.acknowledged_at = None
        self.acknowledged_by = None
    
    def to_dict(self) -> Dict:
        """Convert alert to dictionary"""
        return {
            'alert_id': self.alert_id,
            'severity': self.severity.value,
            'title': self.title,
            'message': self.message,
            'location': self.location,
            'disaster_type': self.disaster_type,
            'channels': [ch.value for ch in self.channels],
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat(),
            'acknowledged': self.acknowledged,
            'acknowledged_at': self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            'acknowledged_by': self.acknowledged_by
        }
    
    def acknowledge(self, user_id: str = "system"):
        """Mark alert as acknowledged"""
        self.acknowledged = True
        self.acknowledged_at = datetime.now()
        self.acknowledged_by = user_id


class AdvancedAlertSystem:
    """
    Comprehensive alert management system
    Handles multi-channel notifications, alert history, and user preferences
    """
    
    def __init__(self):
        self.alerts: List[Alert] = []
        self.alert_history: List[Alert] = []
        self.user_preferences: Dict = {}
        self.alert_zones: List[Dict] = []
        
        # Load initial settings
        self._load_initial_settings()
    
    def _load_initial_settings(self):
        """Load settings from environment or DB"""
        from db.database import SessionLocal, SystemSettings
        from sqlalchemy.exc import OperationalError
        
        db = SessionLocal()
        try:
            self.load_settings_from_db(db)
        except OperationalError:
            print("⚠️ System settings table not ready. Using defaults.")
            # Set defaults to prevent startup crash
            self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
            self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
            self.smtp_user = os.getenv('SMTP_USER', '')
            self.smtp_password = os.getenv('SMTP_PASSWORD', '')
            self.user_preferences = {
                'default_user': {
                    'email': os.getenv('ALERT_EMAIL_TO', 'admin@sdars.com'),
                    'phone': os.getenv('ALERT_PHONE', '+1234567890'),
                    'channels': [AlertChannel.SYSTEM],
                    'severity_threshold': AlertSeverity.MEDIUM
                }
            }
        except Exception as e:
            print(f"⚠️ Error loading settings: {e}")
        finally:
            db.close()
            
    def load_settings_from_db(self, db):
        """Load dynamic settings from database"""
        from db.database import SystemSettings
        
        # Helper to get setting from DB or fallback to environment
        def get_setting(key, env_var, default):
            setting = db.query(SystemSettings).filter(SystemSettings.key == key).first()
            if setting:
                return setting.value
            return os.getenv(env_var, default)

        self.smtp_server = get_setting('smtp_server', 'SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(get_setting('smtp_port', 'SMTP_PORT', '587'))
        self.smtp_user = get_setting('smtp_user', 'SMTP_USER', '')
        self.smtp_password = get_setting('smtp_password', 'SMTP_PASSWORD', '')

        # Double check: if they are empty strings, fallback to env
        if not self.smtp_user: self.smtp_user = os.getenv('SMTP_USER', '')
        if not self.smtp_password: self.smtp_password = os.getenv('SMTP_PASSWORD', '')
        
        # Update user preferences with alert email
        alert_email = get_setting('alert_email_to', 'ALERT_EMAIL_TO', os.getenv('SMTP_USER', 'admin@sdars.com'))
        
        self.user_preferences = {
            'default_user': {
                'email': alert_email,
                'phone': os.getenv('ALERT_PHONE', '+1234567890'),
                'channels': [AlertChannel.SYSTEM, AlertChannel.EMAIL],
                'severity_threshold': AlertSeverity.MEDIUM,
                'quiet_hours': {'start': '22:00', 'end': '07:00'},
                'disaster_types': ['fire', 'flood', 'cyclone', 'earthquake']
            }
        }
        print(f"📡 Alert System: Loaded configuration for {self.smtp_user} (Target: {alert_email})")
    
    def create_alert(
        self,
        prediction: Dict,
        severity_override: Optional[AlertSeverity] = None,
        recipients: Optional[List[str]] = None
    ) -> Alert:
        """
        Create an alert from a disaster prediction
        
        Args:
            prediction: AI prediction data
            severity_override: Override calculated severity
        
        Returns:
            Created Alert object
        """
        # Extract prediction data
        overall_risk = prediction.get('overall_risk_level', 'LOW')
        primary_threat = prediction.get('primary_threat', 'unknown')
        location_name = prediction.get('location_name', 'Unknown')
        confidence = prediction.get(primary_threat, {}).get('confidence', 0)
        
        # Determine severity
        if severity_override:
            severity = severity_override
        else:
            if overall_risk == 'CRITICAL' or confidence >= 0.9:
                severity = AlertSeverity.CRITICAL
            elif overall_risk == 'HIGH' or confidence >= 0.7:
                severity = AlertSeverity.HIGH
            elif overall_risk == 'MEDIUM' or confidence >= 0.5:
                severity = AlertSeverity.MEDIUM
            else:
                severity = AlertSeverity.LOW
        
        # Determine notification channels based on severity but FORCE Email if we have specific overrides
        if severity == AlertSeverity.CRITICAL:
            channels = [AlertChannel.SYSTEM, AlertChannel.EMAIL, AlertChannel.SMS, AlertChannel.PUSH]
        elif severity == AlertSeverity.HIGH:
            channels = [AlertChannel.SYSTEM, AlertChannel.EMAIL, AlertChannel.PUSH]
        else:
            # Always include EMAIL and SYSTEM; the email service will filter if no recipients match
            channels = [AlertChannel.SYSTEM, AlertChannel.EMAIL]
        
        # FORCE EMAIL if manually promoted (recipients provided)
        if recipients and AlertChannel.EMAIL not in channels:
            channels.append(AlertChannel.EMAIL)
        
        # Generate alert message
        title = self._generate_alert_title(primary_threat, severity, location_name)
        message = self._generate_alert_message(prediction, severity)
        
        # Create alert ID
        alert_id = f"ALERT-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{primary_threat[:3].upper()}"
        
        # ⭐ CALCULATE MATCHED ZONES IMMEDIATELY
        matched_zones = []
        alert_lat = prediction.get('latitude')
        alert_lon = prediction.get('longitude')
        
        if alert_lat is not None and alert_lon is not None:
            from db.database import SessionLocal, Zone
            db = SessionLocal()
            try:
                zones = db.query(Zone).filter(Zone.is_active == 1).all()
                for zone in zones:
                    if self._is_point_in_polygon(alert_lat, alert_lon, zone.coordinates):
                        matched_zones.append({
                            'id': zone.id,
                            'name': zone.name
                        })
            except Exception as e:
                print(f"⚠️ Error matching zones: {e}")
            finally:
                db.close()

        # Create alert object
        alert = Alert(
            alert_id=alert_id,
            severity=severity,
            title=title,
            message=message,
            location={
                'name': location_name,
                'lat': alert_lat,
                'lon': alert_lon
            },
            disaster_type=primary_threat,
            channels=channels,
            metadata={
                'confidence': confidence,
                'overall_risk': overall_risk,
                'prediction': prediction,
                'additional_recipients': recipients or [],
                'matched_zones': matched_zones # ⭐ Added
            }
        )
        
        # Add to active alerts
        self.alerts.append(alert)
        
        # NOTE: Notification sending DEFERRED to acknowledgement step
        # self._send_notifications(alert) 
        
        print(f"⚠️ Alert Created (Pending Acknowledgement): {alert.alert_id}")
        
        return alert
    
    def _generate_alert_title(self, disaster_type: str, severity: AlertSeverity, location: str) -> str:
        """Generate alert title"""
        severity_emoji = {
            AlertSeverity.LOW: "ℹ️",
            AlertSeverity.MEDIUM: "⚠️",
            AlertSeverity.HIGH: "🚨",
            AlertSeverity.CRITICAL: "🆘"
        }
        
        emoji = severity_emoji.get(severity, "⚠️")
        disaster = disaster_type.upper()
        
        return f"{emoji} {severity.value} {disaster} ALERT - {location}"
    
    def _generate_alert_message(self, prediction: Dict, severity: AlertSeverity) -> str:
        """Generate detailed alert message"""
        primary_threat = prediction.get('primary_threat', 'unknown')
        location_name = prediction.get('location_name', 'Unknown')
        confidence = prediction.get(primary_threat, {}).get('confidence', 0)
        reasons = prediction.get(primary_threat, {}).get('reasons', [])
        
        message = f"A {severity.value} {primary_threat} risk has been detected in {location_name}.\n\n"
        message += f"Confidence Level: {confidence*100:.1f}%\n\n"
        
        if reasons:
            message += "Key Indicators:\n"
            for i, reason in enumerate(reasons[:3], 1):
                message += f"  {i}. {reason}\n"
        
        if severity in [AlertSeverity.HIGH, AlertSeverity.CRITICAL]:
            message += "\n⚠️ IMMEDIATE ACTION REQUIRED:\n"
            message += "  • Move to a safe location\n"
            message += "  • Follow evacuation procedures\n"
            message += "  • Stay informed through official channels\n"
            
            # Add shelter information if available
            shelters = prediction.get('shelters', [])
            if shelters:
                message += f"\nNearest Emergency Shelter:\n"
                message += f"  📍 {shelters[0].get('name', 'N/A')}\n"
                if 'distance_km' in shelters[0]:
                    message += f"  📏 {shelters[0]['distance_km']} km away\n"
        
        return message
    
    def _send_notifications(self, alert: Alert):
        """Send notifications through all specified channels"""
        for channel in alert.channels:
            if channel == AlertChannel.SYSTEM:
                self._send_system_notification(alert)
            elif channel == AlertChannel.EMAIL:
                self._send_email_notification(alert)
            elif channel == AlertChannel.SMS:
                self._send_sms_notification(alert)
            elif channel == AlertChannel.PUSH:
                self._send_push_notification(alert)
    
    def _send_system_notification(self, alert: Alert):
        """Log system notification"""
        print(f"\n{'='*80}")
        print(f"🔔 SYSTEM NOTIFICATION")
        print(f"{'='*80}")
        print(f"Alert ID: {alert.alert_id}")
        print(f"Severity: {alert.severity.value}")
        print(f"Title: {alert.title}")
        print(f"Time: {alert.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"\nMessage:\n{alert.message}")
        print(f"{'='*80}\n")
    
    def _is_point_in_polygon(self, lat: float, lon: float, polygon: List[List[float]]) -> bool:
        """Ray casting algorithm to check if point is inside polygon"""
        n = len(polygon)
        inside = False
        p1x, p1y = polygon[0][1], polygon[0][0] # lon, lat
        for i in range(n + 1):
            p2x, p2y = polygon[i % n][1], polygon[i % n][0]
            if lon > min(p1y, p2y):
                if lon <= max(p1y, p2y):
                    if lat <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (lon - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or lat <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        return inside

    async def send_zone_verification(self, zone_name: str, recipients: List[str]) -> Dict:
        """
        Send a specialized verification email when a new zone is created.
        Returns a report of successes and failures.
        """
        print(f"🛰️ [VERIFICATION START] Zone: {zone_name} | Recipients: {recipients}")
        
        if not self.smtp_user or not self.smtp_password:
            print("❌ [VERIFICATION ABORTED] SMTP credentials missing.")
            return {"status": "error", "message": "SMTP not configured", "successes": [], "failures": recipients}

        report = {"successes": [], "failures": []}
        subject = f"✅ SDARS: Verify Monitoring for {zone_name}"
        text_body = f"Hello,\n\nYou have been added as an emergency contact for the SDARS Alert Zone: {zone_name}.\n\nNo action is required. You will receive real-time alerts if a threat is detected.\n\nThank you."
        
        # Simplified HTML for reliability
        html_body = f"""
        <div style="font-family: sans-serif; max-width: 500px; border: 1px solid #10b981; border-radius: 12px; overflow: hidden;">
            <div style="background: #10b981; color: white; padding: 20px; font-weight: bold; font-size: 18px;">
                📡 TACTICAL LINK ESTABLISHED
            </div>
            <div style="padding: 24px;">
                <p>Establishing secure monitoring for zone: <strong>{zone_name}</strong></p>
                <p>Your email has been registered as a <strong>High-Priority Emergency Contact</strong>.</p>
                <div style="background: #f0fdf4; padding: 15px; border-radius: 8px; font-size: 14px; border: 1px solid #d1fae5;">
                    📍 You will receive automated SITREPs if satellite arrays detect thermal anomalies, water displacement, or pressure drops in this sector.
                </div>
            </div>
        </div>
        """

        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=15) as server:
                server.ehlo()
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                
                for recipient in recipients:
                    if not recipient or '@' not in recipient:
                        report["failures"].append(recipient)
                        continue
                    try:
                        msg = MIMEMultipart('alternative')
                        msg['Subject'] = subject
                        msg['From'] = f"SDARS Alert System <{self.smtp_user}>"
                        msg['To'] = recipient
                        msg.attach(MIMEText(text_body, 'plain'))
                        msg.attach(MIMEText(html_body, 'html'))
                        server.send_message(msg)
                        report["successes"].append(recipient)
                        print(f"   📬 Verification sent to: {recipient}")
                    except Exception as e:
                        print(f"   ❌ Failed for {recipient}: {e}")
                        report["failures"].append(recipient)
            
            return {"status": "success", "report": report}
        except Exception as e:
            print(f"❌ SMTP Handshake Failure: {e}")
            return {"status": "error", "message": str(e), "failures": recipients}

    def _send_email_notification(self, alert: Alert):
        """Send email notification with targeted zone-based recipients"""
        if not self.smtp_user or not self.smtp_password:
            print(f"📧 [EMAIL FAILURE] SMTP credentials not configured. Please check Strategic Config or .env")
            return
        
        try:
            # 1. Start with global default recipient
            recipients = []
            default_email = self.user_preferences.get('default_user', {}).get('email')
            if default_email:
                recipients.append(default_email)
            
            # 2. Find matching zones and add their specific recipients
            from db.database import SessionLocal, Zone, User
            db = SessionLocal()
            try:
                alert_lat = alert.location.get('lat')
                alert_lon = alert.location.get('lon')
                
                matched_zone_names = []
                if alert_lat is not None and alert_lon is not None:
                    # Fetch active zones
                    zones = db.query(Zone).filter(Zone.is_active == 1).all()
                    for zone in zones:
                        if self._is_point_in_polygon(alert_lat, alert_lon, zone.coordinates):
                            matched_zone_names.append(zone.name)
                            if zone.recipient_emails:
                                print(f"🎯 MATCHED ZONE: {zone.name} - Adding recipients: {zone.recipient_emails}")
                                recipients.extend(zone.recipient_emails)
                
                # 3. Fetch Subscribers (Users who have these zones in their subscribed_zones)
                if matched_zone_names:
                    # We need to find users whose subscribed_zones (JSON list) contains any of the matched_zone_names
                    # Since subscribed_zones is a JSON column, we'll fetch all users and filter in Python
                    # or use JSON_CONTAINS if supported. For SQLite/JSON, we'll do careful Python filtering.
                    active_users = db.query(User).all()
                    subscriber_count = 0
                    for user in active_users:
                        if user.email and user.subscribed_zones:
                            # Check if user has ANY of the matched zones
                            user_subs = user.subscribed_zones if isinstance(user.subscribed_zones, list) else []
                            if any(z in user_subs for z in matched_zone_names):
                                if user.email not in recipients:
                                    recipients.append(user.email)
                                    subscriber_count += 1
                    
                    if subscriber_count > 0:
                        print(f"👥 Added {subscriber_count} subscribers from the User table for zones: {matched_zone_names}")
                
                # 4. Add explicitly provided additional recipients (e.g. acknowledging user)
                additional = alert.metadata.get('additional_recipients', [])
                if additional:
                    print(f"👤 Adding user-specific recipients: {additional}")
                    recipients.extend(additional)

                # Deduplicate and filter out empty values
                recipients = list(set([r for r in recipients if r and isinstance(r, str) and '@' in r]))
            finally:
                db.close()
            
            if not recipients:
                print("📧 [EMAIL SKIPPED] No valid recipients or subscribers found for this alert.")
                return

            print(f"📧 Sending alerts to {len(recipients)} recipients: {recipients}")
            
            # Generate content once
            text_body = f"{alert.title}\n\n{alert.message}\n\nLocation: {alert.location.get('name')}"
            html_body = self._generate_html_email(alert)
            
            try:
                with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=10) as server:
                    server.ehlo()
                    server.starttls()
                    server.ehlo()
                    server.login(self.smtp_user, self.smtp_password)
                    print(f"   🔓 SMTP Login Success as {self.smtp_user}")
                    
                    for recipient in recipients:
                        try:
                            msg = MIMEMultipart('alternative')
                            msg['Subject'] = alert.title
                            msg['From'] = f"SDARS Alerts <{self.smtp_user}>"
                            msg['To'] = recipient
                            
                            msg.attach(MIMEText(text_body, 'plain'))
                            msg.attach(MIMEText(html_body, 'html'))
                            
                            server.send_message(msg)
                            print(f"   ✅ Sent to: {recipient}")
                        except Exception as inner_e:
                            print(f"   ❌ Failed to send to {recipient}: {inner_e}")
                            
            except Exception as smtp_e:
                print(f"   ⛔ SMTP Connection/Login Error: {smtp_e}")
                
        except Exception as e:
            print(f"❌ Alert System Global Error: {e}")
    
    def _generate_html_email(self, alert: Alert) -> str:
        """Generate HTML email template"""
        severity_colors = {
            AlertSeverity.LOW: '#3b82f6',
            AlertSeverity.MEDIUM: '#f59e0b',
            AlertSeverity.HIGH: '#ef4444',
            AlertSeverity.CRITICAL: '#dc2626'
        }
        
        color = severity_colors.get(alert.severity, '#6b7280')
        
        # Determine header text
        header_text = "TACTICAL ALERT"
        if "ACKNOWLEDGED" in alert.title:
            header_text = "ALERT ACKNOWLEDGED"
            color = "#16a34a" # Success Green
        
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: {color}; color: white; padding: 20px; border-radius: 8px 8px 0 0;">
                <h2 style="margin: 0; font-size: 14px; text-transform: uppercase; letter-spacing: 1px; opacity: 0.8;">{header_text}</h2>
                <h1 style="margin: 5px 0 0 0; font-size: 24px;">{alert.title}</h1>
                <p style="margin: 10px 0 0 0; opacity: 0.9;">
                    {alert.created_at.strftime('%B %d, %Y at %H:%M:%S')}
                </p>
            </div>
            <div style="background: #f9fafb; padding: 20px; border-radius: 0 0 8px 8px;">
                <div style="background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                    <pre style="white-space: pre-wrap; font-family: Arial, sans-serif; margin: 0;">
{alert.message}
                    </pre>
                </div>
                <div style="background: #eff6ff; padding: 15px; border-radius: 8px; border-left: 4px solid #3b82f6;">
                    <strong>Location:</strong> {alert.location.get('name', 'Unknown')}<br>
                    <strong>Disaster Type:</strong> {alert.disaster_type.upper()}<br>
                    <strong>Confidence:</strong> {alert.metadata.get('confidence', 0)*100:.1f}%
                </div>
                <p style="color: #6b7280; font-size: 12px; margin-top: 20px;">
                    This is an automated alert from the SDARS Disaster Alert System.
                </p>
            </div>
        </body>
        </html>
        """
    
    def _send_sms_notification(self, alert: Alert):
        """Send SMS notification (mock/Twilio integration)"""
        phone = self.user_preferences['default_user']['phone']
        
        # Abbreviated message for SMS (160 char limit)
        sms_message = f"{alert.severity.value} {alert.disaster_type.upper()} ALERT: {alert.location['name']}. "
        sms_message += f"Confidence: {alert.metadata.get('confidence', 0)*100:.0f}%. "
        sms_message += "Check SDARS app for details."
        
        print(f"📱 [SMS NOTIFICATION - MOCK]")
        print(f"   To: {phone}")
        print(f"   Message: {sms_message}")
        print(f"   (Configure Twilio to enable real SMS)")
    
    def _send_push_notification(self, alert: Alert):
        """Send push notification (mock/Firebase integration)"""
        print(f"🔔 [PUSH NOTIFICATION - MOCK]")
        print(f"   Title: {alert.title}")
        print(f"   Body: {alert.disaster_type.upper()} risk detected in {alert.location['name']}")
        print(f"   (Configure Firebase to enable real push notifications)")
    
    def get_active_alerts(self, severity_filter: Optional[AlertSeverity] = None) -> List[Dict]:
        """Get all active (unacknowledged) alerts"""
        active = [a for a in self.alerts if not a.acknowledged]
        
        if severity_filter:
            active = [a for a in active if a.severity == severity_filter]
        
        return [a.to_dict() for a in active]
    
    def get_alert_history(self, limit: int = 50) -> List[Dict]:
        """Get alert history"""
        all_alerts = self.alerts + self.alert_history
        all_alerts.sort(key=lambda a: a.created_at, reverse=True)
        return [a.to_dict() for a in all_alerts[:limit]]
    
    def acknowledge_alert(self, alert_id: str, user_id: str = "system", email: Optional[str] = None):
        """Acknowledge an alert and return it for background notification processing"""
        for alert in self.alerts:
            if alert.alert_id == alert_id:
                alert.acknowledge(user_id)
                
                # Add the acknowledging user's email to additional recipients for this notification
                if email:
                    if 'additional_recipients' not in alert.metadata:
                        alert.metadata['additional_recipients'] = []
                    
                    if email not in alert.metadata['additional_recipients']:
                        alert.metadata['additional_recipients'].append(email)
                
                # Update title/message to reflect acknowledgment while maintaining "ALERT" context
                alert.title = f"✅ ACKNOWLEDGED: {alert.title}"
                alert.message = f"THIS ALERT HAS BEEN OFFICIALLY ACKNOWLEDGED BY {user_id.upper()}.\n\n--- ORIGINAL MESSAGE ---\n{alert.message}"

                # FORCE Email channel for acknowledgment receipts
                if AlertChannel.EMAIL not in alert.channels:
                    alert.channels.append(AlertChannel.EMAIL)
                    
                # Move to history
                self.alert_history.append(alert)
                self.alerts.remove(alert)
                
                print(f"✅ Alert {alert.alert_id} Acknowledged by {user_id}. Returning for background task.")
                return True, alert
        return False, None
    
    def clear_old_alerts(self, days: int = 30):
        """Clear alerts older than specified days"""
        cutoff = datetime.now() - timedelta(days=days)
        self.alert_history = [a for a in self.alert_history if a.created_at > cutoff]


# Global instance
advanced_alert_system = AdvancedAlertSystem()


# Example usage
if __name__ == "__main__":
    # Mock prediction
    prediction = {
        'location_name': 'Mumbai',
        'latitude': 19.0760,
        'longitude': 72.8777,
        'overall_risk_level': 'HIGH',
        'primary_threat': 'fire',
        'fire': {
            'confidence': 0.85,
            'risk_level': 'HIGH',
            'reasons': [
                'High temperature and low humidity detected',
                'NASA VIIRS: 5 active fire hotspots within 50km',
                'Wind speed favorable for fire spread'
            ]
        },
        'shelters': [
            {'name': 'BKC Emergency Center', 'distance_km': 2.5}
        ]
    }
    
    # Create alert
    alert = advanced_alert_system.create_alert(prediction)
    print(f"\n✅ Alert created: {alert.alert_id}")
    
    # Get active alerts
    active = advanced_alert_system.get_active_alerts()
    print(f"\n📊 Active alerts: {len(active)}")
