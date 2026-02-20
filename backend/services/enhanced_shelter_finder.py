"""
Enhanced Emergency Shelter Finder with Multiple Data Sources
Combines Google Places API + OpenStreetMap for maximum coverage
"""
import requests
import os
from typing import List, Dict, Optional
from datetime import datetime
import math

class EnhancedShelterFinder:
    """Find emergency facilities using multiple data sources"""
    
    def __init__(self):
        self.OVERPASS_URL = "https://overpass-api.de/api/interpreter"
        # Google Places API key (optional - falls back to OSM if not provided)
        self.GOOGLE_API_KEY = os.getenv('GOOGLE_PLACES_API_KEY', '')
        self.GOOGLE_PLACES_URL = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
        
    def find_emergency_facilities(self, lat: float, lon: float, radius_km: int = 10) -> Dict:
        """
        Find emergency facilities using multiple sources
        Priority: Google Places API -> OpenStreetMap -> Fallback
        """
        facilities = None
        
        # Try Google Places API first (if API key available)
        if self.GOOGLE_API_KEY:
            print(f"🌐 Trying Google Places API...")
            facilities = self._fetch_from_google_places(lat, lon, radius_km)
            if facilities and facilities['total_count'] > 0:
                print(f"✅ Google Places found {facilities['total_count']} facilities")
                return facilities
        
        # Fallback to OpenStreetMap
        print(f"🗺️ Fetching from OpenStreetMap...")
        facilities = self._fetch_from_osm(lat, lon, radius_km)
        if facilities and facilities['total_count'] > 0:
            print(f"✅ OpenStreetMap found {facilities['total_count']} facilities")
            return facilities
        
        # Last resort: return empty but valid structure
        print(f"⚠️ No facilities found in any source")
        return self._get_empty_facilities(lat, lon, radius_km)
    
    def _fetch_from_google_places(self, lat: float, lon: float, radius_km: int) -> Optional[Dict]:
        """Fetch facilities from Google Places API"""
        try:
            radius_m = min(radius_km * 1000, 50000)  # Google max is 50km
            
            facility_types = [
                ('hospital', 'hospitals'),
                ('fire_station', 'fire_stations'),
                ('police', 'police_stations'),
                ('local_government_office', 'shelters'),
                ('city_hall', 'community_centers')
            ]
            
            facilities = {
                'hospitals': [],
                'fire_stations': [],
                'police_stations': [],
                'shelters': [],
                'community_centers': [],
                'total_count': 0,
                'source': 'Google Places API',
                'query_location': {'lat': lat, 'lon': lon},
                'radius_km': radius_km
            }
            
            for place_type, category in facility_types:
                params = {
                    'location': f"{lat},{lon}",
                    'radius': radius_m,
                    'type': place_type,
                    'key': self.GOOGLE_API_KEY
                }
                
                response = requests.get(self.GOOGLE_PLACES_URL, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    results = data.get('results', [])
                    
                    for place in results:
                        location = place.get('geometry', {}).get('location', {})
                        facility_info = {
                            'name': place.get('name', 'Unnamed Facility'),
                            'coords': [location.get('lat'), location.get('lon')],
                            'type': place_type,
                            'address': place.get('vicinity', ''),
                            'rating': place.get('rating', 'N/A'),
                            'place_id': place.get('place_id'),
                            'source': 'Google Places',
                            'distance_km': self._calculate_distance(
                                lat, lon, 
                                location.get('lat'), location.get('lon')
                            )
                        }
                        facilities[category].append(facility_info)
            
            facilities['total_count'] = sum(
                len(facilities[cat]) for cat in 
                ['hospitals', 'fire_stations', 'police_stations', 'shelters', 'community_centers']
            )
            
            return facilities if facilities['total_count'] > 0 else None
            
        except Exception as e:
            print(f"⚠️ Google Places API error: {e}")
            return None
    
    def _fetch_from_osm(self, lat: float, lon: float, radius_km: int) -> Optional[Dict]:
        """Fetch facilities from OpenStreetMap (existing implementation)"""
        radius_m = radius_km * 1000
        
        # Enhanced Overpass query with more facility types
        query = f"""
        [out:json][timeout:25];
        (
          // Hospitals & Clinics
          node["amenity"="hospital"](around:{radius_m},{lat},{lon});
          way["amenity"="hospital"](around:{radius_m},{lat},{lon});
          node["amenity"="clinic"](around:{radius_m},{lat},{lon});
          
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
          
          // Community Centers & Government Buildings
          node["amenity"="community_centre"](around:{radius_m},{lat},{lon});
          way["amenity"="community_centre"](around:{radius_m},{lat},{lon});
          node["amenity"="townhall"](around:{radius_m},{lat},{lon});
          way["amenity"="townhall"](around:{radius_m},{lat},{lon});
          
          // Schools (potential emergency shelters)
          node["amenity"="school"](around:{radius_m},{lat},{lon});
          way["amenity"="school"](around:{radius_m},{lat},{lon});
        );
        out center;
        """
        
        try:
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
                    'source': 'OpenStreetMap',
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
                        center = element.get('center', {})
                        facility_lat = center.get('lat', lat)
                        facility_lon = center.get('lon', lon)
                    
                    facility_info = {
                        'name': name,
                        'coords': [facility_lat, facility_lon],
                        'type': tags.get('amenity') or tags.get('emergency') or 'facility',
                        'address': tags.get('addr:full') or tags.get('addr:street', ''),
                        'phone': tags.get('phone', ''),
                        'capacity': tags.get('capacity', 'Unknown'),
                        'osm_id': element.get('id'),
                        'source': 'OpenStreetMap',
                        'distance_km': self._calculate_distance(lat, lon, facility_lat, facility_lon)
                    }
                    
                    # Categorize
                    amenity = tags.get('amenity', '')
                    emergency = tags.get('emergency', '')
                    social = tags.get('social_facility', '')
                    
                    if amenity in ['hospital', 'clinic']:
                        facilities['hospitals'].append(facility_info)
                    elif amenity == 'fire_station':
                        facilities['fire_stations'].append(facility_info)
                    elif amenity == 'police':
                        facilities['police_stations'].append(facility_info)
                    elif amenity == 'shelter' or emergency == 'assembly_point' or social == 'shelter':
                        facilities['shelters'].append(facility_info)
                    elif amenity in ['community_centre', 'townhall', 'school']:
                        facilities['community_centers'].append(facility_info)
                
                facilities['total_count'] = sum(
                    len(facilities[cat]) for cat in 
                    ['hospitals', 'fire_stations', 'police_stations', 'shelters', 'community_centers']
                )
                
                return facilities if facilities['total_count'] > 0 else None
                
            return None
            
        except Exception as e:
            print(f"⚠️ OpenStreetMap error: {e}")
            return None
    
    def get_nearest_shelters(self, lat: float, lon: float, limit: int = 5) -> List[Dict]:
        """Get the nearest shelters/safe locations for evacuation"""
        facilities = self.find_emergency_facilities(lat, lon, radius_km=15)
        
        # Combine all potential shelter locations
        all_shelters = (
            facilities.get('shelters', []) +
            facilities.get('community_centers', []) +
            facilities.get('hospitals', [])[:2]
        )
        
        # Sort by distance
        all_shelters.sort(key=lambda x: x.get('distance_km', 999))
        return all_shelters[:limit]
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance in km between two points using Haversine formula"""
        R = 6371  # Earth's radius in km
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return round(R * c, 2)
    
    def _get_empty_facilities(self, lat: float, lon: float, radius_km: int) -> Dict:
        """Return empty but valid structure when no facilities found"""
        return {
            'hospitals': [],
            'fire_stations': [],
            'police_stations': [],
            'shelters': [],
            'community_centers': [],
            'total_count': 0,
            'source': 'No data available',
            'query_location': {'lat': lat, 'lon': lon},
            'radius_km': radius_km,
            'note': 'No facilities found in this area. Try expanding the search radius or checking a different location.'
        }


# Singleton instance
enhanced_shelter_finder = EnhancedShelterFinder()


# Test
if __name__ == "__main__":
    finder = EnhancedShelterFinder()
    
    # Test with Mumbai
    print("\n🔍 Testing Mumbai Emergency Facilities...")
    facilities = finder.find_emergency_facilities(19.0760, 72.8777, radius_km=5)
    
    print(f"\n📊 Results for Mumbai:")
    print(f"  Source: {facilities['source']}")
    print(f"  🏥 Hospitals: {len(facilities['hospitals'])}")
    print(f"  🚒 Fire Stations: {len(facilities['fire_stations'])}")
    print(f"  🚔 Police Stations: {len(facilities['police_stations'])}")
    print(f"  🏠 Shelters: {len(facilities['shelters'])}")
    print(f"  🏛️ Community Centers: {len(facilities['community_centers'])}")
    print(f"  📍 Total: {facilities['total_count']}")
    
    # Show some names
    if facilities['hospitals']:
        print(f"\n  Sample Hospitals:")
        for hospital in facilities['hospitals'][:3]:
            print(f"    - {hospital['name']} ({hospital['distance_km']} km)")
