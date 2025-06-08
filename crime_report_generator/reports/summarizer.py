from typing import Dict, Any, List
from datetime import datetime


def normalize_crime_types(crime_type: str) -> str:
    """Normalize crime type names across sources."""
    crime_type = crime_type.lower()
    if "violent" in crime_type or "assault" in crime_type:
        return "Violent Crime"
    elif "property" in crime_type or "theft" in crime_type or "burglary" in crime_type:
        return "Property Crime"
    elif "drug" in crime_type:
        return "Drug Crime"
    elif "traffic" in crime_type:
        return "Traffic Violation"
    else:
        return "Other Crime"


def summarize_arcgis_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Summarize ArcGIS data into key metrics."""
    if "error" in data:
        return {"error": data["error"]}
    
    summary = {
        "total_crimes": data.get("total_crimes", 0),
        "crime_categories": {
            "violent": 0,
            "property": 0,
            "drug": 0,
            "traffic": 0,
            "other": 0
        },
        "monthly_trend": {},
        "status_breakdown": {},
        "key_locations": []
    }
    
    # Process crimes
    for crime in data.get("crimes", []):
        # Categorize crime type
        crime_type = normalize_crime_types(crime["type"])
        if "violent" in crime_type.lower():
            summary["crime_categories"]["violent"] += 1
        elif "property" in crime_type.lower():
            summary["crime_categories"]["property"] += 1
        elif "drug" in crime_type.lower():
            summary["crime_categories"]["drug"] += 1
        elif "traffic" in crime_type.lower():
            summary["crime_categories"]["traffic"] += 1
        else:
            summary["crime_categories"]["other"] += 1
        
        # Track monthly trend
        month = crime["date"][:7]  # YYYY-MM
        summary["monthly_trend"][month] = summary["monthly_trend"].get(month, 0) + 1
        
        # Track status
        status = crime["status"]
        summary["status_breakdown"][status] = summary["status_breakdown"].get(status, 0) + 1
        
        # Track locations (top 5)
        if len(summary["key_locations"]) < 5:
            location = crime["location"]
            if location and location not in summary["key_locations"]:
                summary["key_locations"].append(location)
    
    return summary


def summarize_crimegrade_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Summarize CrimeGrade.org data into key metrics."""
    if "error" in data:
        return {"error": data["error"]}
    
    summary = {
        "safety_grade": data.get("safety_grade"),
        "crime_rate": data.get("crime_rate_per_1000"),
        "summary_stats": data.get("summary_stats", {}),
        "neighborhoods": data.get("neighborhoods", []),
        "crime_types": data.get("crime_types", {}),
        "risk_assessment": {}
    }
    
    # Process summary stats into risk assessment
    stats = data.get("summary_stats", {})
    for key, value in stats.items():
        if "violent" in key.lower():
            summary["risk_assessment"]["violent_crime"] = value
        elif "property" in key.lower():
            summary["risk_assessment"]["property_crime"] = value
        elif "safety" in key.lower():
            summary["risk_assessment"]["overall_safety"] = value
    
    # Add neighborhood safety summary
    if summary["neighborhoods"]:
        safe_neighborhoods = sum(1 for n in summary["neighborhoods"] if n["grade"] in ["A", "A+", "A-"])
        total_neighborhoods = len(summary["neighborhoods"])
        summary["neighborhood_safety"] = {
            "safe_count": safe_neighborhoods,
            "total_count": total_neighborhoods,
            "safe_percentage": (safe_neighborhoods / total_neighborhoods * 100) if total_neighborhoods > 0 else 0
        }
    
    # Add crime type summary
    if summary["crime_types"]:
        violent_crimes = sum(1 for t in summary["crime_types"] if "violent" in t.lower())
        property_crimes = sum(1 for t in summary["crime_types"] if "property" in t.lower())
        summary["crime_type_summary"] = {
            "violent_count": violent_crimes,
            "property_count": property_crimes,
            "total_types": len(summary["crime_types"])
        }
    
    return summary


def compare_sources(arcgis_summary: Dict[str, Any], crimegrade_summary: Dict[str, Any]) -> Dict[str, Any]:
    """Compare and highlight differences between ArcGIS and CrimeGrade data."""
    comparison = {
        "data_quality": {
            "arcgis_complete": "error" not in arcgis_summary,
            "crimegrade_complete": "error" not in crimegrade_summary
        },
        "key_differences": [],
        "recommendations": []
    }
    
    # Compare total crime counts if available
    if "total_crimes" in arcgis_summary and "crime_rate" in crimegrade_summary:
        arcgis_total = arcgis_summary["total_crimes"]
        crimegrade_rate = float(crimegrade_summary["crime_rate"] or 0)
        
        # Add comparison note
        comparison["key_differences"].append({
            "metric": "Total Crimes",
            "arcgis": arcgis_total,
            "crimegrade": f"{crimegrade_rate} per 1,000 residents"
        })
    
    # Compare crime categories
    if "crime_categories" in arcgis_summary:
        violent_arcgis = arcgis_summary["crime_categories"]["violent"]
        property_arcgis = arcgis_summary["crime_categories"]["property"]
        
        if "risk_assessment" in crimegrade_summary:
            violent_crimegrade = crimegrade_summary["risk_assessment"].get("violent_crime")
            property_crimegrade = crimegrade_summary["risk_assessment"].get("property_crime")
            
            if violent_crimegrade and property_crimegrade:
                comparison["key_differences"].append({
                    "metric": "Crime Distribution",
                    "arcgis": f"Violent: {violent_arcgis}, Property: {property_arcgis}",
                    "crimegrade": f"Violent: {violent_crimegrade}, Property: {property_crimegrade}"
                })
    
    # Add recommendations based on data quality
    if not comparison["data_quality"]["arcgis_complete"]:
        comparison["recommendations"].append("Consider using CrimeGrade data as primary source")
    if not comparison["data_quality"]["crimegrade_complete"]:
        comparison["recommendations"].append("Consider using ArcGIS data as primary source")
    if comparison["data_quality"]["arcgis_complete"] and comparison["data_quality"]["crimegrade_complete"]:
        comparison["recommendations"].append("Use both sources for comprehensive analysis")
    
    return comparison 
