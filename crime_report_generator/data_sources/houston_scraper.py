"""
Houston Police Department crime data scraper.
Scrapes monthly Group A/B crime statistics from the HPD website.
"""

import os
import logging
import requests
from datetime import datetime
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
import pandas as pd

logger = logging.getLogger(__name__)

class HoustonScraper:
    """Scraper for Houston Police Department crime data."""
    
    BASE_URL = "https://www.houstontx.gov/police/cs/stats2.htm"
    DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
    
    def __init__(self):
        """Initialize the Houston scraper."""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
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
        logger.info(f"Collecting Houston crime data for {month}/{year}")
        
        try:
            # Get the webpage content
            response = self.session.get(self.BASE_URL)
            response.raise_for_status()
            
            # Parse the HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find the relevant table (this will need to be updated based on actual HTML structure)
            table = soup.find('table', {'class': 'crime-stats'})
            if not table:
                raise ValueError("Could not find crime statistics table")
            
            # Extract data from table
            data = []
            rows = table.find_all('tr')[1:]  # Skip header row
            
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 4:  # Ensure we have enough columns
                    crime_data = {
                        'date': f"{year}-{month}-01",  # Use first day of month
                        'crime_type': cols[0].text.strip(),
                        'count': int(cols[1].text.strip()),
                        'location': cols[2].text.strip(),
                        'status': cols[3].text.strip()
                    }
                    data.append(crime_data)
            
            # Save raw data to CSV
            self._save_raw_data(data, month, year)
            
            logger.info(f"Successfully collected {len(data)} crime records for Houston")
            return data
            
        except Exception as e:
            logger.error(f"Error collecting Houston crime data: {str(e)}")
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
            filename = f"houston_crime_{year}_{month}.csv"
            filepath = os.path.join(self.DATA_DIR, filename)
            
            # Save to CSV
            df.to_csv(filepath, index=False)
            logger.info(f"Saved raw Houston data to {filepath}")
            
        except Exception as e:
            logger.error(f"Error saving Houston raw data: {str(e)}")
            raise
    
    def _parse_crime_type(self, crime_type: str) -> Dict[str, str]:
        """Parse crime type into category and subcategory.
        
        Args:
            crime_type: Raw crime type string
            
        Returns:
            Dictionary with category and subcategory
        """
        # This mapping will need to be updated based on actual HPD crime categories
        crime_categories = {
            'Homicide': 'Violent',
            'Rape': 'Violent',
            'Robbery': 'Violent',
            'Aggravated Assault': 'Violent',
            'Burglary': 'Property',
            'Larceny': 'Property',
            'Motor Vehicle Theft': 'Property',
            'Arson': 'Property'
        }
        
        category = crime_categories.get(crime_type, 'Other')
        return {
            'category': category,
            'subcategory': crime_type
        } 