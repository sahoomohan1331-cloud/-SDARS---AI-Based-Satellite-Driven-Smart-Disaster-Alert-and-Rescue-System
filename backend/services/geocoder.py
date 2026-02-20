"""
Real Geocoding Service for SDARS
Uses OpenStreetMap Nominatim API (FREE - No API key required!)
Can find ANY location worldwide including remote areas
"""
import requests
from typing import Optional, Dict
import time

class RealGeocoder:
    """Real geocoding using OpenStreetMap Nominatim API"""
    
    def __init__(self):
        self.NOMINATIM_URL = "https://nominatim.openstreetmap.org"
        self.headers = {
            'User-Agent': 'SDARS-DisasterAlertSystem/1.0 (College Project)'
        }
        self.last_request_time = 0
        
        # Cache for frequently searched locations
        self.cache = {}
        
    def _rate_limit(self):
        """Nominatim requires 1 request per second"""
        elapsed = time.time() - self.last_request_time
        if elapsed < 1.0:
            time.sleep(1.0 - elapsed)
        self.last_request_time = time.time()
    
    def geocode(self, location_name: str) -> Optional[Dict]:
        """
        Convert location name to coordinates
        Works for ANY location worldwide - cities, villages, remote areas
        """
        # Check cache first
        cache_key = location_name.lower().strip()
        if cache_key in self.cache:
            print(f"📍 Cache hit for '{location_name}'")
            return self.cache[cache_key]
        
        self._rate_limit()
        
        try:
            print(f"🔍 Geocoding '{location_name}' using OpenStreetMap...")
            
            response = requests.get(
                f"{self.NOMINATIM_URL}/search",
                params={
                    'q': location_name,
                    'format': 'json',
                    'limit': 1,
                    'addressdetails': 1
                },
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                results = response.json()
                
                if results:
                    result = results[0]
                    coords = {
                        'lat': float(result['lat']),
                        'lon': float(result['lon']),
                        'display_name': result.get('display_name', location_name),
                        'type': result.get('type', 'unknown'),
                        'source': 'OpenStreetMap Nominatim (REAL)'
                    }
                    
                    # Cache the result
                    self.cache[cache_key] = coords
                    
                    print(f"✅ Found: {coords['display_name'][:50]}... ({coords['lat']}, {coords['lon']})")
                    return coords
                else:
                    print(f"⚠️ Location '{location_name}' not found")
                    return None
                    
            else:
                print(f"⚠️ Nominatim API error: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"⚠️ Geocoding error: {e}")
            return None
    
    def reverse_geocode(self, lat: float, lon: float) -> Optional[Dict]:
        """
        Convert coordinates to location name
        """
        cache_key = f"{lat:.4f},{lon:.4f}"
        if cache_key in self.cache:
            return self.cache[cache_key]
            
        self._rate_limit()
        
        try:
            response = requests.get(
                f"{self.NOMINATIM_URL}/reverse",
                params={
                    'lat': lat,
                    'lon': lon,
                    'format': 'json',
                    'addressdetails': 1
                },
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result and 'address' in result:
                    # Fallback chain for location name
                    addr = result.get('address', {})
                    name_parts = [
                        addr.get('hamlet'),
                        addr.get('village'),
                        addr.get('town'),
                        addr.get('suburb'),
                        addr.get('neighbourhood'),
                        addr.get('city_district'),
                        addr.get('city'),
                        addr.get('municipality'),
                        addr.get('county'),
                        addr.get('district'),
                        addr.get('state'),
                        addr.get('country')
                    ]
                    
                    # Get the first non-None part
                    location_name = next((part for part in name_parts if part), 'Unknown Area')
                    
                    # Start with location_name
                    final_name = location_name

                    location_info = {
                        'name': final_name,
                        'display_name': result.get('display_name', ''),
                        'country': address.get('country', ''),
                        'state': address.get('state', ''),
                        'lat': lat,
                        'lon': lon,
                        'source': 'OpenStreetMap Nominatim (REAL)'
                    }
                    
                    self.cache[cache_key] = location_info
                    return location_info
                    
        except Exception as e:
            print(f"⚠️ Reverse geocoding error: {e}")
            
        return {'name': f"Location ({lat:.2f}, {lon:.2f})", 'lat': lat, 'lon': lon}


# Singleton instance
real_geocoder = RealGeocoder()


# Wrapper functions for backwards compatibility
def geocode_city(name: str) -> Optional[Dict]:
    """Convert location name to lat/lon - now works for ANY location!"""
    result = real_geocoder.geocode(name)
    if result:
        return {'lat': result['lat'], 'lon': result['lon']}
    return None


def reverse_geocode(lat: float, lon: float) -> str:
    """Convert coordinates to location name"""
    result = real_geocoder.reverse_geocode(lat, lon)
    if result:
        return result.get('name', f"({lat:.2f}, {lon:.2f})")
    return f"Location ({lat:.2f}, {lon:.2f})"


# Test
if __name__ == "__main__":
    print("\n🧪 Testing Real Geocoder...\n")
    
    # Test various locations including remote areas
    test_locations = [
        "Cuttack",
        "Dasapalla", 
        "Mumbai",
        "Raighar, Odisha",
        "Nabarangpur",
        "Tokyo",
        "some random village in India"
    ]
    
    for loc in test_locations:
        result = geocode_city(loc)
        if result:
            print(f"  ✅ {loc}: ({result['lat']}, {result['lon']})")
        else:
            print(f"  ❌ {loc}: Not found")
        print()
