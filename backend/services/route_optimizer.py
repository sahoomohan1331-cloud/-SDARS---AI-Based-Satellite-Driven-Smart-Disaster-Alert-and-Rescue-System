"""
SDARS Advanced Route Optimizer
Disaster-aware routing with multi-objective optimization
"""
import requests
from typing import List, Dict, Tuple, Optional
import math
from datetime import datetime
import asyncio
import aiohttp


class RouteOptimizer:
    """Advanced routing system with disaster awareness"""
    
    def __init__(self):
        self.OSRM_URL = "https://router.project-osrm.org/route/v1"
        self.cache = {}
        
    def calculate_route_safety_score(self, route_predictions: List[Dict], road_statuses: Optional[List[Dict]] = None) -> Dict:
        """
        Calculate comprehensive safety score for a route, factoring in active disaster predictions
        and real-time blocked/waterlogged road corridor telemetry.
        
        Returns:
            {
                'overall_score': 0-100 (100 = safest),
                'risk_level': 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL',
                'hazard_segments': [...],
                'blocked_roads': [...],
                'detour_recommendations': [...],
                'recommendations': [...],
                'safest_time': 'now' | 'wait_6h' | 'avoid',
            }
        """
        if not route_predictions:
            return {
                'overall_score': 100,
                'risk_level': 'LOW',
                'hazard_segments': [],
                'blocked_roads': [],
                'detour_recommendations': [],
                'recommendations': ['Route is clear'],
                'safest_time': 'now'
            }
        
        # Aggregate all predictions along route
        total_points = len(route_predictions)
        high_risk_count = sum(1 for p in route_predictions if p.get('overall_risk_level') == 'HIGH')
        medium_risk_count = sum(1 for p in route_predictions if p.get('overall_risk_level') == 'MEDIUM')
        
        # Calculate weighted score
        safety_score = 100
        safety_score -= (high_risk_count / total_points) * 50  # Each high risk waypoint reduces score by up to 50
        safety_score -= (medium_risk_count / total_points) * 25  # Each medium risk reduces by up to 25

        # Check proximity to real-time road blockages / flooded corridors
        blocked_roads_detected = []
        detour_recommendations = []
        if road_statuses:
            for pred in route_predictions:
                loc = pred.get('location', {})
                plat = loc.get('lat') if 'lat' in loc else loc.get('latitude')
                plon = loc.get('lon') if 'lon' in loc else loc.get('longitude')
                if plat is None or plon is None:
                    continue
                
                for road in road_statuses:
                    status = road.get('status', 'OPEN').upper()
                    if status in ['BLOCKED', 'WATERLOGGED', 'LANDSLIDE']:
                        rlat = road.get('latitude')
                        rlon = road.get('longitude')
                        if rlat is not None and rlon is not None:
                            dist_km = self._calculate_distance(plat, plon, rlat, rlon)
                            if dist_km <= 2.0:  # Within 2 km of corridor obstruction
                                if not any(b['name'] == road.get('name') for b in blocked_roads_detected):
                                    blocked_roads_detected.append({
                                        'road_id': road.get('road_id'),
                                        'name': road.get('name'),
                                        'status': status,
                                        'reason': road.get('reason', 'Corridor impassable'),
                                        'detour': road.get('detour', 'Seek alternative high-elevation route'),
                                        'distance_km': round(dist_km, 2)
                                    })
                                    if road.get('detour'):
                                        detour_recommendations.append(f"Detour for {road.get('name')}: {road.get('detour')}")

        # Heavy penalty for blocked or submerged corridors on route
        if blocked_roads_detected:
            safety_score -= len(blocked_roads_detected) * 35

        safety_score = max(0, min(100, safety_score))  # Clamp to 0-100
        
        # Determine risk level
        if safety_score >= 80 and not blocked_roads_detected:
            risk_level = 'LOW'
        elif safety_score >= 60 and not blocked_roads_detected:
            risk_level = 'MEDIUM'
        elif safety_score >= 40:
            risk_level = 'HIGH'
        else:
            risk_level = 'CRITICAL'
        
        # Extract hazard segments
        hazard_segments = []
        for pred in route_predictions:
            if pred.get('overall_risk_level') in ['HIGH', 'MEDIUM']:
                hazard_segments.append({
                    'location': pred.get('location', {}),
                    'threat': pred.get('primary_threat'),
                    'confidence': pred.get(pred.get('primary_threat'), {}).get('confidence', 0),
                    'risk_level': pred.get('overall_risk_level')
                })
        
        # Generate recommendations
        recommendations = []
        # Prepend blocked road directives first as highest priority
        for b in blocked_roads_detected:
            recommendations.append(f"🛑 CORRIDOR {b['status']}: {b['name']} ({b['reason']}). DETOUR: {b['detour']}")

        if high_risk_count > 0:
            recommendations.append(f"⚠️ {high_risk_count} high-risk zones detected on route")
            recommendations.append("Consider alternative route or delay travel")
        
        if medium_risk_count > 0:
            recommendations.append(f"⚡ {medium_risk_count} medium-risk areas along path")
            recommendations.append("Proceed with caution and monitor conditions")
        
        if safety_score >= 80 and not blocked_roads_detected:
            recommendations.append("✅ Route is generally safe for travel")
            safest_time = 'now'
        elif safety_score >= 60 and not blocked_roads_detected:
            recommendations.append("⚠️ Some risks present, travel during daylight recommended")
            safest_time = 'now'
        elif safety_score >= 40:
            recommendations.append("🚨 High risk route, consider waiting or alternate path")
            safest_time = 'wait_6h'
        else:
            recommendations.append("🛑 Critical risk, strongly advise avoiding this route")
            safest_time = 'avoid'
        
        return {
            'overall_score': round(safety_score, 1),
            'risk_level': risk_level,
            'hazard_segments': hazard_segments,
            'blocked_roads': blocked_roads_detected,
            'detour_recommendations': detour_recommendations,
            'recommendations': recommendations,
            'safest_time': safest_time,
            'interception_events': self._detect_interception_risk(route_predictions),
            'analysis': {
                'total_waypoints': total_points,
                'high_risk_zones': high_risk_count,
                'medium_risk_zones': medium_risk_count,
                'blocked_corridors': len(blocked_roads_detected),
                'safe_zones': max(0, total_points - high_risk_count - medium_risk_count)
            }
        }

    def _detect_interception_risk(self, route_predictions: List[Dict]) -> List[Dict]:
        """
        Detect specific spatiotemporal 'interception' points where a 
        moving disaster expands into the travel path.
        """
        interceptions = []
        for i, pred in enumerate(route_predictions):
            risk = pred.get('overall_risk_level')
            if risk in ['CRITICAL', 'HIGH']:
                # Detect 'Collision Point'
                threat_type = pred.get('primary_threat', 'Unknown hazard')
                interceptions.append({
                    'waypoint_index': i,
                    'coords': pred.get('location', {}),
                    'threat': threat_type,
                    'estimated_time_to_impact': f"{i * 5} minutes", # Simplified time heuristic
                    'severity': 'IMMEDIATE INTERCEPTION' if risk == 'CRITICAL' else 'POTENTIAL INTERCEPTION'
                })
        return interceptions
    
    async def find_multiple_routes(
        self, 
        start_lat: float, 
        start_lon: float, 
        end_lat: float, 
        end_lon: float,
        alternatives: int = 3
    ) -> List[Dict]:
        """
        Find multiple route alternatives using different strategies
        
        Strategies:
        1. Fastest route (OSRM default)
        2. Shortest distance route
        3. Alternative waypoints (scenic/avoiding highways)
        """
        routes = []
        
        # Strategy 1: Direct fastest route with alternatives
        try:
            params = {
                'alternatives': alternatives,
                'steps': 'true',
                'overview': 'full',
                'geometries': 'geojson'
            }
            
            url = f"{self.OSRM_URL}/driving/{start_lon},{start_lat};{end_lon},{end_lat}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        osrm_routes = data.get('routes', [])
                        
                        for idx, route in enumerate(osrm_routes):
                            routes.append({
                                'id': f'route_{idx+1}',
                                'name': f'Route {idx+1}',
                                'strategy': 'fastest' if idx == 0 else f'alternative_{idx}',
                                'distance_m': route['distance'],
                                'duration_s': route['duration'],
                                'geometry': route['geometry'],
                                'legs': route.get('legs', []),
                                'source': 'OSRM'
                            })
        except Exception as e:
            print(f"Error fetching OSRM routes: {e}")
        
        # Strategy 2: If we have less than 3 routes, generate synthetic alternatives
        # by adding intermediate waypoints
        if len(routes) < alternatives:
            try:
                # Calculate midpoint with offset for alternative route
                mid_lat = (start_lat + end_lat) / 2
                mid_lon = (start_lon + end_lon) / 2
                
                # Offset perpendicular to direct line (creates a detour)
                offset = 0.05  # ~5km offset
                alt_mid_lat = mid_lat + offset
                alt_mid_lon = mid_lon + offset
                
                # Route through alternative waypoint
                alt_url = f"{self.OSRM_URL}/driving/{start_lon},{start_lat};{alt_mid_lon},{alt_mid_lat};{end_lon},{end_lat}"
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(alt_url, params={'steps': 'true', 'overview': 'full', 'geometries': 'geojson'}, timeout=10) as response:
                        if response.status == 200:
                            data = await response.json()
                            if data.get('routes'):
                                alt_route = data['routes'][0]
                                routes.append({
                                    'id': f'route_{len(routes)+1}',
                                    'name': f'Scenic Route',
                                    'strategy': 'waypoint_detour',
                                    'distance_m': alt_route['distance'],
                                    'duration_s': alt_route['duration'],
                                    'geometry': alt_route['geometry'],
                                    'legs': alt_route.get('legs', []),
                                    'source': 'OSRM-Waypoint'
                                })
            except Exception as e:
                print(f"Error generating alternative route: {e}")
        
        return routes
    
    def calculate_evacuation_route(
        self,
        current_lat: float,
        current_lon: float,
        disaster_type: str,
        disaster_lat: float,
        disaster_lon: float,
        shelters: List[Dict]
    ) -> Dict:
        """
        Calculate optimal evacuation route away from disaster
        
        Priority:
        1. Direction away from disaster epicenter
        2. Closest safe shelter
        3. Avoid high-risk zones
        """
        # Calculate direction away from disaster
        away_bearing = self._calculate_bearing(
            disaster_lat, disaster_lon, 
            current_lat, current_lon
        )
        
        # Find shelters in the "away" direction (within 90° cone)
        safe_shelters = []
        for shelter in shelters:
            shelter_coords = shelter.get('coords', [0, 0])
            shelter_bearing = self._calculate_bearing(
                current_lat, current_lon,
                shelter_coords[0], shelter_coords[1]
            )
            
            # Check if shelter is in safe direction (away from disaster)
            bearing_diff = abs(shelter_bearing - away_bearing)
            if bearing_diff <= 90 or bearing_diff >= 270:
                shelter['distance_km'] = self._calculate_distance(
                    current_lat, current_lon,
                    shelter_coords[0], shelter_coords[1]
                )
                safe_shelters.append(shelter)
        
        # Sort by distance
        safe_shelters.sort(key=lambda x: x.get('distance_km', 999))
        
        # ⭐ TACTICAL VECTORING: Calculate immediate escape vector
        escape_vector = (away_bearing + 180) % 360 # Vector from disaster through user
        
        return {
            'recommended_direction': self._bearing_to_direction(away_bearing),
            'escape_vector_degrees': escape_vector,
            'nearest_safe_shelters': safe_shelters[:5],
            'disaster_distance_km': self._calculate_distance(
                current_lat, current_lon,
                disaster_lat, disaster_lon
            ),
            'evacuation_priority': 'IMMEDIATE' if self._calculate_distance(
                current_lat, current_lon, disaster_lat, disaster_lon
            ) < 5 else 'HIGH',
            'tactical_guidance': f"HEADING {self._bearing_to_direction(away_bearing)} TOWARDS {safe_shelters[0]['name'] if safe_shelters else 'SAFE ZONE'}"
        }
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Haversine distance in km"""
        R = 6371
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return round(R * c, 2)
    
    def _calculate_bearing(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate bearing from point 1 to point 2 in degrees"""
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lon = math.radians(lon2 - lon1)
        
        x = math.sin(delta_lon) * math.cos(lat2_rad)
        y = math.cos(lat1_rad) * math.sin(lat2_rad) - math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(delta_lon)
        
        bearing = math.atan2(x, y)
        bearing_deg = math.degrees(bearing)
        
        return (bearing_deg + 360) % 360
    
    def _bearing_to_direction(self, bearing: float) -> str:
        """Convert bearing to cardinal direction"""
        directions = ['North', 'NE', 'East', 'SE', 'South', 'SW', 'West', 'NW']
        index = round(bearing / 45) % 8
        return directions[index]


# Singleton
route_optimizer = RouteOptimizer()


if __name__ == "__main__":
    # Test
    import asyncio
    
    async def test():
        optimizer = RouteOptimizer()
        
        # Test Mumbai to Pune
        print("🗺️ Finding multiple routes Mumbai → Pune...")
        routes = await optimizer.find_multiple_routes(
            19.0760, 72.8777,  # Mumbai
            18.5204, 73.8567,  # Pune
            alternatives=3
        )
        
        print(f"\n✅ Found {len(routes)} routes:")
        for route in routes:
            dist_km = route['distance_m'] / 1000
            time_min = route['duration_s'] / 60
            print(f"  • {route['name']}: {dist_km:.1f}km, {time_min:.0f} min ({route['strategy']})")
    
    asyncio.run(test())
