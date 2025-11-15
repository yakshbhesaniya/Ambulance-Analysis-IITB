# backend/ors_client.py
import requests
import json
import config

BASE_URL = "https://api.openrouteservice.org"

def get_route(start, via, end, profile="driving-car"):
    """
    start, via, end: tuples (lng, lat)
    returns: dict with 'geojson', 'summary' (distance m, duration s)
    """
    url = f"{BASE_URL}/v2/directions/{profile}/geojson"
    coords = [ [start[0], start[1]], [via[0], via[1]], [end[0], end[1]] ]
    body = {
        "coordinates": coords,
        "instructions": False,
        # Use "shortest" preference to get more direct routes through campus
        # instead of fastest routes that might go around the lake
        "preference": "shortest"  # Options: "fastest" (default), "shortest", "recommended"
    }
    
    # Add radiuses parameter to allow finding nearest road within specified radius
    # Format: array of radius values in meters, one per coordinate
    # -1 means unlimited search (find nearest road regardless of distance)
    # Using -1 to ensure we can find roads even if coordinates are inside buildings
    body["radiuses"] = [-1, -1, -1]  # Unlimited search radius for each coordinate
    headers = {
        "Authorization": config.ORS_API_KEY,
        "Content-Type": "application/json"
    }
    
    try:
        print(f"Requesting route from {start} via {via} to {end}")
        print(f"Using radiuses: unlimited (-1) for each coordinate to find nearest roads")
        resp = requests.post(url, json=body, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        
        # Validate response
        if not data:
            raise ValueError("Empty response from ORS route API")
        
        # extract route summary if present
        summary = {}
        features = data.get("features", [])
        if not features or len(features) == 0:
            raise ValueError("No route features in response")
        
        props = features[0].get("properties", {})
        seg_summary = props.get("summary", {})
        summary = {
            "distance_m": seg_summary.get("distance"),
            "duration_s": seg_summary.get("duration")
        }
        
        print(f"Route generated: {summary.get('distance_m', 0)/1000:.2f} km, {summary.get('duration_s', 0)/60:.1f} min")
        return {"geojson": data, "summary": summary}
        
    except requests.exceptions.HTTPError as e:
        error_detail = ""
        try:
            error_detail = e.response.json()
        except:
            error_detail = e.response.text
        error_msg = f"ORS API HTTP error {e.response.status_code}: {error_detail}"
        print(f"Route error: {error_msg}")
        raise Exception(error_msg)
    except requests.exceptions.RequestException as e:
        error_msg = f"ORS API request failed: {str(e)}"
        print(f"Route error: {error_msg}")
        raise Exception(error_msg)
    except Exception as e:
        error_msg = f"Route processing failed: {str(e)}"
        print(f"Route error: {error_msg}")
        raise Exception(error_msg)

def get_isochrones(center, ranges_minutes=(1,2,3,5), bbox=None):
    """
    Get isochrones from center point.
    center: (longitude, latitude) tuple
    ranges_minutes: tuple of time ranges in minutes
    bbox: optional bounding box [min_lon, min_lat, max_lon, max_lat] to limit isochrones
    Note: OpenRouteService API may not support bbox parameter directly
    """
    url = f"{BASE_URL}/v2/isochrones/driving-car"
    body = {
        "locations": [[center[0], center[1]]],
        "range": [r*60 for r in ranges_minutes],
        "units": "m"
    }
    
    # Note: OpenRouteService v2 isochrones API may not support bbox parameter
    # We'll filter results after receiving them if needed
    # if bbox:
    #     body["bbox"] = bbox  # [min_lon, min_lat, max_lon, max_lat]
    
    headers = {
        "Authorization": config.ORS_API_KEY,
        "Content-Type": "application/json"
    }
    
    try:
        resp = requests.post(url, json=body, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        
        # Validate response structure
        if not data:
            raise ValueError("Empty response from isochrones API")
        
        if "features" not in data:
            # Log the actual response for debugging
            print(f"Unexpected isochrones response structure: {data}")
            raise ValueError(f"Invalid isochrones response: missing features. Response: {data}")
        
        # Clip isochrones to IITB campus boundary using shapely
        if bbox and data.get("features"):
            try:
                from shapely.geometry import shape, Polygon, box
                from shapely.ops import unary_union
                import json
                
                # Create campus boundary polygon from bbox
                # bbox format: [min_lon, min_lat, max_lon, max_lat]
                min_lon, min_lat, max_lon, max_lat = bbox
                campus_boundary = box(min_lon, min_lat, max_lon, max_lat)
                
                clipped_features = []
                for feature in data["features"]:
                    try:
                        # Convert GeoJSON feature to Shapely geometry
                        geom = shape(feature["geometry"])
                        
                        # Clip geometry to campus boundary
                        clipped_geom = geom.intersection(campus_boundary)
                        
                        # Only add if intersection produces a valid geometry
                        if not clipped_geom.is_empty and clipped_geom.area > 0:
                            # Convert back to GeoJSON
                            clipped_feature = {
                                "type": "Feature",
                                "properties": feature.get("properties", {}),
                                "geometry": json.loads(json.dumps(clipped_geom.__geo_interface__))
                            }
                            clipped_features.append(clipped_feature)
                    except Exception as e:
                        print(f"Error clipping feature: {e}")
                        # If clipping fails, check if original is within bbox
                        geom = feature.get("geometry", {})
                        coords = geom.get("coordinates", [])
                        if coords and len(coords) > 0:
                            # Simple bbox check as fallback
                            if isinstance(coords[0][0], list):
                                first_point = coords[0][0]
                            else:
                                first_point = coords[0]
                            lon, lat = first_point[0], first_point[1]
                            if min_lon <= lon <= max_lon and min_lat <= lat <= max_lat:
                                clipped_features.append(feature)
                
                if clipped_features:
                    data["features"] = clipped_features
                    print(f"Clipped {len(clipped_features)} isochrone features to campus boundary")
                else:
                    print("Warning: No isochrone features after clipping, returning original")
            except ImportError:
                print("Warning: shapely not available, using simple bbox filtering")
                # Fallback to simple bbox check
                filtered_features = []
                min_lon, min_lat, max_lon, max_lat = bbox
                for feature in data["features"]:
                    geom = feature.get("geometry", {})
                    coords = geom.get("coordinates", [])
                    if coords and len(coords) > 0:
                        if isinstance(coords[0][0], list):
                            first_point = coords[0][0]
                        else:
                            first_point = coords[0]
                        lon, lat = first_point[0], first_point[1]
                        if min_lon <= lon <= max_lon and min_lat <= lat <= max_lat:
                            filtered_features.append(feature)
                if filtered_features:
                    data["features"] = filtered_features
        
        return data
        
    except requests.exceptions.HTTPError as e:
        error_detail = ""
        try:
            error_detail = e.response.json()
        except:
            error_detail = e.response.text
        raise Exception(f"ORS API HTTP error: {e.response.status_code} - {error_detail}")
    except requests.exceptions.RequestException as e:
        raise Exception(f"ORS API request failed: {str(e)}")

def geocode_place(text, country="IN", size=1):
    """
    Fallback geocoder using ORS /geocode/search
    returns first (lng, lat) tuple or None
    """
    url = f"{BASE_URL}/geocode/search"
    params = {
        "api_key": config.ORS_API_KEY,
        "text": text,
        "size": size,
        "boundary.country": country
    }
    resp = requests.get(url, params=params, timeout=20)
    resp.raise_for_status()
    data = resp.json()
    features = data.get("features") or []
    if not features:
        return None
    # coordinates in features[0].geometry.coordinates = [lng, lat]
    coords = features[0].get("geometry", {}).get("coordinates")
    if coords and len(coords) >= 2:
        return (coords[0], coords[1])
    return None
