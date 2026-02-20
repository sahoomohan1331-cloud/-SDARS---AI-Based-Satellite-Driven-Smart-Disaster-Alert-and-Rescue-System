import json
from datetime import datetime
from typing import List, Dict
import os

class AlertManager:
    """
    Manages automated alerts across multiple channels (SMS, System, Mobile)
    Also matches disaster locations to nearest emergency shelters
    """
    
    def __init__(self):
        # In a real app, these would come from a database
        self.shelters = {
            "Mumbai": [
                {"name": "BKC Emergency Center", "coords": (19.0596, 72.8444), "capacity": 5000},
                {"name": "IIT Bombay Safe Zone", "coords": (19.1334, 72.9133), "capacity": 2000}
            ],
            "Chennai": [
                {"name": "Marina Coastal Shelter", "coords": (13.0418, 80.2850), "capacity": 3000},
                {"name": "Anna University Relief Camp", "coords": (13.0125, 80.2353), "capacity": 1500}
            ],
            # Default fallback for unknown locations
            "Default": [
                {"name": "District Administrative Hub", "coords": (0, 0), "capacity": 1000}
            ]
        }

    def process_prediction(self, prediction: Dict) -> List[Dict]:
        """
        Analyze prediction and trigger necessary alerts
        """
        alerts_triggered = []
        location = prediction.get('location_name', 'Unknown')
        overall_risk = prediction.get('overall_risk_level', 'LOW')
        primary_threat = prediction.get('primary_threat', 'none')
        confidence = prediction.get(primary_threat, {}).get('confidence', 0)

        # 🚨 THRESHOLD 1: SYSTEM ALERT (Medium Risk)
        if confidence >= 0.4:
            alert = {
                "type": "SYSTEM",
                "severity": overall_risk,
                "message": f"SYSTEM ALERT: Potential {primary_threat} risk detected in {location}.",
                "timestamp": datetime.now().isoformat()
            }
            alerts_triggered.append(alert)

        # 🚨 THRESHOLD 2: EMERGENCY SMS (High Risk > 0.7)
        if confidence >= 0.7:
            shelters = self.get_nearest_shelters(location)
            shelter_msg = f"Nearest Shelter: {shelters[0]['name']}" if shelters else ""
            
            sms_alert = {
                "type": "SMS/PUSH",
                "severity": "CRITICAL",
                "message": f"CRITICAL: High {primary_threat} risk in {location}! Evacute to safe zone immediately. {shelter_msg}",
                "timestamp": datetime.now().isoformat()
            }
            alerts_triggered.append(sms_alert)
            self._send_mock_sms(sms_alert)

        return alerts_triggered

    def get_nearest_shelters(self, location_name: str) -> List[Dict]:
        """Return list of shelters for the given location"""
        return self.shelters.get(location_name, self.shelters["Default"])

    def _send_mock_sms(self, alert: Dict):
        """Simulate sending an SMS via Twilio/Firebase"""
        print(f"\n📱 [MOCK SMS SENT] To: Emergency Broadcast Group")
        print(f"   Message: {alert['message']}")
        print(f"   Severity: {alert['severity']}\n")

# Global instance
alert_manager = AlertManager()
