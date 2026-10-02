"""
Real Geocoding Service for SDARS
Combines:
1. Multi-format coordinate parsing (e.g. "20 17591, 85 62055" or "20.17591, 85.62055")
2. Built-in Local & National Gazetteer (Cuttack, Bhubaneswar, Odisha districts, Indian metros, global hubs)
3. Smart Fuzzy Token Matching (handles typos, spaces, local aliases like Chauliaganj, Badambadi, Patia)
4. Multi-tier Online Fallback (Open-Meteo Geocoding & OpenStreetMap Nominatim with context hints)
"""
import requests
import re
import difflib
import time
from typing import Optional, Dict, List

# Comprehensive Pre-Indexed Registry of Localities, Districts, and Metros
SDARS_GAZETTEER = {
    # --- CUTTACK LOCALITIES & LANDMARKS ---
    "chauliaganj": {"lat": 20.4584, "lon": 85.9091, "display_name": "Chauliaganj, Cuttack, Odisha, India"},
    "chauliahata": {"lat": 20.4610, "lon": 85.9045, "display_name": "Chauliahata, Cuttack, Odisha, India"},
    "badambadi": {"lat": 20.4530, "lon": 85.8670, "display_name": "Badambadi Bus Terminal, Cuttack, Odisha, India"},
    "ranihat": {"lat": 20.4680, "lon": 85.8810, "display_name": "Ranihat, Cuttack, Odisha, India"},
    "college square": {"lat": 20.4625, "lon": 85.8920, "display_name": "College Square, Cuttack, Odisha, India"},
    "manglabag": {"lat": 20.4695, "lon": 85.8870, "display_name": "Manglabag, Cuttack, Odisha, India"},
    "scb medical": {"lat": 20.4690, "lon": 85.8880, "display_name": "SCB Medical College & Hospital, Cuttack, Odisha, India"},
    "scb": {"lat": 20.4690, "lon": 85.8880, "display_name": "SCB Medical College, Cuttack, Odisha, India"},
    "jobra": {"lat": 20.4720, "lon": 85.8990, "display_name": "Jobra Barrage, Cuttack, Odisha, India"},
    "madhupatna": {"lat": 20.4480, "lon": 85.8920, "display_name": "Madhupatna, Cuttack, Odisha, India"},
    "link road": {"lat": 20.4450, "lon": 85.8780, "display_name": "Link Road, Cuttack, Odisha, India"},
    "cda": {"lat": 20.4750, "lon": 85.8350, "display_name": "CDA (Cuttack Development Area), Cuttack, Odisha, India"},
    "cda sector": {"lat": 20.4750, "lon": 85.8350, "display_name": "CDA Sector, Cuttack, Odisha, India"},
    "choudwar": {"lat": 20.5280, "lon": 85.9080, "display_name": "Choudwar, Cuttack, Odisha, India"},
    "jagatpur": {"lat": 20.4980, "lon": 85.9250, "display_name": "Jagatpur Industrial Area, Cuttack, Odisha, India"},
    "bidanasi": {"lat": 20.4760, "lon": 85.8230, "display_name": "Bidanasi, Cuttack, Odisha, India"},
    "cantonment": {"lat": 20.4710, "lon": 85.8650, "display_name": "Cantonment Road, Cuttack, Odisha, India"},
    "barabati stadium": {"lat": 20.4810, "lon": 85.8690, "display_name": "Barabati Stadium, Cuttack, Odisha, India"},
    "high court": {"lat": 20.4760, "lon": 85.8610, "display_name": "Orissa High Court, Cuttack, Odisha, India"},
    "mahanadi vihar": {"lat": 20.4780, "lon": 85.9180, "display_name": "Mahanadi Vihar, Cuttack, Odisha, India"},
    "sikharpur": {"lat": 20.4710, "lon": 85.9220, "display_name": "Sikharpur, Cuttack, Odisha, India"},
    "khannagar": {"lat": 20.4430, "lon": 85.8710, "display_name": "Khannagar, Cuttack, Odisha, India"},
    "nayabazar": {"lat": 20.4650, "lon": 85.9230, "display_name": "Nayabazar, Cuttack, Odisha, India"},
    "malgodown": {"lat": 20.4590, "lon": 85.8980, "display_name": "Malgodown, Cuttack, Odisha, India"},
    "cuttack railway station": {"lat": 20.4620, "lon": 85.8930, "display_name": "Cuttack Railway Station, Odisha, India"},
    "ravenshaw": {"lat": 20.4635, "lon": 85.8950, "display_name": "Ravenshaw University, Cuttack, Odisha, India"},
    "cuttack": {"lat": 20.4625, "lon": 85.8828, "display_name": "Cuttack, Odisha, India"},

    # --- BHUBANESWAR LOCALITIES & LANDMARKS ---
    "patia": {"lat": 20.3540, "lon": 85.8180, "display_name": "Patia, Bhubaneswar, Odisha, India"},
    "kiit": {"lat": 20.3533, "lon": 85.8178, "display_name": "KIIT University, Bhubaneswar, Odisha, India"},
    "nayapalli": {"lat": 20.2980, "lon": 85.8120, "display_name": "Nayapalli, Bhubaneswar, Odisha, India"},
    "jaydev vihar": {"lat": 20.3020, "lon": 85.8240, "display_name": "Jaydev Vihar, Bhubaneswar, Odisha, India"},
    "saheed nagar": {"lat": 20.2910, "lon": 85.8450, "display_name": "Saheed Nagar, Bhubaneswar, Odisha, India"},
    "acharya vihar": {"lat": 20.3010, "lon": 85.8320, "display_name": "Acharya Vihar, Bhubaneswar, Odisha, India"},
    "vani vihar": {"lat": 20.3030, "lon": 85.8420, "display_name": "Vani Vihar (Utkal University), Bhubaneswar, Odisha, India"},
    "rasulgarh": {"lat": 20.2980, "lon": 85.8640, "display_name": "Rasulgarh, Bhubaneswar, Odisha, India"},
    "chandrasekharpur": {"lat": 20.3250, "lon": 85.8190, "display_name": "Chandrasekharpur, Bhubaneswar, Odisha, India"},
    "cspur": {"lat": 20.3250, "lon": 85.8190, "display_name": "Chandrasekharpur, Bhubaneswar, Odisha, India"},
    "khandagiri": {"lat": 20.2580, "lon": 85.7760, "display_name": "Khandagiri, Bhubaneswar, Odisha, India"},
    "udayagiri": {"lat": 20.2620, "lon": 85.7820, "display_name": "Udayagiri, Bhubaneswar, Odisha, India"},
    "baramunda": {"lat": 20.2780, "lon": 85.7980, "display_name": "Baramunda ISBT, Bhubaneswar, Odisha, India"},
    "master canteen": {"lat": 20.2680, "lon": 85.8410, "display_name": "Master Canteen, Bhubaneswar, Odisha, India"},
    "bhubaneswar railway station": {"lat": 20.2660, "lon": 85.8430, "display_name": "Bhubaneswar Railway Station, Odisha, India"},
    "bhubaneswar airport": {"lat": 20.2520, "lon": 85.8170, "display_name": "Biju Patnaik International Airport (BBI), Bhubaneswar, Odisha, India"},
    "biju patnaik airport": {"lat": 20.2520, "lon": 85.8170, "display_name": "Biju Patnaik International Airport (BBI), Bhubaneswar, Odisha, India"},
    "kalpana square": {"lat": 20.2560, "lon": 85.8390, "display_name": "Kalpana Square, Bhubaneswar, Odisha, India"},
    "samantarapur": {"lat": 20.2350, "lon": 85.8420, "display_name": "Samantarapur, Bhubaneswar, Odisha, India"},
    "old town": {"lat": 20.2410, "lon": 85.8340, "display_name": "Old Town, Bhubaneswar, Odisha, India"},
    "lingaraj temple": {"lat": 20.2380, "lon": 85.8330, "display_name": "Lingaraj Temple, Bhubaneswar, Odisha, India"},
    "dhauli": {"lat": 20.1920, "lon": 85.8390, "display_name": "Dhauli Shanti Stupa, Bhubaneswar, Odisha, India"},
    "aiims": {"lat": 20.2310, "lon": 85.7780, "display_name": "AIIMS Bhubaneswar, Sijua, Odisha, India"},
    "aiims bhubaneswar": {"lat": 20.2310, "lon": 85.7780, "display_name": "AIIMS Bhubaneswar, Sijua, Odisha, India"},
    "iter": {"lat": 20.2510, "lon": 85.7960, "display_name": "ITER / SOA University, Bhubaneswar, Odisha, India"},
    "soa university": {"lat": 20.2510, "lon": 85.7960, "display_name": "Siksha 'O' Anusandhan (SOA), Bhubaneswar, Odisha, India"},
    "silicon": {"lat": 20.3590, "lon": 85.8070, "display_name": "Silicon University, Bhubaneswar, Odisha, India"},
    "infocity": {"lat": 20.3580, "lon": 85.8130, "display_name": "Infocity, Bhubaneswar, Odisha, India"},
    "kalinga nagar": {"lat": 20.2460, "lon": 85.7510, "display_name": "Kalinga Nagar, Bhubaneswar, Odisha, India"},
    "tamando": {"lat": 20.2310, "lon": 85.7420, "display_name": "Tamando, Bhubaneswar, Odisha, India"},
    "jatni": {"lat": 20.1650, "lon": 85.7060, "display_name": "Jatni, Khurda, Odisha, India"},
    "iit bhubaneswar": {"lat": 20.1480, "lon": 85.6710, "display_name": "IIT Bhubaneswar, Argul, Odisha, India"},
    "khurda": {"lat": 20.1880, "lon": 85.6210, "display_name": "Khurda, Odisha, India"},
    "khurda road": {"lat": 20.1650, "lon": 85.7110, "display_name": "Khurda Road Junction, Odisha, India"},
    "bhubaneswar": {"lat": 20.2961, "lon": 85.8245, "display_name": "Bhubaneswar, Odisha, India"},
    "bbsr": {"lat": 20.2961, "lon": 85.8245, "display_name": "Bhubaneswar, Odisha, India"},
    "bhuban": {"lat": 20.2961, "lon": 85.8245, "display_name": "Bhubaneswar, Odisha, India"},

    # --- ODISHA DISTRICT HEADQUARTERS & COASTAL DISASTER HUBS ---
    "puri": {"lat": 19.8135, "lon": 85.8312, "display_name": "Puri, Odisha, India"},
    "pipili": {"lat": 20.1130, "lon": 85.8310, "display_name": "Pipili, Puri, Odisha, India"},
    "konark": {"lat": 19.8876, "lon": 86.0945, "display_name": "Konark Sun Temple, Odisha, India"},
    "nimapada": {"lat": 20.0630, "lon": 86.0150, "display_name": "Nimapada, Puri, Odisha, India"},
    "astaranga": {"lat": 19.9820, "lon": 86.2710, "display_name": "Astaranga Coastal Belt, Odisha, India"},
    "paradeep": {"lat": 20.3164, "lon": 86.6114, "display_name": "Paradeep Port, Jagatsinghpur, Odisha, India"},
    "jagatsinghpur": {"lat": 20.2680, "lon": 86.1680, "display_name": "Jagatsinghpur, Odisha, India"},
    "kendrapara": {"lat": 20.5020, "lon": 86.4220, "display_name": "Kendrapara, Odisha, India"},
    "pattamundai": {"lat": 20.5740, "lon": 86.5680, "display_name": "Pattamundai, Kendrapara, Odisha, India"},
    "dhamra": {"lat": 20.7950, "lon": 86.9740, "display_name": "Dhamra Port, Bhadrak, Odisha, India"},
    "chandbali": {"lat": 20.7740, "lon": 86.7450, "display_name": "Chandbali, Bhadrak, Odisha, India"},
    "bhadrak": {"lat": 21.0570, "lon": 86.4950, "display_name": "Bhadrak, Odisha, India"},
    "balasore": {"lat": 21.4934, "lon": 86.9135, "display_name": "Balasore, Odisha, India"},
    "chandipur": {"lat": 21.4720, "lon": 87.0140, "display_name": "Chandipur Coast, Balasore, Odisha, India"},
    "jaleswar": {"lat": 21.8020, "lon": 87.2150, "display_name": "Jaleswar, Balasore, Odisha, India"},
    "baripada": {"lat": 21.9320, "lon": 86.7320, "display_name": "Baripada, Mayurbhanj, Odisha, India"},
    "mayurbhanj": {"lat": 21.9300, "lon": 86.7300, "display_name": "Mayurbhanj, Odisha, India"},
    "jajpur": {"lat": 20.8520, "lon": 86.3310, "display_name": "Jajpur, Odisha, India"},
    "keonjhar": {"lat": 21.6280, "lon": 85.5820, "display_name": "Kendujhar (Keonjhar), Odisha, India"},
    "dhenkanal": {"lat": 20.6620, "lon": 85.5980, "display_name": "Dhenkanal, Odisha, India"},
    "angul": {"lat": 20.8400, "lon": 85.1010, "display_name": "Angul, Odisha, India"},
    "talcher": {"lat": 20.9500, "lon": 85.2200, "display_name": "Talcher Coalfields, Angul, Odisha, India"},
    "sambalpur": {"lat": 21.4669, "lon": 83.9812, "display_name": "Sambalpur, Odisha, India"},
    "burla": {"lat": 21.5030, "lon": 83.8720, "display_name": "Burla (Hirakud Dam), Sambalpur, Odisha, India"},
    "hirakud": {"lat": 21.5200, "lon": 83.8700, "display_name": "Hirakud Dam, Sambalpur, Odisha, India"},
    "bargarh": {"lat": 21.3340, "lon": 83.6210, "display_name": "Bargarh, Odisha, India"},
    "jharsuguda": {"lat": 21.8550, "lon": 84.0080, "display_name": "Jharsuguda, Odisha, India"},
    "rourkela": {"lat": 22.2604, "lon": 84.8536, "display_name": "Rourkela Steel City, Sundargarh, Odisha, India"},
    "sundargarh": {"lat": 22.1220, "lon": 84.0320, "display_name": "Sundargarh, Odisha, India"},
    "bolangir": {"lat": 20.7100, "lon": 83.4860, "display_name": "Balangir (Bolangir), Odisha, India"},
    "subarnapur": {"lat": 20.8400, "lon": 83.9180, "display_name": "Subarnapur (Sonepur), Odisha, India"},
    "sonepur": {"lat": 20.8400, "lon": 83.9180, "display_name": "Sonepur, Odisha, India"},
    "nuapada": {"lat": 20.8350, "lon": 82.5280, "display_name": "Nuapada, Odisha, India"},
    "kalahandi": {"lat": 19.9070, "lon": 83.1760, "display_name": "Bhawanipatna, Kalahandi, Odisha, India"},
    "bhawanipatna": {"lat": 19.9070, "lon": 83.1760, "display_name": "Bhawanipatna, Kalahandi, Odisha, India"},
    "berhampur": {"lat": 19.3149, "lon": 84.7941, "display_name": "Berhampur (Brahmapur), Ganjam, Odisha, India"},
    "gopalpur": {"lat": 19.2610, "lon": 84.9080, "display_name": "Gopalpur-on-Sea, Ganjam, Odisha, India"},
    "chhatrapur": {"lat": 19.3550, "lon": 84.9870, "display_name": "Chhatrapur, Ganjam, Odisha, India"},
    "ganjam": {"lat": 19.3800, "lon": 85.0600, "display_name": "Ganjam Coastal District, Odisha, India"},
    "koraput": {"lat": 18.8130, "lon": 82.7120, "display_name": "Koraput, Odisha, India"},
    "jeypore": {"lat": 18.8560, "lon": 82.5680, "display_name": "Jeypore, Koraput, Odisha, India"},
    "rayagada": {"lat": 19.1710, "lon": 83.4160, "display_name": "Rayagada, Odisha, India"},
    "nabarangpur": {"lat": 19.2310, "lon": 82.5510, "display_name": "Nabarangpur, Odisha, India"},
    "malkangiri": {"lat": 18.3430, "lon": 81.8950, "display_name": "Malkangiri, Odisha, India"},
    "gajapati": {"lat": 18.7760, "lon": 84.0920, "display_name": "Paralakhemundi, Gajapati, Odisha, India"},
    "paralakhemundi": {"lat": 18.7760, "lon": 84.0920, "display_name": "Paralakhemundi, Gajapati, Odisha, India"},
    "kandhamal": {"lat": 20.4760, "lon": 84.2330, "display_name": "Phulbani, Kandhamal, Odisha, India"},
    "phulbani": {"lat": 20.4760, "lon": 84.2330, "display_name": "Phulbani, Kandhamal, Odisha, India"},
    "boudh": {"lat": 20.8380, "lon": 84.3260, "display_name": "Boudh, Odisha, India"},
    "deogarh": {"lat": 21.5360, "lon": 84.7320, "display_name": "Deogarh (Debagarh), Odisha, India"},
    "nayagarh": {"lat": 20.1260, "lon": 85.1060, "display_name": "Nayagarh, Odisha, India"},
    "dasapalla": {"lat": 20.3450, "lon": 84.8510, "display_name": "Dasapalla, Nayagarh, Odisha, India"},

    # --- MAJOR INDIAN METROPOLITAN & DISASTER VULNERABLE HUBS ---
    "delhi": {"lat": 28.6139, "lon": 77.2090, "display_name": "New Delhi, Delhi, India"},
    "new delhi": {"lat": 28.6139, "lon": 77.2090, "display_name": "New Delhi, Delhi, India"},
    "mumbai": {"lat": 19.0760, "lon": 72.8777, "display_name": "Mumbai, Maharashtra, India"},
    "kolkata": {"lat": 22.5726, "lon": 88.3639, "display_name": "Kolkata, West Bengal, India"},
    "chennai": {"lat": 13.0827, "lon": 80.2707, "display_name": "Chennai, Tamil Nadu, India"},
    "bangalore": {"lat": 12.9716, "lon": 77.5946, "display_name": "Bengaluru, Karnataka, India"},
    "bengaluru": {"lat": 12.9716, "lon": 77.5946, "display_name": "Bengaluru, Karnataka, India"},
    "hyderabad": {"lat": 17.3850, "lon": 78.4867, "display_name": "Hyderabad, Telangana, India"},
    "ahmedabad": {"lat": 23.0225, "lon": 72.5714, "display_name": "Ahmedabad, Gujarat, India"},
    "pune": {"lat": 18.5204, "lon": 73.8567, "display_name": "Pune, Maharashtra, India"},
    "jaipur": {"lat": 26.9124, "lon": 75.7873, "display_name": "Jaipur, Rajasthan, India"},
    "surat": {"lat": 21.1702, "lon": 72.8311, "display_name": "Surat, Gujarat, India"},
    "lucknow": {"lat": 26.8467, "lon": 80.9462, "display_name": "Lucknow, Uttar Pradesh, India"},
    "kanpur": {"lat": 26.4499, "lon": 80.3319, "display_name": "Kanpur, Uttar Pradesh, India"},
    "nagpur": {"lat": 21.1458, "lon": 79.0882, "display_name": "Nagpur, Maharashtra, India"},
    "indore": {"lat": 22.7196, "lon": 75.8577, "display_name": "Indore, Madhya Pradesh, India"},
    "bhopal": {"lat": 23.2599, "lon": 77.4126, "display_name": "Bhopal, Madhya Pradesh, India"},
    "visakhapatnam": {"lat": 17.6868, "lon": 83.2185, "display_name": "Visakhapatnam, Andhra Pradesh, India"},
    "vizag": {"lat": 17.6868, "lon": 83.2185, "display_name": "Visakhapatnam, Andhra Pradesh, India"},
    "patna": {"lat": 25.5941, "lon": 85.1376, "display_name": "Patna, Bihar, India"},
    "vadodara": {"lat": 22.3072, "lon": 73.1812, "display_name": "Vadodara, Gujarat, India"},
    "ranchi": {"lat": 23.3441, "lon": 85.3096, "display_name": "Ranchi, Jharkhand, India"},
    "howrah": {"lat": 22.5958, "lon": 88.2636, "display_name": "Howrah, West Bengal, India"},
    "guwahati": {"lat": 26.1445, "lon": 91.7362, "display_name": "Guwahati, Assam, India"},
    "chandigarh": {"lat": 30.7333, "lon": 76.7794, "display_name": "Chandigarh, India"},
    "kochi": {"lat": 9.9312, "lon": 76.2673, "display_name": "Kochi, Kerala, India"},
    "cochin": {"lat": 9.9312, "lon": 76.2673, "display_name": "Kochi, Kerala, India"},
    "thiruvananthapuram": {"lat": 8.5241, "lon": 76.9366, "display_name": "Thiruvananthapuram, Kerala, India"},
    "trivandrum": {"lat": 8.5241, "lon": 76.9366, "display_name": "Thiruvananthapuram, Kerala, India"},
    "kanyakumari": {"lat": 8.0883, "lon": 77.5385, "display_name": "Kanyakumari, Tamil Nadu, India"},
    "port blair": {"lat": 11.6234, "lon": 92.7265, "display_name": "Port Blair, Andaman and Nicobar Islands, India"},

    # --- MAJOR INTERNATIONAL CITIES ---
    "tokyo": {"lat": 35.6762, "lon": 139.6503, "display_name": "Tokyo, Japan"},
    "new york": {"lat": 40.7128, "lon": -74.0060, "display_name": "New York, NY, USA"},
    "london": {"lat": 51.5074, "lon": -0.1278, "display_name": "London, United Kingdom"},
    "paris": {"lat": 48.8566, "lon": 2.3522, "display_name": "Paris, France"},
    "singapore": {"lat": 1.3521, "lon": 103.8198, "display_name": "Singapore"},
    "dubai": {"lat": 25.2048, "lon": 55.2708, "display_name": "Dubai, UAE"},
    "sydney": {"lat": -33.8688, "lon": 151.2093, "display_name": "Sydney, NSW, Australia"},
    "dhaka": {"lat": 23.8103, "lon": 90.4125, "display_name": "Dhaka, Bangladesh"},
    "colombo": {"lat": 6.9271, "lon": 79.8612, "display_name": "Colombo, Sri Lanka"},
    "kathmandu": {"lat": 27.7172, "lon": 85.3240, "display_name": "Kathmandu, Nepal"}
}


def parse_raw_coordinates(text: str) -> Optional[Dict]:
    """
    Intelligently parse raw coordinates even if written with spaces, e.g.:
    - "20 17591, 85 62055"
    - "20.17591, 85.62055"
    - "20 17591 85 62055"
    - "20.17591 85.62055"
    - "20.17591N, 85.62055E"
    """
    if not text:
        return None
        
    cleaned = text.strip()
    # Normalize space-separated decimals: "20 17591" -> "20.17591"
    cleaned = re.sub(r'(\b\d{1,2})\s+(\d{3,7}\b)', r'\1.\2', cleaned)
    # Remove compass notations N, S, E, W
    cleaned = re.sub(r'[nNsSeEwW]', '', cleaned)
    
    # Check for two float numbers separated by comma or space
    m = re.search(r'([-+]?\d{1,2}(?:\.\d+)?)[,\s]+([-+]?\d{1,3}(?:\.\d+)?)', cleaned)
    if m:
        try:
            lat = float(m.group(1))
            lon = float(m.group(2))
            if -90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0:
                return {
                    'lat': lat,
                    'lon': lon,
                    'display_name': f"GPS ({lat:.5f}, {lon:.5f})",
                    'type': 'coordinate',
                    'source': 'Coordinate Decoder'
                }
        except ValueError:
            pass
            
    return None


class RealGeocoder:
    """Smart Multi-Tier Geocoding Engine for SDARS"""

    def __init__(self):
        self.NOMINATIM_URL = "https://nominatim.openstreetmap.org"
        self.OPEN_METEO_GEO_URL = "https://geocoding-api.open-meteo.com/v1/search"
        self.headers = {
            'User-Agent': 'SDARS-DisasterAlertSystem/2.0 (Disaster-Response-Platform)'
        }
        self.last_request_time = 0
        self.cache = {}

    def _rate_limit(self):
        elapsed = time.time() - self.last_request_time
        if elapsed < 0.6:
            time.sleep(0.6 - elapsed)
        self.last_request_time = time.time()

    def _clean_query(self, text: str) -> str:
        s = text.lower().strip()
        # Remove special characters
        s = re.sub(r'[^a-zA-Z0-9\s]', ' ', s)
        s = re.sub(r'\s+', ' ', s).strip()
        return s

    def _search_gazetteer(self, query: str) -> Optional[Dict]:
        """Fast offline search in gazetteer with fuzzy matching & token stripping"""
        clean = self._clean_query(query)
        if not clean:
            return None

        # 1. Exact match
        if clean in SDARS_GAZETTEER:
            res = SDARS_GAZETTEER[clean].copy()
            res['source'] = 'SDARS Local Registry (Fast)'
            return res

        # 2. Match with common redundant words removed (e.g. "cuttack", "bhubaneswar", "odisha", "road", "chhak")
        noise_words = {'cuttack', 'bhubaneswar', 'bbsr', 'odisha', 'india', 'near', 'chhak', 'chowk', 'square', 'road', 'street', 'ps', 'police station', 'dist', 'district'}
        tokens = [w for w in clean.split() if w not in noise_words]
        stripped = " ".join(tokens)
        if stripped and stripped in SDARS_GAZETTEER:
            res = SDARS_GAZETTEER[stripped].copy()
            res['source'] = 'SDARS Local Registry (Token Match)'
            return res

        # 3. Substring inclusion
        for k, v in SDARS_GAZETTEER.items():
            if k == clean or (len(k) > 3 and k in clean) or (len(clean) > 3 and clean in k):
                res = v.copy()
                res['source'] = 'SDARS Local Registry (Partial Match)'
                return res

        # 4. Fuzzy match with cutoff
        keys = list(SDARS_GAZETTEER.keys())
        target = stripped if stripped else clean
        matches = difflib.get_close_matches(target, keys, n=1, cutoff=0.72)
        if matches:
            res = SDARS_GAZETTEER[matches[0]].copy()
            res['source'] = f"SDARS Local Registry (Fuzzy: {matches[0]})"
            return res

        return None

    def geocode(self, location_name: str) -> Optional[Dict]:
        """
        Convert location name or coordinates to {lat, lon, display_name}
        Prioritizes:
        1. Direct Coordinate parsing (instant)
        2. In-memory Cache
        3. Local SDARS Gazetteer & Fuzzy Matcher (instant)
        4. ArcGIS World Geocoding API (Enterprise-grade, Free, No key needed)
        5. Open-Meteo Geocoding API
        6. OpenStreetMap Nominatim with contextual prefixes
        """
        if not location_name:
            return None

        raw_str = str(location_name).strip()

        # Step 1: Direct Coordinate check
        coords = parse_raw_coordinates(raw_str)
        if coords:
            return coords

        cache_key = self._clean_query(raw_str)
        if cache_key in self.cache:
            return self.cache[cache_key]

        # Step 2: Gazetteer lookup
        gazetteer_match = self._search_gazetteer(raw_str)
        if gazetteer_match:
            self.cache[cache_key] = gazetteer_match
            return gazetteer_match

        # Step 3: ArcGIS World Geocoding API (Super accurate for India/Villages, Free without key for basic searches)
        try:
            arcgis_url = "https://geocode.arcgis.com/arcgis/rest/services/World/GeocodeServer/findAddressCandidates"
            arcgis_params = {'f': 'json', 'singleLine': f"{raw_str}, India", 'maxLocations': 1}
            resp = requests.get(arcgis_url, params=arcgis_params, headers=self.headers, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                if data.get('candidates'):
                    candidate = data['candidates'][0]
                    # Only accept if it's reasonably confident and in India (since we appended India)
                    if candidate.get('score', 0) > 70:
                        coords = {
                            'lat': float(candidate['location']['y']),
                            'lon': float(candidate['location']['x']),
                            'display_name': candidate.get('address', raw_str),
                            'type': 'place',
                            'source': 'ArcGIS Geocoding API'
                        }
                        self.cache[cache_key] = coords
                        return coords
        except Exception as e:
            print(f"⚠️ ArcGIS Geocoding error: {e}")

        # Step 4: Open-Meteo Geocoding (Fast, Free, No API key)
        try:
            resp = requests.get(
                self.OPEN_METEO_GEO_URL,
                params={'name': raw_str, 'count': 5, 'language': 'en', 'format': 'json'},
                timeout=4
            )
            if resp.status_code == 200:
                data = resp.json()
                results = data.get('results', [])
                if results:
                    # Prefer Indian result if available
                    best = next((r for r in results if r.get('country_code') == 'IN'), results[0])
                    coords = {
                        'lat': float(best['latitude']),
                        'lon': float(best['longitude']),
                        'display_name': f"{best.get('name', raw_str)}, {best.get('admin1', '')}, {best.get('country', '')}".strip(', '),
                        'type': best.get('feature_code', 'place'),
                        'source': 'Open-Meteo Geocoding'
                    }
                    self.cache[cache_key] = coords
                    return coords
        except Exception:
            pass

        # Step 5: OpenStreetMap Nominatim with context hints
        nominatim_queries = [
            f"{raw_str}, Odisha, India",
            f"{raw_str}, India",
            raw_str
        ]

        for q in nominatim_queries:
            self._rate_limit()
            try:
                r = requests.get(
                    f"{self.NOMINATIM_URL}/search",
                    params={'q': q, 'format': 'json', 'limit': 1, 'addressdetails': 1},
                    headers=self.headers,
                    timeout=1.2
                )
                if r.status_code == 200:
                    data = r.json()
                    if data and len(data) > 0:
                        first = data[0]
                        coords = {
                            'lat': float(first['lat']),
                            'lon': float(first['lon']),
                            'display_name': first.get('display_name', raw_str),
                            'type': first.get('type', 'place'),
                            'source': 'OpenStreetMap Nominatim'
                        }
                        self.cache[cache_key] = coords
                        return coords
            except Exception:
                continue

        return None

    def reverse_geocode(self, lat: float, lon: float) -> Optional[Dict]:
        """Convert coordinates to location name"""
        cache_key = f"{lat:.4f},{lon:.4f}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        # Check if close to any known gazetteer place (< 3km)
        for place, data in SDARS_GAZETTEER.items():
            if abs(data['lat'] - lat) < 0.03 and abs(data['lon'] - lon) < 0.03:
                res = {'name': data['display_name'].split(',')[0], 'display_name': data['display_name'], 'lat': lat, 'lon': lon}
                self.cache[cache_key] = res
                return res

        self._rate_limit()
        try:
            r = requests.get(
                f"{self.NOMINATIM_URL}/reverse",
                params={'lat': lat, 'lon': lon, 'format': 'json', 'addressdetails': 1},
                headers=self.headers,
                timeout=1.2
            )
            if r.status_code == 200:
                data = r.json()
                addr = data.get('address', {})
                name_parts = [
                    addr.get('suburb'),
                    addr.get('neighbourhood'),
                    addr.get('village'),
                    addr.get('town'),
                    addr.get('city'),
                    addr.get('district'),
                    addr.get('state')
                ]
                loc_name = next((p for p in name_parts if p), f"Location ({lat:.2f}, {lon:.2f})")
                res = {
                    'name': loc_name,
                    'display_name': data.get('display_name', loc_name),
                    'lat': lat,
                    'lon': lon,
                    'source': 'OpenStreetMap Nominatim'
                }
                self.cache[cache_key] = res
                return res
        except Exception:
            pass

        return {'name': f"Location ({lat:.2f}, {lon:.2f})", 'lat': lat, 'lon': lon}


# Singleton instance
real_geocoder = RealGeocoder()


def geocode_city(name: str) -> Optional[Dict]:
    """Convert location name or coordinates to lat/lon"""
    result = real_geocoder.geocode(name)
    if result:
        return {'lat': result['lat'], 'lon': result['lon'], 'display_name': result.get('display_name', name)}
    return None


def reverse_geocode(lat: float, lon: float) -> str:
    """Convert coordinates to location name"""
    result = real_geocoder.reverse_geocode(lat, lon)
    if result:
        return result.get('name', f"({lat:.2f}, {lon:.2f})")
    return f"Location ({lat:.2f}, {lon:.2f})"
