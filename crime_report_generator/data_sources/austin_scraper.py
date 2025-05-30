"""
Austin Police Department crime data scraper.
Queries the Austin Open Data Portal for crime statistics.
"""

import os
import logging
import requests
from datetime import datetime
from typing import Dict, List, Optional
import pandas as pd
import sodapy

logger = logging.getLogger(__name__)

class AustinScraper:
    """Scraper for Austin Police Department crime data."""
    
    # Austin Open Data Portal dataset ID for APD crime data
    DATASET_ID = "7g8v-xxte"  # This is a placeholder - need to verify actual dataset ID
    DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
    
    def __init__(self):
        """Initialize the Austin scraper."""
        # Initialize Socrata client
        self.client = sodapy.Socrata(
            "data.austintexas.gov",
            None  # No app token required for public data
        )
        
        # Create data directory if it doesn't exist
        os.makedirs(self.DATA_DIR, exist_ok=True)
    
    def collect_data(self, month: str, year: int) -> List[Dict]:
        """Collect crime data for the specified month and year.
        
        Args:
            month: Month to collect data for (e.g., '01' for January)
            year: Year to collect data for (e.g., 2024)
            
        Returns:
            List of dictionaries containing crime data
        """
        logger.info(f"Collecting Austin crime data for {month}/{year}")
        
        try:
            # Construct date range for query
            start_date = f"{year}-{month}-01T00:00:00.000"
            if month == "12":
                end_date = f"{int(year) + 1}-01-01T00:00:00.000"
            else:
                next_month = str(int(month) + 1).zfill(2)
                end_date = f"{year}-{next_month}-01T00:00:00.000"
            
            # Query the dataset
            query = f"""
                SELECT 
                    occurred_date,
                    crime_type,
                    location,
                    latitude,
                    longitude,
                    clearance_status
                WHERE 
                    occurred_date >= '{start_date}'
                    AND occurred_date < '{end_date}'
                LIMIT 100000
            """
            
            results = self.client.get(self.DATASET_ID, query=query)
            
            # Transform results into our standard format
            data = []
            for record in results:
                crime_data = {
                    'date': record['occurred_date'].split('T')[0],
                    'crime_type': record['crime_type'],
                    'count': 1,  # Each record is one incident
                    'location': record['location'],
                    'latitude': record.get('latitude'),
                    'longitude': record.get('longitude'),
                    'status': record['clearance_status']
                }
                data.append(crime_data)
            
            # Save raw data to CSV
            self._save_raw_data(data, month, year)
            
            logger.info(f"Successfully collected {len(data)} crime records for Austin")
            return data
            
        except Exception as e:
            logger.error(f"Error collecting Austin crime data: {str(e)}")
            raise
    
    def _save_raw_data(self, data: List[Dict], month: str, year: int) -> None:
        """Save raw data to CSV file.
        
        Args:
            data: List of crime data dictionaries
            month: Month of the data
            year: Year of the data
        """
        try:
            # Convert to DataFrame
            df = pd.DataFrame(data)
            
            # Create filename
            filename = f"austin_crime_{year}_{month}.csv"
            filepath = os.path.join(self.DATA_DIR, filename)
            
            # Save to CSV
            df.to_csv(filepath, index=False)
            logger.info(f"Saved raw Austin data to {filepath}")
            
        except Exception as e:
            logger.error(f"Error saving Austin raw data: {str(e)}")
            raise
    
    def _parse_crime_type(self, crime_type: str) -> Dict[str, str]:
        """Parse crime type into category and subcategory.
        
        Args:
            crime_type: Raw crime type string
            
        Returns:
            Dictionary with category and subcategory
        """
        # This mapping will need to be updated based on actual APD crime categories
        crime_categories = {
            'Murder': 'Violent',
            'Rape': 'Violent',
            'Robbery': 'Violent',
            'Aggravated Assault': 'Violent',
            'Burglary': 'Property',
            'Theft': 'Property',
            'Auto Theft': 'Property',
            'Arson': 'Property',
            'Drug Violations': 'Drug',
            'Public Intoxication': 'Public Order',
            'Disorderly Conduct': 'Public Order'
        }
        
        category = crime_categories.get(crime_type, 'Other')
        return {
            'category': category,
            'subcategory': crime_type
        } 