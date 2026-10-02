"""
SDARS API Key Validator
Tests all configured API keys to check which are working
"""
import requests
import os
import sys
from dotenv import load_dotenv
import smtplib

# Configure UTF-8 encoding for standard output on Windows
if sys.platform == 'win32':
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')

# Load .env from backend
load_dotenv(os.path.join(os.path.dirname(__file__), 'backend', '.env'))

def test_openweather():
    """Test OpenWeatherMap API key"""
    key = os.getenv('OPENWEATHER_API_KEY', '')
    print(f"\n{'='*60}")
    print(f"1. OPENWEATHER API KEY: {key[:8]}...{key[-4:]}")
    print(f"{'='*60}")
    
    if not key:
        print("   ❌ MISSING - No API key configured")
        return False
    
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?lat=19.07&lon=72.87&appid={key}&units=metric"
        r = requests.get(url, timeout=10)
        data = r.json()
        
        if r.status_code == 200:
            print(f"   ✅ WORKING - Status: {r.status_code}")
            print(f"   📍 Test: Mumbai → Temp: {data['main']['temp']}°C, {data['weather'][0]['description']}")
            return True
        elif r.status_code == 401:
            print(f"   ❌ INVALID KEY - {data.get('message', 'Unauthorized')}")
            return False
        else:
            print(f"   ⚠️ ERROR - Status: {r.status_code}, Message: {data.get('message', 'Unknown')}")
            return False
    except Exception as e:
        print(f"   ❌ CONNECTION ERROR - {e}")
        return False

def test_nasa():
    """Test NASA API key"""
    key = os.getenv('NASA_API_KEY', '')
    print(f"\n{'='*60}")
    print(f"2. NASA API KEY: {key[:8]}...{key[-4:]}")
    print(f"{'='*60}")
    
    if not key:
        print("   ❌ MISSING - No API key configured")
        return False
    
    try:
        # Test with APOD (Astronomy Picture of the Day) - simple endpoint
        url = f"https://api.nasa.gov/planetary/apod?api_key={key}"
        r = requests.get(url, timeout=10)
        data = r.json()
        
        if r.status_code == 200:
            print(f"   ✅ WORKING - Status: {r.status_code}")
            print(f"   🛰️ Test: APOD → Title: {data.get('title', 'N/A')}")
            return True
        elif r.status_code == 403:
            print(f"   ❌ INVALID/EXPIRED KEY - {data.get('error', {}).get('message', 'Forbidden')}")
            return False
        else:
            print(f"   ⚠️ ERROR - Status: {r.status_code}, Message: {data}")
            return False
    except Exception as e:
        print(f"   ❌ CONNECTION ERROR - {e}")
        return False

def test_sentinel_hub():
    """Test Planet Insights Platform / Sentinel Hub credentials"""
    planet_key = os.getenv('PLANET_API_KEY', '')
    client_id = os.getenv('SENTINEL_HUB_CLIENT_ID', '')
    client_secret = os.getenv('SENTINEL_HUB_CLIENT_SECRET', '')
    
    print(f"\n{'='*60}")
    print(f"3. PLANET INSIGHTS / SENTINEL HUB")
    if planet_key:
        print(f"   PLANET API KEY: {planet_key[:8]}...{planet_key[-4:]}")
    if client_id:
        print(f"   SENTINEL CLIENT ID: {client_id[:8]}...{client_id[-4:]}")
    print(f"{'='*60}")
    
    # 1. Test Planet Insights API Key first
    if planet_key:
        try:
            url = "https://api.planet.com/basemaps/v1/mosaics"
            r = requests.get(url, auth=(planet_key, ''), timeout=10)
            if r.status_code == 200:
                print(f"   ✅ WORKING - Planet Insights Platform API Key verified! Status: {r.status_code}")
                return True
            else:
                print(f"   ⚠️ Planet Key returned status {r.status_code}")
        except Exception as e:
            print(f"   ⚠️ Planet Key test error: {e}")
            
    # 2. Test Sentinel Hub OAuth client credentials
    if client_id and client_secret:
        try:
            url = "https://services.sentinel-hub.com/oauth/token"
            r = requests.post(url, data={
                'grant_type': 'client_credentials',
                'client_id': client_id,
                'client_secret': client_secret
            }, timeout=10)
            if r.status_code == 200:
                token = r.json().get('access_token', '')
                print(f"   ✅ WORKING - Sentinel Hub OAuth token: {token[:20]}...")
                return True
            else:
                print(f"   ❌ OAuth Status: {r.status_code}")
        except Exception as e:
            print(f"   ❌ OAuth connection error: {e}")

    if not planet_key and not (client_id and client_secret):
        print("   ❌ MISSING - No Planet or Sentinel Hub credentials configured")
    return False

def test_smtp():
    """Test SMTP email credentials"""
    server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    port = int(os.getenv('SMTP_PORT', 587))
    email = os.getenv('SMTP_EMAIL', '')
    password = os.getenv('SMTP_PASSWORD', '')
    print(f"\n{'='*60}")
    print(f"4. SMTP EMAIL: {email}")
    print(f"   SMTP SERVER: {server}:{port}")
    print(f"   SMTP PASSWORD: {'*' * len(password) if password else 'MISSING'}")
    print(f"{'='*60}")
    
    if not email or not password:
        print("   ❌ MISSING - Email credentials not configured")
        return False
    
    try:
        smtp = smtplib.SMTP(server, port, timeout=10)
        smtp.starttls()
        smtp.login(email, password)
        smtp.quit()
        print(f"   ✅ WORKING - SMTP login successful!")
        return True
    except smtplib.SMTPAuthenticationError as e:
        print(f"   ❌ AUTH FAILED - {e}")
        return False
    except Exception as e:
        print(f"   ❌ CONNECTION ERROR - {e}")
        return False

def test_twilio():
    """Test Twilio credentials"""
    sid = os.getenv('TWILIO_ACCOUNT_SID', '')
    token = os.getenv('TWILIO_AUTH_TOKEN', '')
    phone = os.getenv('TWILIO_PHONE_NUMBER', '')
    print(f"\n{'='*60}")
    print(f"5. TWILIO ACCOUNT SID: {sid}")
    print(f"   TWILIO PHONE: {phone}")
    print(f"{'='*60}")
    
    if 'your_' in sid or not sid:
        print("   ⚠️ NOT CONFIGURED - Using placeholder values")
        return None  # Not configured, not an error
    
    try:
        url = f"https://api.twilio.com/2010-04-01/Accounts/{sid}.json"
        r = requests.get(url, auth=(sid, token), timeout=10)
        
        if r.status_code == 200:
            print(f"   ✅ WORKING - Account verified")
            return True
        else:
            print(f"   ❌ INVALID - Status: {r.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ CONNECTION ERROR - {e}")
        return False

def test_telegram():
    """Test Telegram Bot credentials"""
    token = os.getenv('TELEGRAM_BOT_TOKEN', '')
    chat_id = os.getenv('TELEGRAM_CHAT_ID', '')
    print(f"\n{'='*60}")
    print(f"6. TELEGRAM BOT TOKEN: {token}")
    print(f"   TELEGRAM CHAT ID: {chat_id}")
    print(f"{'='*60}")
    
    if 'your_' in token or not token:
        print("   ⚠️ NOT CONFIGURED - Using placeholder values")
        return None
    
    try:
        url = f"https://api.telegram.org/bot{token}/getMe"
        r = requests.get(url, timeout=10)
        
        if r.status_code == 200:
            bot_info = r.json().get('result', {})
            print(f"   ✅ WORKING - Bot: @{bot_info.get('username', 'unknown')}")
            return True
        else:
            print(f"   ❌ INVALID TOKEN - {r.json().get('description', 'Unknown error')}")
            return False
    except Exception as e:
        print(f"   ❌ CONNECTION ERROR - {e}")
        return False

def test_open_meteo():
    """Test Open-Meteo API (primary weather source - FREE, no key needed)"""
    print(f"\n{'='*60}")
    print(f"7. OPEN-METEO API (FREE - No Key Required)")
    print(f"{'='*60}")
    
    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": 19.076,
            "longitude": 72.877,
            "current": ["temperature_2m", "wind_speed_10m"],
            "timezone": "auto"
        }
        r = requests.get(url, params=params, timeout=10)
        
        if r.status_code == 200:
            data = r.json()
            temp = data['current']['temperature_2m']
            wind = data['current']['wind_speed_10m']
            print(f"   ✅ WORKING - Mumbai: {temp}°C, Wind: {wind} km/h")
            return True
        else:
            print(f"   ❌ ERROR - Status: {r.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ CONNECTION ERROR - {e}")
        return False

def test_nasa_eonet():
    """Test NASA EONET API (FREE - No Key Required)"""
    print(f"\n{'='*60}")
    print(f"8. NASA EONET API (FREE - No Key Required)")
    print(f"{'='*60}")
    
    try:
        url = "https://eonet.gsfc.nasa.gov/api/v3/events?limit=3&status=open"
        r = requests.get(url, timeout=10)
        
        if r.status_code == 200:
            data = r.json()
            events = data.get('events', [])
            print(f"   ✅ WORKING - Active events: {len(events)}")
            for ev in events[:3]:
                print(f"      🌍 {ev.get('title', 'Unknown')}")
            return True
        else:
            print(f"   ❌ ERROR - Status: {r.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ CONNECTION ERROR - {e}")
        return False


if __name__ == "__main__":
    print("\n" + "🔑" * 30)
    print("  SDARS API KEY VALIDATION REPORT")
    print("🔑" * 30)
    
    results = {}
    results['OpenWeatherMap'] = test_openweather()
    results['NASA'] = test_nasa()
    results['Sentinel Hub'] = test_sentinel_hub()
    results['SMTP Email'] = test_smtp()
    results['Twilio'] = test_twilio()
    results['Telegram'] = test_telegram()
    results['Open-Meteo'] = test_open_meteo()
    results['NASA EONET'] = test_nasa_eonet()
    
    print(f"\n\n{'='*60}")
    print(f"  📊 SUMMARY")
    print(f"{'='*60}")
    
    for name, status in results.items():
        if status is True:
            icon = "✅"
            label = "WORKING"
        elif status is False:
            icon = "❌"
            label = "BROKEN"
        else:
            icon = "⚠️"
            label = "NOT CONFIGURED (Optional)"
        print(f"  {icon} {name}: {label}")
    
    broken = [k for k, v in results.items() if v is False]
    if broken:
        print(f"\n  ⚠️ {len(broken)} API(s) need attention: {', '.join(broken)}")
    else:
        print(f"\n  🎉 All configured APIs are working!")
