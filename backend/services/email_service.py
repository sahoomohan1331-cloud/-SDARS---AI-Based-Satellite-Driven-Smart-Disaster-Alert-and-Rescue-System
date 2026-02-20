
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import random
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmailService:
    @staticmethod
    def _get_smtp_config():
        """Retrieve SMTP settings from environment variables."""
        return {
            'server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
            'port': int(os.getenv('SMTP_PORT', '587')),
            'user': os.getenv('SMTP_USER', ''),
            'password': os.getenv('SMTP_PASSWORD', ''),
            'from_email': os.getenv('SMTP_USER', '')
        }

    @staticmethod
    def send_otp(to_email: str) -> dict:
        """
        Generates and sends an OTP to the specified email.
        Returns the OTP code and its expiry time.
        """
        config = EmailService._get_smtp_config()
        if not config['user'] or not config['password']:
            logger.warning("SMTP credentials not configured. Using MOCK OTP.")
            # Mock OTP for development if credentials missing
            return {
                'otp': '123456',
                'expiry': datetime.utcnow() + timedelta(minutes=10)
            }

        otp = f"{random.randint(100000, 999999)}"
        expiry = datetime.utcnow() + timedelta(minutes=10)

        subject = "🔐 Your SDARS Login Code"
        text_body = f"Your verification code is: {otp}\nIt expires in 10 minutes."
        html_body = f"""
        <div style="font-family: Arial, sans-serif; padding: 20px; border: 1px solid #ddd; max-width: 400px; border-radius: 8px;">
            <h2 style="color: #6366f1;">SDARS Verification</h2>
            <p>Use the following code to log in:</p>
            <h1 style="background: #f3f4f6; padding: 10px; text-align: center; letter-spacing: 5px; color: #1f2937;">{otp}</h1>
            <p style="color: #6b7280; font-size: 12px;">This code expires in 10 minutes.</p>
        </div>
        """

        try:
            EmailService._send_email(to_email, subject, text_body, html_body)
            return {'otp': otp, 'expiry': expiry}
        except Exception as e:
            logger.error(f"Failed to send OTP: {e}")
            raise e

    @staticmethod
    def send_alert(to_email: str, zone_name: str, risk_level: str, details: str):
        """Sends a disaster alert email."""
        subject = f"⚠️ ALERT: {risk_level} Risk in {zone_name}"
        
        color = "#ef4444" if risk_level == "HIGH" else "#f59e0b"
        
        html_body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; border: 1px solid #ddd; border-top: 5px solid {color}; border-radius: 8px;">
            <div style="padding: 20px;">
                <h2 style="color: {color}; margin-top: 0;">{risk_level} Priority Alert</h2>
                <h3 style="margin: 0;">Location: {zone_name}</h3>
                <p>{details}</p>
                <a href="#" style="background: {color}; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block; margin-top: 10px;">View Full Report</a>
            </div>
            <div style="background: #f9fafb; padding: 10px 20px; font-size: 12px; color: #6b7280;">
                Specific Disaster Alert & Response System (SDARS)
            </div>
        </div>
        """
        
        EmailService._send_email(to_email, subject, details, html_body)

    @staticmethod
    def _send_email(to_email, subject, text_body, html_body):
        config = EmailService._get_smtp_config()
        
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = config['from_email']
        msg['To'] = to_email

        msg.attach(MIMEText(text_body, 'plain'))
        msg.attach(MIMEText(html_body, 'html'))

        with smtplib.SMTP(config['server'], config['port']) as server:
            server.starttls()
            server.login(config['user'], config['password'])
            server.send_message(msg)
            logger.info(f"Email sent to {to_email}")
