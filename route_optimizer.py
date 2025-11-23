"""
Route Optimizer Service with 3-Tier Fallback System
Implements automatic fallback between routing services:
1. OpenRouteService (ORS) - Most accurate, requires API key
2. OSRM - Free public service, no API key needed
3. Haversine - Straight-line calculation, always available
"""

import requests
import math
import logging
from typing import Dict, List, Tuple, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def calculate_route(start_coords: List[float], end_coords: List[float], api_key: Optional[str] = None) -> Dict:
    """
    Calculate route between two points with automatic fallback.
    
    Args:
        start_coords: [lon, lat] of starting point
        end_coords: [lon, lat] of ending point
        api_key: Optional OpenRouteService API key
    
    Returns:
        Dict with keys: distance (km), duration (minutes), geometry (list of [lat, lon])
    """
    # Try OpenRouteService first (if API key available)
    if api_key:
        try:
            logger.info("Attempting route calculation with OpenRouteService...")
            return _try_openrouteservice(start_coords, end_coords, api_key)
        except Exception as e:
            logger.warning(f"OpenRouteService failed: {e}. Falling back to OSRM...")
    
    # Try OSRM as fallback
    try:
        logger.info("Attempting route calculation with OSRM...")
        return _try_osrm(start_coords, end_coords)
    except Exception as e:
        logger.warning(f"OSRM failed: {e}. Falling back to Haversine calculation...")
    
    # Use Haversine as last resort
    logger.info("Using Haversine straight-line calculation...")
    return _calculate_haversine(start_coords, end_coords)


def _try_openrouteservice(start_coords: List[float], end_coords: List[float], api_key: str) -> Dict:
    """
    Calculate route using OpenRouteService API.
    
    Args:
        start_coords: [lon, lat] of starting point
        end_coords: [lon, lat] of ending point
        api_key: OpenRouteService API key
    
    Returns:
        Dict with distance, duration, and geometry
    
    Raises:
        Exception: If API call fails
    """
    url = 'https://api.openrouteservice.org/v2/directions/driving-car'
    
    headers = {
        'Authorization': api_key,
        'Content-Type': 'application/json'
    }
    
    body = {
        'coordinates': [start_coords, end_coords]
    }
    
    response = requests.post(url, json=body, headers=headers, timeout=10)
    
    if response.status_code == 200:
        data = response.json()
        route = data['routes'][0]
        
        # Convert geometry from lon,lat to lat,lon
        geometry = []
        for coord in route['geometry']['coordinates']:
            geometry.append([coord[1], coord[0]])  # Convert lon,lat to lat,lon
        
        logger.info("✓ OpenRouteService route calculated successfully")
        return {
            'distance': route['summary']['distance'] / 1000,  # Convert to km
            'duration': route['summary']['duration'] / 60,  # Convert to minutes
            'geometry': geometry,
            'source': 'OpenRouteService'
        }
    else:
        raise Exception(f"ORS API error: {response.status_code} - {response.text}")


def _try_osrm(start_coords: List[float], end_coords: List[float]) -> Dict:
    """
    Calculate route using OSRM public API.
    
    Args:
        start_coords: [lon, lat] of starting point
        end_coords: [lon, lat] of ending point
    
    Returns:
        Dict with distance, duration, and geometry
    
    Raises:
        Exception: If API call fails
    """
    # OSRM format: /route/v1/{profile}/{coordinates}
    url = f"https://router.project-osrm.org/route/v1/driving/{start_coords[0]},{start_coords[1]};{end_coords[0]},{end_coords[1]}"
    
    params = {
        'overview': 'full',
        'geometries': 'geojson'
    }
    
    response = requests.get(url, params=params, timeout=10)
    
    if response.status_code == 200:
        data = response.json()
        
        if data['code'] == 'Ok' and data['routes']:
            route = data['routes'][0]
            
            # Convert geometry from lon,lat to lat,lon
            geometry = []
            for coord in route['geometry']['coordinates']:
                geometry.append([coord[1], coord[0]])  # Convert lon,lat to lat,lon
            
            logger.info("✓ OSRM route calculated successfully")
            return {
                'distance': route['distance'] / 1000,  # Convert to km
                'duration': route['duration'] / 60,  # Convert to minutes
                'geometry': geometry,
                'source': 'OSRM'
            }
        else:
            raise Exception(f"OSRM returned no routes: {data.get('code', 'Unknown error')}")
    else:
        raise Exception(f"OSRM API error: {response.status_code}")


def _calculate_haversine(start_coords: List[float], end_coords: List[float]) -> Dict:
    """
    Calculate straight-line distance and estimated duration using Haversine formula.
    
    Args:
        start_coords: [lon, lat] of starting point
        end_coords: [lon, lat] of ending point
    
    Returns:
        Dict with distance, duration, and simple geometry
    """
    # Extract coordinates
    lon1, lat1 = start_coords
    lon2, lat2 = end_coords
    
    # Haversine formula
    R = 6371  # Earth's radius in kilometers
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = math.sin(delta_lat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    distance = R * c  # Distance in km
    
    # Assume average speed of 30 km/h for duration estimation
    AVERAGE_SPEED_KMH = 30
    duration = (distance / AVERAGE_SPEED_KMH) * 60  # Duration in minutes
    
    # Create simple straight-line geometry
    geometry = [
        [lat1, lon1],  # Start point
        [lat2, lon2]   # End point
    ]
    
    logger.info("✓ Haversine calculation completed (straight-line distance)")
    return {
        'distance': distance,
        'duration': duration,
        'geometry': geometry,
        'source': 'Haversine'
    }
