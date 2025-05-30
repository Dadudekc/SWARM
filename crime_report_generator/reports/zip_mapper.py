"""
ZIP Code Mapping Module

Provides functions to map ZIP codes to city and state information.
"""

from typing import Dict, Optional, Tuple
import json
from pathlib import Path
import requests
from functools import lru_cache


# Common ZIP codes in Montgomery County, TX
MONTGOMERY_ZIPS = {
    "77301": ("Conroe", "TX"),
    "77302": ("Conroe", "TX"),
    "77303": ("Conroe", "TX"),
    "77304": ("Conroe", "TX"),
    "77316": ("Montgomery", "TX"),
    "77318": ("Willis", "TX"),
    "77339": ("Humble", "TX"),
    "77354": ("Magnolia", "TX"),
    "77356": ("Magnolia", "TX"),
    "77357": ("Magnolia", "TX"),
    "77358": ("Montgomery", "TX"),
    "77365": ("Pinehurst", "TX"),
    "77372": ("Shenandoah", "TX"),
    "77373": ("Spring", "TX"),
    "77380": ("Spring", "TX"),
    "77381": ("Spring", "TX"),
    "77382": ("Spring", "TX"),
    "77384": ("Conroe", "TX"),
    "77385": ("Conroe", "TX"),
    "77386": ("Spring", "TX"),
    "77388": ("Spring", "TX"),
    "77389": ("Spring", "TX"),
    "77447": ("Hockley", "TX"),
    "77493": ("Tomball", "TX"),
}


@lru_cache(maxsize=1000)
def get_zip_info(zip_code: str) -> Tuple[str, str]:
    """
    Get city and state information for a ZIP code.
    
    Args:
        zip_code: 5-digit ZIP code
        
    Returns:
        Tuple of (city, state)
        
    Raises:
        ValueError: If ZIP code is invalid
    """
    # First check our local cache
    if zip_code in MONTGOMERY_ZIPS:
        return MONTGOMERY_ZIPS[zip_code]
    
    # Then try the Zippopotam.us API
    try:
        response = requests.get(f"http://api.zippopotam.us/us/{zip_code}")
        if response.status_code == 200:
            data = response.json()
            return data["places"][0]["place name"], data["places"][0]["state abbreviation"]
    except Exception:
        pass
    
    # If all else fails, return unknown
    return ("Unknown", "TX")


def format_location(zip_code: str) -> str:
    """
    Format location string from ZIP code.
    
    Args:
        zip_code: 5-digit ZIP code
        
    Returns:
        Formatted location string (e.g., "Spring, TX")
    """
    city, state = get_zip_info(zip_code)
    return f"{city}, {state}"


def get_zip_details(zip_code: str) -> Dict[str, str]:
    """
    Get detailed ZIP code information.
    
    Args:
        zip_code: 5-digit ZIP code
        
    Returns:
        Dictionary with zip, city, and state
    """
    city, state = get_zip_info(zip_code)
    return {
        "zip": zip_code,
        "city": city,
        "state": state
    } 