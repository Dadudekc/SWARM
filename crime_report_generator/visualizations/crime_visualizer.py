"""
Crime visualization module for generating various crime data visualizations.
"""

import os
from typing import Dict, Optional
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class CrimeVisualizer:
    """Class for generating crime data visualizations."""
    
    def __init__(self):
        """Initialize the crime visualizer with default styling."""
        # Set default style
        plt.style.use('seaborn-v0_8')
        self.default_style = {
            "figure.figsize": (10, 6),
            "axes.titlesize": 14,
            "axes.labelsize": 12,
            "xtick.labelsize": 10,
            "ytick.labelsize": 10
        }
    
    def create_category_pie_chart(self, df: pd.DataFrame, style: Optional[Dict] = None) -> plt.Figure:
        """Create a pie chart showing crime distribution by category.
        
        Args:
            df: DataFrame containing crime data
            style: Optional dictionary of matplotlib style parameters
            
        Returns:
            matplotlib Figure object
            
        Raises:
            ValueError: If DataFrame is empty or missing required columns
        """
        self._validate_dataframe(df, required_columns=["category"])
        
        # Apply custom style if provided
        if style:
            plt.rcParams.update(style)
        else:
            plt.rcParams.update(self.default_style)
        
        # Create figure
        fig, ax = plt.subplots()
        
        # Convert category to string for plotting
        category_counts = df["category"].apply(lambda x: x.name if hasattr(x, "name") else str(x)).value_counts()
        
        # Create pie chart
        ax.pie(
            category_counts.values,
            labels=category_counts.index,
            autopct='%1.1f%%',
            startangle=90
        )
        ax.set_title("Crime Distribution by Category")
        
        return fig
    
    def create_trend_line_chart(self, df: pd.DataFrame, style: Optional[Dict] = None) -> plt.Figure:
        """Create a line chart showing crime trends over time.
        
        Args:
            df: DataFrame containing crime data
            style: Optional dictionary of matplotlib style parameters
            
        Returns:
            matplotlib Figure object
            
        Raises:
            ValueError: If DataFrame is empty or missing required columns
        """
        self._validate_dataframe(df, required_columns=["date"])
        
        # Apply custom style if provided
        if style:
            plt.rcParams.update(style)
        else:
            plt.rcParams.update(self.default_style)
        
        # Create figure
        fig, ax = plt.subplots()
        
        # Convert date column to datetime if needed
        if not pd.api.types.is_datetime64_any_dtype(df["date"]):
            df["date"] = pd.to_datetime(df["date"])
        
        # Group by date and count crimes
        daily_counts = df.groupby("date").size()
        
        # Create line plot
        ax.plot(daily_counts.index, daily_counts.values, marker='o')
        ax.set_title("Crime Trends Over Time")
        ax.set_xlabel("Date")
        ax.set_ylabel("Number of Crimes")
        plt.xticks(rotation=45)
        
        return fig
    
    def create_location_bar_chart(self, df: pd.DataFrame, style: Optional[Dict] = None) -> plt.Figure:
        """Create a bar chart showing crime distribution by location.
        
        Args:
            df: DataFrame containing crime data
            style: Optional dictionary of matplotlib style parameters
            
        Returns:
            matplotlib Figure object
            
        Raises:
            ValueError: If DataFrame is empty or missing required columns
        """
        self._validate_dataframe(df, required_columns=["location"])
        
        # Apply custom style if provided
        if style:
            plt.rcParams.update(style)
        else:
            plt.rcParams.update(self.default_style)
        
        # Create figure
        fig, ax = plt.subplots()
        
        # Count crimes by location
        location_counts = df["location"].value_counts()
        
        # Create bar plot
        ax.bar(location_counts.index, location_counts.values)
        ax.set_title("Crime Distribution by Location")
        ax.set_xlabel("Location")
        ax.set_ylabel("Number of Crimes")
        plt.xticks(rotation=45)
        
        return fig
    
    def create_category_trend_chart(self, df: pd.DataFrame, style: Optional[Dict] = None) -> plt.Figure:
        """Create a line chart showing crime trends by category.
        
        Args:
            df: DataFrame containing crime data
            style: Optional dictionary of matplotlib style parameters
            
        Returns:
            matplotlib Figure object
            
        Raises:
            ValueError: If DataFrame is empty or missing required columns
        """
        self._validate_dataframe(df, required_columns=["date", "category"])
        
        # Apply custom style if provided
        if style:
            plt.rcParams.update(style)
        else:
            plt.rcParams.update(self.default_style)
        
        # Create figure
        fig, ax = plt.subplots()
        
        # Convert date column to datetime if needed
        if not pd.api.types.is_datetime64_any_dtype(df["date"]):
            df["date"] = pd.to_datetime(df["date"])
        
        # Convert category to string for grouping
        df = df.copy()
        df["category"] = df["category"].apply(lambda x: x.name if hasattr(x, "name") else str(x))
        
        # Group by date and category
        category_trends = df.groupby(["date", "category"]).size().unstack(fill_value=0)
        
        # Create line plot for each category
        for category in category_trends.columns:
            ax.plot(
                category_trends.index,
                category_trends[category],
                marker='o',
                label=category
            )
        
        ax.set_title("Crime Trends by Category")
        ax.set_xlabel("Date")
        ax.set_ylabel("Number of Crimes")
        ax.legend()
        plt.xticks(rotation=45)
        
        return fig
    
    def save_visualization(self, fig: plt.Figure, output_path: str) -> None:
        """Save visualization to file.
        
        Args:
            fig: matplotlib Figure object to save
            output_path: Path where to save the visualization
            
        Raises:
            IOError: If the file cannot be saved
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Save figure
            fig.savefig(output_path, bbox_inches='tight', dpi=300)
            logger.info(f"Visualization saved to {output_path}")
            
        except Exception as e:
            logger.error(f"Error saving visualization: {str(e)}")
            raise IOError(f"Failed to save visualization: {str(e)}")
    
    def _validate_dataframe(self, df: pd.DataFrame, required_columns: list) -> None:
        """Validate DataFrame for visualization.
        
        Args:
            df: DataFrame to validate
            required_columns: List of required column names
            
        Raises:
            ValueError: If DataFrame is empty or missing required columns
        """
        if df.empty:
            raise ValueError("No data to visualize")
        
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Required column{'' if len(missing_columns) == 1 else 's'} "
                           f"'{', '.join(missing_columns)}' not found") 
