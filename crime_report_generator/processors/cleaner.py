"""
Data cleaner module for processing raw crime data.
"""

import logging
from datetime import datetime
from typing import List, Dict, Any
import re

logger = logging.getLogger(__name__)

class DataCleaner:
    """Class for cleaning and standardizing crime data."""
    
    # Valid crime types
    VALID_CRIME_TYPES = {
        'Homicide', 'Burglary', 'Theft', 'Robbery', 'Assault'
    }
    
    # Valid status values
    VALID_STATUSES = {'Open', 'Closed'}
    
    def __init__(self):
        """Initialize the data cleaner."""
        self.required_fields = {'date', 'crime_type', 'count', 'location', 'status'}
    
    def clean(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Clean and standardize a list of crime records.
        
        Args:
            data: List of crime data dictionaries
            
        Returns:
            List of cleaned crime data dictionaries
            
        Raises:
            ValueError: If required fields are missing or data is invalid
        """
        cleaned_data = []
        
        for record in data:
            # Check for required fields
            if not all(field in record for field in self.required_fields):
                raise ValueError(f"Missing required fields in record: {record}")
            
            # Clean each field
            cleaned_record = {
                'date': self._clean_date(record['date']),
                'crime_type': self._clean_crime_type(record['crime_type']),
                'count': self._clean_count(record['count']),
                'location': self._clean_location(record['location']),
                'status': self._clean_status(record['status'])
            }
            
            cleaned_data.append(cleaned_record)
        
        return cleaned_data
    
    def _clean_date(self, date_str: str) -> str:
        """Clean and standardize date format.
        
        Args:
            date_str: Date string in various formats
            
        Returns:
            Date string in YYYY-MM-DD format
        """
        try:
            # Try parsing different date formats
            for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y']:
                try:
                    date_obj = datetime.strptime(date_str, fmt)
                    return date_obj.strftime('%Y-%m-%d')
                except ValueError:
                    continue
            
            raise ValueError(f"Invalid date format: {date_str}")
            
        except Exception as e:
            logger.error(f"Error cleaning date {date_str}: {str(e)}")
            raise
    
    def _clean_crime_type(self, crime_type: str) -> str:
        """Clean and standardize crime type.
        
        Args:
            crime_type: Raw crime type string
            
        Returns:
            Standardized crime type string
        """
        # Convert to title case
        cleaned_type = crime_type.title()
        
        # Validate against known crime types
        if cleaned_type not in self.VALID_CRIME_TYPES:
            raise ValueError(f"Invalid crime type: {crime_type}")
        
        return cleaned_type
    
    def _clean_count(self, count: Any) -> int:
        """Clean and standardize count value.
        
        Args:
            count: Count value (string or int)
            
        Returns:
            Integer count value
        """
        try:
            count_int = int(count)
            if count_int <= 0:
                raise ValueError(f"Count must be positive: {count}")
            return count_int
            
        except (ValueError, TypeError) as e:
            logger.error(f"Error cleaning count {count}: {str(e)}")
            raise
    
    def _clean_location(self, location: str) -> str:
        """Clean and standardize location string.
        
        Args:
            location: Raw location string
            
        Returns:
            Standardized location string
        """
        # Convert to title case
        cleaned_location = location.title()
        
        # Remove extra whitespace
        cleaned_location = ' '.join(cleaned_location.split())
        
        # Validate format (at least one word in title case)
        if not any(word.istitle() for word in cleaned_location.split()):
            raise ValueError(f"Invalid location format: {location}")
        
        return cleaned_location
    
    def _clean_status(self, status: str) -> str:
        """Clean and standardize status value.
        
        Args:
            status: Raw status string
            
        Returns:
            Standardized status string
        """
        # Convert to title case
        cleaned_status = status.title()
        
        # Validate against known statuses
        if cleaned_status not in self.VALID_STATUSES:
            raise ValueError(f"Invalid status: {status}")
        
        return cleaned_status 
