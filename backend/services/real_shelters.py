"""
Real Emergency Shelter & Facility Finder
Uses OpenStreetMap Overpass API to find REAL emergency facilities
100% FREE - No API key required!
"""
import requests
from typing import List, Dict, Optional
from datetime import datetime

class RealShelterFinder:
    """Find real emergency shelters, hospitals, fire stations using OpenStreetMap"""
    
    def __init__(self):
        self.OVERPASS_URL = "https://overpass-api.de/api/interpreter"
        
    def find_emergency_facilities(self, lat: float, lon: float, radius_km: int = 10) -> Dict:
        """
        Find REAL emergency facilities near a location
        Returns hospitals, fire stations, police, shelters
        """
        radius_m = radius_km * 1000
        
        # Overpass QL query for emergency facilities - ENHANCED for better detection
        query = f"""
        [out:json][timeout:35];
        (
          // Hospitals (Nodes, Ways, and Relations)
          node["amenity"="hospital"](around:{radius_m},{lat},{lon});
          way["amenity"="hospital"](around:{radius_m},{lat},{lon});
          rel["amenity"="hospital"](around:{radius_m},{lat},{lon});
          
          // Alternative Medical Tags
          node["healthcare"="hospital"](around:{radius_m},{lat},{lon});
          way["healthcare"="hospital"](around:{radius_m},{lat},{lon});
          node["amenity"="clinic"](around:{radius_m},{lat},{lon});
          node["healthcare"="clinic"](around:{radius_m},{lat},{lon});
          
          // Fire Stations
          node["amenity"="fire_station"](around:{radius_m},{lat},{lon});
          way["amenity"="fire_station"](around:{radius_m},{lat},{lon});
          
          // Police Stations
          node["amenity"="police"](around:{radius_m},{lat},{lon});
          way["amenity"="police"](around:{radius_m},{lat},{lon});
          
          // Emergency Shelters
          node["amenity"="shelter"](around:{radius_m},{lat},{lon});
          node["emergency"="assembly_point"](around:{radius_m},{lat},{lon});
          node["social_facility"="shelter"](around:{radius_m},{lat},{lon});
          
          // Community Centers (potential shelters)
          node["amenity"="community_centre"](around:{radius_m},{lat},{lon});
          way["amenity"="community_centre"](around:{radius_m},{lat},{lon});
        );
        out center;
        """
        
        try:
            print(f"🏥 Fetching REAL emergency facilities near ({lat}, {lon})...")
            
            response = requests.post(
                self.OVERPASS_URL,
                data={'data': query},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                elements = data.get('elements', [])
                
                facilities = {
                    'hospitals': [],
                    'fire_stations': [],
                    'police_stations': [],
                    'shelters': [],
                    'community_centers': [],
                    'total_count': 0,
                    'source': 'OpenStreetMap (REAL)',
                    'query_location': {'lat': lat, 'lon': lon},
                    'radius_km': radius_km
                }
                
                for element in elements:
                    tags = element.get('tags', {})
                    name = tags.get('name', 'Unnamed Facility')
                    
                    # Get coordinates
                    if element['type'] == 'node':
                        facility_lat = element.get('lat')
                        facility_lon = element.get('lon')
                    else:
                        # For ways, use center
                        center = element.get('center', {})
                        facility_lat = center.get('lat', lat)
                        facility_lon = center.get('lon', lon)
                    
                    # Smart type detection
                    f_type = tags.get('amenity') or tags.get('healthcare') or tags.get('emergency') or 'facility'
                    
                    facility_info = {
                        'name': name,
                        'coords': [facility_lat, facility_lon],
                        'type': f_type,
                        'address': tags.get('addr:full') or tags.get('addr:street', ''),
                        'phone': tags.get('phone', ''),
                        'capacity': tags.get('capacity', 'Unknown'),
                        'osm_id': element.get('id'),
                        'source': 'OpenStreetMap (REAL)'
                    }
                    
                    # Categorize - SMART CATEGORIZATION
                    amenity = tags.get('amenity', '')
                    emergency = tags.get('emergency', '')
                    social = tags.get('social_facility', '')
                    healthcare = tags.get('healthcare', '')
                    
                    if amenity in ['hospital', 'clinic'] or healthcare in ['hospital', 'clinic']:
                        facilities['hospitals'].append(facility_info)
                    elif amenity == 'fire_station':
                        facilities['fire_stations'].append(facility_info)
                    elif amenity == 'police':
                        facilities['police_stations'].append(facility_info)
                    elif amenity == 'shelter' or emergency == 'assembly_point' or social == 'shelter':
                        facilities['shelters'].append(facility_info)
                    elif amenity == 'community_centre':
                        facilities['community_centers'].append(facility_info)
                
                facilities['total_count'] = (
                    len(facilities['hospitals']) +
                    len(facilities['fire_stations']) +
                    len(facilities['police_stations']) +
                    len(facilities['shelters']) +
                    len(facilities['community_centers'])
                )
                
                print(f"✅ Found {facilities['total_count']} REAL emergency facilities!")
                return facilities
                
            else:
                print(f"⚠️ Tier 1 (Overpass) error: {response.status_code}. Initiating Tier 2...")
                # Note: For simplicity in this synchronous service, we use a basic version of tier 2
                return self._fetch_secondary_tier_sync(lat, lon, radius_km)
                
        except Exception as e:
            print(f"⚠️ Tier 1 (Overpass) exception: {e}. Initiating Tier 2...")
            return self._fetch_secondary_tier_sync(lat, lon, radius_km)

    def _fetch_secondary_tier_sync(self, lat: float, lon: float, radius_km: int) -> Dict:
        """Synchronous version of Tier 2 for seamless integration"""
        try:
            print(f"📡 Tier 2: Nominatim Redundancy Search for ({lat}, {lon})...")
            url = f"https://nominatim.openstreetmap.org/search?q=hospital+near+{lat},{lon}&format=json&limit=5"
            headers = {'User-Agent': 'SDARS-Survival-System/1.0'}
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                results = response.json()
                if results:
                    hospitals = [{
                        'name': r.get('display_name', '').split(',')[0],
                        'coords': [float(r['lat']), float(r['lon'])],
                        'type': 'hospital',
                        'source': 'Nominatim (Redundancy Tier 2)'
                    } for r in results]
                    return {'hospitals': hospitals, 'total_count': len(hospitals), 'source': 'Tier 2 Recovery'}
            return self._get_fallback_facilities(lat, lon)
        except:
            return self._get_fallback_facilities(lat, lon)
    
    def get_nearest_shelters(self, lat: float, lon: float, limit: int = 10) -> List[Dict]:
        """Get the nearest shelters/safe locations for evacuation"""
        # Search in a slightly larger 20km radius for better coverage
        facilities = self.find_emergency_facilities(lat, lon, radius_km=20)
        
        # Combine all potential rescue/medical locations
        # Prioritize hospitals by including all of them in the main stream
        all_shelters = (
            facilities.get('hospitals', []) +
            facilities.get('shelters', []) +
            facilities.get('fire_stations', []) +
            facilities.get('community_centers', [])
        )
        
        # Calculate distance and sort
        for shelter in all_shelters:
            coords = shelter.get('coords', [lat, lon])
            shelter['distance_km'] = self._calculate_distance(lat, lon, coords[0], coords[1])
        
        # Sort by distance and limit
        # This will now include hospitals and shelters naturally based on distance
        all_shelters.sort(key=lambda x: x.get('distance_km', 999))
        
        # De-duplicate by name and location (if OSM returns same object as way and node)
        unique_facilities = []
        seen = set()
        for f in all_shelters:
            key = f"{f['name']}_{f['coords'][0]:.4f}"
            if key not in seen:
                unique_facilities.append(f)
                seen.add(key)

        return unique_facilities[:limit]

    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate approximate distance in km between two points"""
        import math
        R = 6371  # Earth's radius in km
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return round(R * c, 2)
    
    async def _fetch_secondary_tier(self, lat: float, lon: float, radius_km: int) -> Dict:
        """
        Tier 2: Nominatim API (Different infrastructure than Overpass)
        Search for essential amenities as a secondary fallback
        """
        try:
            print(f"📡 Tier 2: Launching Nominatim Redundancy Search for ({lat}, {lon})...")
            # We search for 'emergency' and 'hospital' specifically
            url = f"https://nominatim.openstreetmap.org/search?q=hospital+near+{lat},{lon}&format=json&limit=5"
            headers = {'User-Agent': 'SDARS-Survival-System/1.0'}
            
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                results = response.json()
                fallback_hospitals = []
                for res in results:
                    fallback_hospitals.append({
                        'name': res.get('display_name', '').split(',')[0],
                        'coords': [float(res['lat']), float(res['lon'])],
                        'type': 'hospital',
                        'source': 'Nominatim (Redundancy Tier 2)'
                    })
                
                if fallback_hospitals:
                    print(f"✅ Tier 2 Recovery: Found {len(fallback_hospitals)} hospitals.")
                    return {
                        'hospitals': fallback_hospitals,
                        'total_count': len(fallback_hospitals),
                        'source': 'Nominatim (Redundancy Tier 2)'
                    }
            return self._get_fallback_facilities(lat, lon)
        except Exception as e:
            print(f"⚠️ Tier 2 Failed: {e}")
            return self._get_fallback_facilities(lat, lon)

    def _get_fallback_facilities(self, lat: float, lon: float) -> Dict:
        """
        Tier 3: Global Strategic Registry (HARD CODED FAIL-SAFE)
        In a total API blackout, we return the closest MAJOR International Emergency Center
        """
        print("🛑 Tier 3: TOTAL API BLACKOUT. Activating Hardcoded Strategic Registry.")
        
        # Registry of major global coordination centers
        global_registry = [
            {'name': 'WHO Strategic Health Ops (Geneva)', 'coords': [46.2044, 6.1432]},
            {'name': 'UN Disaster Relief Hub (Dubai)', 'coords': [25.2048, 55.2708]},
            {'name': 'National Emergency Management (USA)', 'coords': [38.8977, -77.0365]},
            {'name': 'India Disaster Response (NDRF)', 'coords': [28.6139, 77.2090]},
            {'name': 'Tokyo Crisis Management', 'coords': [35.6895, 139.6917]}
        ]
        
        # Find the single closest one to help the user at least find a coordination point
        closest = min(global_registry, key=lambda x: self._calculate_distance(lat, lon, x['coords'][0], x['coords'][1]))
        
        return {
            'hospitals': [{
                'name': f"GLOBAL FAILSAFE: {closest['name']}",
                'coords': closest['coords'],
                'type': 'strategic_command',
                'source': 'Hardcoded Fail-Safe (Tier 3)',
                'note': 'CRITICAL: Live APIs unavailable. Head to nearest Major Response Hub.'
            }],
            'total_count': 1,
            'source': 'Fail-Safe Registry',
            'query_location': {'lat': lat, 'lon': lon}
        }


# Singleton instance
real_shelter_finder = RealShelterFinder()


# Test
if __name__ == "__main__":
    finder = RealShelterFinder()
    
    # Test with Mumbai
    print("\n🔍 Testing Mumbai Emergency Facilities...")
    facilities = finder.find_emergency_facilities(19.0760, 72.8777, radius_km=5)
    
    print(f"\n📊 Results for Mumbai:")
    print(f"  🏥 Hospitals: {len(facilities['hospitals'])}")
    print(f"  🚒 Fire Stations: {len(facilities['fire_stations'])}")
    print(f"  🚔 Police Stations: {len(facilities['police_stations'])}")
    print(f"  🏠 Shelters: {len(facilities['shelters'])}")
    print(f"  🏛️ Community Centers: {len(facilities['community_centers'])}")
    
    # Show some names
    for hospital in facilities['hospitals'][:3]:
        print(f"    - {hospital['name']}")
