
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Load .env from backend directory
load_dotenv('backend/.env')

def test_smtp():
    server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    port = int(os.getenv('SMTP_PORT', '587'))
    user = os.getenv('SMTP_EMAIL', '')
    password = os.getenv('SMTP_PASSWORD', '')

    print(f"--- SMTP Diagnostic ---")
    print(f"Server: {server}")
    print(f"Port: {port}")
    print(f"User: {user}")
    print(f"Password: {'********' if password else 'MISSING'}")

    if not user or not password:
        print("\n❌ Error: SMTP_EMAIL or SMTP_PASSWORD not set in backend/.env")
        return

    msg = MIMEMultipart()
    msg['Subject'] = "SDARS SMTP Test"
    msg['From'] = user
    msg['To'] = user
    msg.attach(MIMEText("If you see this, your SDARS email configuration is working!", 'plain'))

    try:
        print("\nConnecting to server...")
        with smtplib.SMTP(server, port, timeout=10) as s:
            s.starttls()
            print("Logging in...")
            s.login(user, password)
            print("Sending test email to yourself...")
            s.send_message(msg)
            print("\n✅ SUCCESS: Email sent successfully!")
    except Exception as e:
        print(f"\n❌ FAILURE: {e}")

if __name__ == "__main__":
    test_smtp()
