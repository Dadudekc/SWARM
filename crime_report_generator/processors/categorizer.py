"""
Crime categorizer module for classifying crime data into standardized categories.
"""

from enum import Enum, auto
from typing import Dict, List, Set
import pandas as pd
import logging

logger = logging.getLogger(__name__)

class CrimeCategory(Enum):
    """Enumeration of crime categories."""
    VIOLENT = auto()
    PROPERTY = auto()
    DRUG = auto()
    OTHER = auto()

class CrimeCategorizer:
    """Class for categorizing crime data into standardized categories."""
    
    def __init__(self):
        """Initialize the crime categorizer with offense and keyword mappings."""
        # Offense type to category mapping
        self.offense_categories: Dict[str, CrimeCategory] = {
            # Violent crimes
            "MURDER": CrimeCategory.VIOLENT,
            "HOMICIDE": CrimeCategory.VIOLENT,
            "ASSAULT": CrimeCategory.VIOLENT,
            "BATTERY": CrimeCategory.VIOLENT,
            "ROBBERY": CrimeCategory.VIOLENT,
            
            # Property crimes
            "BURGLARY": CrimeCategory.PROPERTY,
            "THEFT": CrimeCategory.PROPERTY,
            "LARCENY": CrimeCategory.PROPERTY,
            "VANDALISM": CrimeCategory.PROPERTY,
            "ARSON": CrimeCategory.PROPERTY,
            
            # Drug crimes
            "DRUG": CrimeCategory.DRUG,
            "NARCOTICS": CrimeCategory.DRUG,
            "POSSESSION": CrimeCategory.DRUG,
        }
        
        # Description keywords to category mapping
        self.keyword_categories: Dict[str, CrimeCategory] = {
            # Violent crime keywords
            "homicide": CrimeCategory.VIOLENT,
            "murder": CrimeCategory.VIOLENT,
            "assault": CrimeCategory.VIOLENT,
            "battery": CrimeCategory.VIOLENT,
            "robbery": CrimeCategory.VIOLENT,
            "shooting": CrimeCategory.VIOLENT,
            "stabbing": CrimeCategory.VIOLENT,
            
            # Property crime keywords
            "burglary": CrimeCategory.PROPERTY,
            "theft": CrimeCategory.PROPERTY,
            "larceny": CrimeCategory.PROPERTY,
            "vandalism": CrimeCategory.PROPERTY,
            "arson": CrimeCategory.PROPERTY,
            "breaking": CrimeCategory.PROPERTY,
            "entering": CrimeCategory.PROPERTY,
            
            # Drug crime keywords
            "drug": CrimeCategory.DRUG,
            "narcotics": CrimeCategory.DRUG,
            "possession": CrimeCategory.DRUG,
            "controlled": CrimeCategory.DRUG,
            "substance": CrimeCategory.DRUG,
        }
    
    def categorize_offense(self, offense: str) -> CrimeCategory:
        """Categorize a crime based on its offense type.
        
        Args:
            offense: The offense type string
            
        Returns:
            CrimeCategory enum value
        """
        if not offense:
            return CrimeCategory.OTHER
            
        offense_upper = offense.upper()
        return self.offense_categories.get(offense_upper, CrimeCategory.OTHER)
    
    def categorize_description(self, description: str) -> CrimeCategory:
        """Categorize a crime based on its description.
        
        Args:
            description: The crime description string
            
        Returns:
            CrimeCategory enum value
        """
        if not description:
            return CrimeCategory.OTHER
            
        description_lower = description.lower()
        
        # Check each keyword in the description
        for keyword, category in self.keyword_categories.items():
            if keyword in description_lower:
                return category
        
        return CrimeCategory.OTHER
    
    def categorize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Categorize all crimes in a DataFrame.
        
        Args:
            df: DataFrame containing 'offense' and 'description' columns
            
        Returns:
            DataFrame with added 'category' column
            
        Raises:
            ValueError: If required columns are missing
        """
        if df.empty:
            return pd.DataFrame(columns=["offense", "description", "category"])
        
        # Validate required columns
        required_columns = {"offense", "description"}
        missing_columns = required_columns - set(df.columns)
        if missing_columns:
            raise ValueError(f"Required column{'' if len(missing_columns) == 1 else 's'} "
                           f"'{', '.join(missing_columns)}' not found")
        
        try:
            # Create a copy to avoid modifying the original
            result = df.copy()
            
            # Apply categorization
            result["category"] = result.apply(
                lambda row: self._categorize_row(row["offense"], row["description"]),
                axis=1
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error categorizing DataFrame: {str(e)}")
            raise
    
    def _categorize_row(self, offense: str, description: str) -> CrimeCategory:
        """Categorize a single crime record.
        
        Args:
            offense: The offense type
            description: The crime description
            
        Returns:
            CrimeCategory enum value
        """
        # Try offense first, then fall back to description
        category = self.categorize_offense(offense)
        if category == CrimeCategory.OTHER:
            category = self.categorize_description(description)
        return category

    def categorize_crime(self, offense: str, description: str) -> CrimeCategory:
        """Alias for _categorize_row to maintain backward compatibility.
        
        Args:
            offense: The offense type
            description: The crime description
            
        Returns:
            CrimeCategory enum value
        """
        return self._categorize_row(offense, description) 
