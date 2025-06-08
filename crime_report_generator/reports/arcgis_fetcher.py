import requests
from typing import Dict, Any, List, Optional
from geopy.geocoders import Nominatim
from datetime import datetime


def get_bounding_box(zip_code: str) -> Dict[str, float]:
    """
    Get bounding box coordinates for a ZIP code using geopy.
    Returns a dict with xmin, ymin, xmax, ymax coordinates.
    """
    geolocator = Nominatim(user_agent="crime_data_fetcher")
    location = geolocator.geocode(zip_code)
    if not location:
        raise ValueError(f"Could not find location for ZIP {zip_code}")
    
    # Buffer: ~1km radius
    lat, lon = location.latitude, location.longitude
    buffer = 0.01
    return {
        "xmin": lon - buffer,
        "ymin": lat - buffer,
        "xmax": lon + buffer,
        "ymax": lat + buffer
    }


def fetch_montgomery_arcgis(zip_code: str, year: int) -> Dict[str, Any]:
    """
    Fetch crime data from Montgomery County ArcGIS REST API.
    Returns structured data including crime counts, types, and locations.
    """
    base_url = "https://www.mctx.org/arcgis/rest/services/CrimeReports/MapServer/0/query"
    
    try:
        # Get bounding box for ZIP
        bbox = get_bounding_box(zip_code)
        
        # Build query parameters
        params = {
            "where": f"ReportedYear={year}",
            "geometry": f"{bbox['xmin']},{bbox['ymin']},{bbox['xmax']},{bbox['ymax']}",
            "geometryType": "esriGeometryEnvelope",
            "inSR": "4326",
            "spatialRel": "esriSpatialRelIntersects",
            "outFields": "*",
            "returnGeometry": "false",
            "f": "json"
        }
        
        # Make request
        response = requests.get(base_url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if "error" in data:
            raise ValueError(f"ArcGIS error: {data['error'].get('message')}")
        
        # Process features
        features = data.get("features", [])
        crimes = []
        for feature in features:
            attrs = feature.get("attributes", {})
            if attrs:
                crime = {
                    "date": datetime.fromtimestamp(attrs.get("ReportedDate", 0) / 1000).strftime("%Y-%m-%d"),
                    "type": attrs.get("CrimeType", "Unknown"),
                    "location": attrs.get("Location", "Unknown"),
                    "description": attrs.get("Description", ""),
                    "status": attrs.get("Status", "Unknown")
                }
                crimes.append(crime)
        
        # Build summary
        summary = {
            "total_crimes": len(crimes),
            "crime_types": {},
            "by_month": {},
            "by_status": {}
        }
        
        for crime in crimes:
            # Count by type
            crime_type = crime["type"]
            summary["crime_types"][crime_type] = summary["crime_types"].get(crime_type, 0) + 1
            
            # Count by month
            month = crime["date"][:7]  # YYYY-MM
            summary["by_month"][month] = summary["by_month"].get(month, 0) + 1
            
            # Count by status
            status = crime["status"]
            summary["by_status"][status] = summary["by_status"].get(status, 0) + 1
        
        return {
            "zip_code": zip_code,
            "year": year,
            "source": "Montgomery County ArcGIS",
            "bounding_box": bbox,
            "total_crimes": len(crimes),
            "crimes": crimes,
            "summary": summary
        }
        
    except requests.exceptions.RequestException as e:
        return {
            "zip_code": zip_code,
            "year": year,
            "source": "Montgomery County ArcGIS",
            "error": f"Request failed: {str(e)}"
        }
    except Exception as e:
        return {
            "zip_code": zip_code,
            "year": year,
            "source": "Montgomery County ArcGIS",
            "error": f"Error: {str(e)}"
        } 
