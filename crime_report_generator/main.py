#!/usr/bin/env python3
"""
Monthly Crime Report Generator for Houston and Austin, TX
Main execution pipeline for data collection, processing, and report generation.
"""

import os
import sys
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(project_root / 'logs' / 'crime_report.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class CrimeReportGenerator:
    """Main class for orchestrating the crime report generation pipeline."""
    
    def __init__(self, month: Optional[str] = None, year: Optional[int] = None):
        """Initialize the report generator.
        
        Args:
            month: Month to generate report for (e.g., '01' for January)
            year: Year to generate report for (e.g., 2024)
        """
        self.month = month or datetime.now().strftime('%m')
        self.year = year or datetime.now().year
        self.data_dir = project_root / 'data'
        self.reports_dir = project_root / 'reports'
        
        # Create necessary directories
        self.data_dir.mkdir(exist_ok=True)
        self.reports_dir.mkdir(exist_ok=True)
        
        logger.info(f"Initialized CrimeReportGenerator for {self.month}/{self.year}")
    
    def collect_data(self) -> Dict[str, List[Dict]]:
        """Collect crime data from both cities.
        
        Returns:
            Dict containing raw data from both cities
        """
        logger.info("Starting data collection...")
        
        try:
            from data_sources.houston_scraper import HoustonScraper
            from data_sources.austin_scraper import AustinScraper
            
            # Initialize scrapers
            houston_scraper = HoustonScraper()
            austin_scraper = AustinScraper()
            
            # Collect data
            houston_data = houston_scraper.collect_data(self.month, self.year)
            austin_data = austin_scraper.collect_data(self.month, self.year)
            
            logger.info("Data collection completed successfully")
            return {
                'houston': houston_data,
                'austin': austin_data
            }
            
        except Exception as e:
            logger.error(f"Error during data collection: {str(e)}")
            raise
    
    def process_data(self, raw_data: Dict[str, List[Dict]]) -> Dict[str, Dict]:
        """Process and clean the collected data.
        
        Args:
            raw_data: Raw data from both cities
            
        Returns:
            Processed data ready for analysis
        """
        logger.info("Starting data processing...")
        
        try:
            from processors.cleaner import DataCleaner
            from processors.categorizer import CrimeCategorizer
            from processors.aggregator import DataAggregator
            
            # Initialize processors
            cleaner = DataCleaner()
            categorizer = CrimeCategorizer()
            aggregator = DataAggregator()
            
            # Process data for each city
            processed_data = {}
            for city, data in raw_data.items():
                # Clean the data
                cleaned_data = cleaner.clean(data)
                
                # Categorize crimes
                categorized_data = categorizer.categorize(cleaned_data)
                
                # Aggregate statistics
                processed_data[city] = aggregator.aggregate(categorized_data)
            
            logger.info("Data processing completed successfully")
            return processed_data
            
        except Exception as e:
            logger.error(f"Error during data processing: {str(e)}")
            raise
    
    def generate_visualizations(self, processed_data: Dict[str, Dict]) -> Dict[str, str]:
        """Generate visualizations from processed data.
        
        Args:
            processed_data: Processed data from both cities
            
        Returns:
            Dict mapping visualization types to file paths
        """
        logger.info("Starting visualization generation...")
        
        try:
            from visualizations.map_generator import MapGenerator
            from visualizations.trend_charts import TrendChartGenerator
            
            # Initialize visualization generators
            map_gen = MapGenerator()
            chart_gen = TrendChartGenerator()
            
            # Generate visualizations
            visualizations = {}
            
            # Generate maps
            for city, data in processed_data.items():
                map_path = map_gen.generate_heatmap(data, city)
                visualizations[f"{city}_map"] = map_path
            
            # Generate trend charts
            for city, data in processed_data.items():
                chart_path = chart_gen.generate_trends(data, city)
                visualizations[f"{city}_trends"] = chart_path
            
            logger.info("Visualization generation completed successfully")
            return visualizations
            
        except Exception as e:
            logger.error(f"Error during visualization generation: {str(e)}")
            raise
    
    def generate_report(self, processed_data: Dict[str, Dict], 
                       visualizations: Dict[str, str]) -> str:
        """Generate the final report.
        
        Args:
            processed_data: Processed data from both cities
            visualizations: Generated visualization file paths
            
        Returns:
            Path to the generated report
        """
        logger.info("Starting report generation...")
        
        try:
            from reports.generator import ReportGenerator
            
            # Initialize report generator
            report_gen = ReportGenerator()
            
            # Generate report
            report_path = report_gen.generate(
                processed_data,
                visualizations,
                self.month,
                self.year
            )
            
            logger.info(f"Report generation completed successfully: {report_path}")
            return report_path
            
        except Exception as e:
            logger.error(f"Error during report generation: {str(e)}")
            raise
    
    def run_pipeline(self) -> str:
        """Run the complete report generation pipeline.
        
        Returns:
            Path to the generated report
        """
        try:
            # Step 1: Collect data
            raw_data = self.collect_data()
            
            # Step 2: Process data
            processed_data = self.process_data(raw_data)
            
            # Step 3: Generate visualizations
            visualizations = self.generate_visualizations(processed_data)
            
            # Step 4: Generate report
            report_path = self.generate_report(processed_data, visualizations)
            
            logger.info("Pipeline completed successfully")
            return report_path
            
        except Exception as e:
            logger.error(f"Pipeline failed: {str(e)}")
            raise

def main():
    """Main entry point for the crime report generator."""
    try:
        # Initialize generator
        generator = CrimeReportGenerator()
        
        # Run pipeline
        report_path = generator.run_pipeline()
        
        print(f"Report generated successfully: {report_path}")
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 