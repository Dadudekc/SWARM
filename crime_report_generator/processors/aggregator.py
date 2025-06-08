"""
Data aggregator module for processing crime statistics.

This module provides functions for aggregating and analyzing crime data,
including aggregation by type, district, and location-based analysis.
"""

from typing import List, Tuple, Optional
import pandas as pd
import logging

logger = logging.getLogger(__name__)

def aggregate_by_type(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate crime data by category.
    
    Args:
        df: DataFrame containing crime data with 'crime_category' column
        
    Returns:
        DataFrame with columns 'category' and 'count', sorted by count in descending order
        
    Raises:
        ValueError: If required column 'crime_category' is missing
    """
    if df.empty:
        return pd.DataFrame(columns=["category", "count"])
    
    if "crime_category" not in df.columns:
        raise ValueError("Required column 'crime_category' not found in DataFrame")
    
    try:
        result = (df.groupby("crime_category")
                 .size()
                 .reset_index(name="count")
                 .rename(columns={"crime_category": "category"}))
        return result.sort_values("count", ascending=False)
    except Exception as e:
        logger.error(f"Error aggregating by type: {str(e)}")
        raise

def aggregate_by_district(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate crime data by district.
    
    Args:
        df: DataFrame containing crime data with 'district' column
        
    Returns:
        DataFrame with columns 'district' and 'count', sorted by count in descending order
        
    Raises:
        ValueError: If required column 'district' is missing
    """
    if df.empty:
        return pd.DataFrame(columns=["district", "count"])
    
    if "district" not in df.columns:
        raise ValueError("Required column 'district' not found in DataFrame")
    
    try:
        result = (df.groupby("district")
                 .size()
                 .reset_index(name="count"))
        return result.sort_values("count", ascending=False)
    except Exception as e:
        logger.error(f"Error aggregating by district: {str(e)}")
        raise

def top_locations(
    df: pd.DataFrame,
    n: int = 5,
    ascending: bool = False,
    min_count: Optional[int] = None
) -> List[Tuple[str, int]]:
    """Find top N locations by crime count.
    
    Args:
        df: DataFrame containing crime data with 'location' column
        n: Number of top locations to return
        ascending: If True, return locations with lowest crime counts
        min_count: Optional minimum count threshold for locations
        
    Returns:
        List of (location, count) tuples, sorted by count
        
    Raises:
        ValueError: If required column 'location' is missing
    """
    if df.empty:
        return []
    
    if "location" not in df.columns:
        raise ValueError("Required column 'location' not found in DataFrame")
    
    try:
        # Group by location and count occurrences
        location_counts = df.groupby("location").size()
        
        # Apply minimum count filter if specified
        if min_count is not None:
            location_counts = location_counts[location_counts >= min_count]
        
        # Sort and get top N
        sorted_locations = location_counts.sort_values(ascending=ascending)
        return list(zip(sorted_locations.index[:n], sorted_locations.values[:n]))
    except Exception as e:
        logger.error(f"Error finding top locations: {str(e)}")
        raise 
