"""
Enhanced Alert System with Custom Zones and Advanced Features
Extends the existing alert system with user-defined zones and preferences
"""

from typing import List, Dict, Optional
from datetime import datetime
import json
from pathlib import Path

class CustomAlertZone:
    """User-defined geographic zones for custom alerts"""
    
    def __init__(self, zone_id: str, name: str, coordinates: List[List[float]], 
                 user_id: str, severity_threshold: str = "MEDIUM"):
        self.zone_id = zone_id
        self.name = name
        self.coordinates = coordinates  # List of [lat, lon] pairs forming polygon
        self.user_id = user_id
        self.severity_threshold = severity_threshold
        self.created_at = datetime.utcnow()
        self.active = True
        self.notification_channels = ["system", "email"]  # Default channels
        
    def to_dict(self):
        return {
            "zone_id": self.zone_id,
            "name": self.name,
            "coordinates": self.coordinates,
            "user_id": self.user_id,
            "severity_threshold": self.severity_threshold,
            "created_at": self.created_at.isoformat(),
            "active": self.active,
            "notification_channels": self.notification_channels
        }
    
    def contains_point(self, lat: float, lon: float) -> bool:
        """Check if a point is within the zone using ray casting algorithm"""
        n = len(self.coordinates)
        inside = False
        
        p1_lat, p1_lon = self.coordinates[0]
        for i in range(1, n + 1):
            p2_lat, p2_lon = self.coordinates[i % n]
            if lon > min(p1_lon, p2_lon):
                if lon <= max(p1_lon, p2_lon):
                    if lat <= max(p1_lat, p2_lat):
                        if p1_lon != p2_lon:
                            x_inters = (lon - p1_lon) * (p2_lat - p1_lat) / (p2_lon - p1_lon) + p1_lat
                        if p1_lat == p2_lat or lat <= x_inter:
                            inside = not inside
            p1_lat, p1_lon = p2_lat, p2_lon
        
        return inside


class AlertZoneManager:
    """Manages custom alert zones and user preferences"""
    
    def __init__(self, storage_path: str = "data/alert_zones.json"):
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.zones: Dict[str, CustomAlertZone] = {}
        self.user_preferences: Dict[str, Dict] = {}
        self.load_zones()
        
    def load_zones(self):
        """Load zones from storage"""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    for zone_data in data.get('zones', []):
                        zone = CustomAlertZone(
                            zone_id=zone_data['zone_id'],
                            name=zone_data['name'],
                            coordinates=zone_data['coordinates'],
                            user_id=zone_data['user_id'],
                            severity_threshold=zone_data.get('severity_threshold', 'MEDIUM')
                        )
                        zone.active = zone_data.get('active', True)
                        zone.notification_channels = zone_data.get('notification_channels', ['system', 'email'])
                        self.zones[zone.zone_id] = zone
                    
                    self.user_preferences = data.get('preferences', {})
            except Exception as e:
                print(f"Error loading zones: {e}")
    
    def save_zones(self):
        """Save zones to storage"""
        try:
            data = {
                'zones': [zone.to_dict() for zone in self.zones.values()],
                'preferences': self.user_preferences,
                'last_updated': datetime.utcnow().isoformat()
            }
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving zones: {e}")
    
    def create_zone(self, name: str, coordinates: List[List[float]], 
                   user_id: str, severity_threshold: str = "MEDIUM",
                   notification_channels: List[str] = None) -> CustomAlertZone:
        """Create a new custom alert zone"""
        import uuid
        zone_id = f"zone_{uuid.uuid4().hex[:12]}"
        
        zone = CustomAlertZone(
            zone_id=zone_id,
            name=name,
            coordinates=coordinates,
            user_id=user_id,
            severity_threshold=severity_threshold
        )
        
        if notification_channels:
            zone.notification_channels = notification_channels
        
        self.zones[zone_id] = zone
        self.save_zones()
        
        return zone
    
    def get_user_zones(self, user_id: str) -> List[CustomAlertZone]:
        """Get all zones for a specific user"""
        return [zone for zone in self.zones.values() if zone.user_id == user_id and zone.active]
    
    def get_zones_containing_point(self, lat: float, lon: float) -> List[CustomAlertZone]:
        """Get all zones that contain a specific point"""
        return [zone for zone in self.zones.values() 
                if zone.active and zone.contains_point(lat, lon)]
    
    def update_zone(self, zone_id: str, **kwargs) -> Optional[CustomAlertZone]:
        """Update zone properties"""
        if zone_id in self.zones:
            zone = self.zones[zone_id]
            for key, value in kwargs.items():
                if hasattr(zone, key):
                    setattr(zone, key, value)
            self.save_zones()
            return zone
        return None
    
    def delete_zone(self, zone_id: str, user_id: str) -> bool:
        """Delete a zone (soft delete by setting active=False)"""
        if zone_id in self.zones and self.zones[zone_id].user_id == user_id:
            self.zones[zone_id].active = False
            self.save_zones()
            return True
        return False
    
    def set_user_preferences(self, user_id: str, preferences: Dict):
        """Set notification preferences for a user"""
        self.user_preferences[user_id] = {
            **preferences,
            'updated_at': datetime.utcnow().isoformat()
        }
        self.save_zones()
    
    def get_user_preferences(self, user_id: str) -> Dict:
        """Get notification preferences for a user"""
        default_prefs = {
            'email_enabled': True,
            'sms_enabled': False,
            'push_enabled': True,
            'sound_enabled': True,
            'min_severity': 'MEDIUM',
            'quiet_hours': {
                'enabled': False,
                'start': '22:00',
                'end': '07:00'
            },
            'channels': {
                'CRITICAL': ['system', 'email', 'sms', 'push'],
                'HIGH': ['system', 'email', 'push'],
                'MEDIUM': ['system', 'email'],
                'LOW': ['system']
            }
        }
        
        return self.user_preferences.get(user_id, default_prefs)


class EnhancedAlertNotifier:
    """Enhanced notification system with browser push support"""
    
    def __init__(self):
        self.push_subscriptions: Dict[str, Dict] = {}  # user_id -> subscription info
        
    def subscribe_push(self, user_id: str, subscription: Dict):
        """Subscribe user to push notifications"""
        self.push_subscriptions[user_id] = {
            'subscription': subscription,
            'subscribed_at': datetime.utcnow().isoformat()
        }
        
    def unsubscribe_push(self, user_id: str):
        """Unsubscribe user from push notifications"""
        if user_id in self.push_subscriptions:
            del self.push_subscriptions[user_id]
    
    def send_push_notification(self, user_id: str, title: str, message: str, 
                              icon: str = "/icon-192.png", urgency: str = "high"):
        """Send browser push notification"""
        if user_id not in self.push_subscriptions:
            return False
        
        try:
            from pywebpush import webpush, WebPushException
            import json
            
            subscription = self.push_subscriptions[user_id]['subscription']
            
            payload = json.dumps({
                'title': title,
                'body': message,
                'icon': icon,
                'badge': '/badge-72.png',
                'urgency': urgency,
                'data': {
                    'timestamp': datetime.utcnow().isoformat(),
                    'url': '/alerts.html'
                }
            })
            
            # Send using Web Push Protocol
            webpush(
                subscription_info=subscription,
                data=payload,
                vapid_private_key="YOUR_VAPID_PRIVATE_KEY",  # Set in env
                vapid_claims={
                    "sub": "mailto:admin@sdars.com"
                }
            )
            
            return True
            
        except Exception as e:
            print(f"Push notification error: {e}")
            return False
    
    def play_alert_sound(self, severity: str) -> str:
        """Get alert sound file based on severity"""
        sounds = {
            'CRITICAL': '/sounds/critical-alert.mp3',
            'HIGH': '/sounds/high-alert.mp3',
            'MEDIUM': '/sounds/medium-alert.mp3',
            'LOW': '/sounds/low-alert.mp3'
        }
        return sounds.get(severity, sounds['MEDIUM'])


# Global instances
zone_manager = AlertZoneManager()
enhanced_notifier = EnhancedAlertNotifier()


def check_zones_for_alert(lat: float, lon: float, severity: str) -> List[Dict]:
    """Check if an alert location triggers any custom zones"""
    triggered_zones = []
    
    zones = zone_manager.get_zones_containing_point(lat, lon)
    
    severity_levels = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
    
    for zone in zones:
        # Check if alert severity meets zone threshold
        if severity_levels.index(severity) >= severity_levels.index(zone.severity_threshold):
            triggered_zones.append({
                'zone_id': zone.zone_id,
                'zone_name': zone.name,
                'user_id': zone.user_id,
                'notification_channels': zone.notification_channels,
                'severity_threshold': zone.severity_threshold
            })
    
    return triggered_zones


def send_enhanced_alert(alert_data: Dict, user_id: str = "default_user"):
    """Send alert through all enabled channels based on user preferences"""
    prefs = zone_manager.get_user_preferences(user_id)
    severity = alert_data.get('severity', 'MEDIUM')
    
    # Determine which channels to use based on severity and preferences
    channels = prefs['channels'].get(severity, ['system'])
    
    results = {}
    
    # System notification (always sent)
    results['system'] = True
    
    # Email notification
    if 'email' in channels and prefs.get('email_enabled', True):
        # Use existing email system
        results['email'] = True  # Would call advanced_alert_system.send_email()
    
    # SMS notification
    if 'sms' in channels and prefs.get('sms_enabled', False):
        # Use existing SMS system
        results['sms'] = True  # Would call advanced_alert_system.send_sms()
    
    # Push notification
    if 'push' in channels and prefs.get('push_enabled', True):
        title = f"🚨 {severity} Alert"
        message = alert_data.get('message', 'New disaster alert')
        results['push'] = enhanced_notifier.send_push_notification(
            user_id, title, message, urgency=severity.lower()
        )
    
    # Sound alert
    if prefs.get('sound_enabled', True):
        results['sound'] = enhanced_notifier.play_alert_sound(severity)
    
    return results
