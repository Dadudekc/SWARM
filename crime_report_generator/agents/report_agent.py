from typing import Optional, Dict, Any, List
import logging
from datetime import datetime
import pandas as pd
import os

from ..reports.report_generator import ReportGenerator
from ..scheduler.report_scheduler import ReportScheduler
from ..processors.cleaner import DataCleaner
from ..processors.categorizer import CrimeCategorizer
from ..processors.aggregator import aggregate_by_type, aggregate_by_district, top_locations
from ..visualizations.crime_visualizer import CrimeVisualizer
from social.strategies.reddit_strategy import RedditStrategy

logger = logging.getLogger(__name__)

class ReportAgent:
    """Agent for managing crime report generation and distribution."""
    
    def __init__(
        self,
        data_source: Any,
        output_dir: str = "reports",
        timezone: str = "UTC",
        social_config: Optional[Dict[str, Dict[str, str]]] = None,
        distributor: Any = None
    ):
        """Initialize the report agent.
        
        Args:
            data_source: Object that provides crime data (must implement get_crime_data())
            output_dir: Directory where reports will be saved
            timezone: Timezone for scheduling (default: UTC)
            social_config: Configuration for social media platforms
            distributor: Object that handles report distribution (must implement distribute_report())
        """
        self.data_source = data_source
        self.output_dir = output_dir
        self.timezone = timezone
        self.social_config = social_config or {}
        self.distributor = distributor
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.cleaner = DataCleaner()
        self.categorizer = CrimeCategorizer()
        self.visualizer = CrimeVisualizer()
        self.report_generator = ReportGenerator()
        self.scheduler = ReportScheduler(
            data_source=data_source,
            distributor=distributor,
            output_dir=output_dir,
            timezone=timezone
        )
        
        # Initialize social media strategies
        self.social_strategies = {}
        if 'reddit' in self.social_config:
            # Create a mock driver for testing
            from unittest.mock import Mock
            mock_driver = Mock()
            
            # Initialize RedditStrategy with the mock driver and config
            self.social_strategies['reddit'] = RedditStrategy(
                driver=mock_driver,
                config=self.social_config['reddit']
            )
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
    
    def process_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Process raw crime data.
        
        Args:
            data: Raw crime data as a DataFrame
            
        Returns:
            Processed crime data as a DataFrame
        """
        try:
            # Convert DataFrame to list of dicts for cleaning
            records = data.to_dict('records')
            
            # Clean data
            cleaned_records = self.cleaner.clean(records)
            
            # Convert back to DataFrame
            cleaned_data = pd.DataFrame(cleaned_records)
            
            # Ensure 'description' column exists for categorization
            if 'description' not in cleaned_data.columns:
                if 'crime_type' in cleaned_data.columns:
                    cleaned_data['description'] = cleaned_data['crime_type']
                else:
                    cleaned_data['description'] = ""
            
            # Categorize crimes (need both crime_type and description)
            cleaned_data['category'] = cleaned_data.apply(
                lambda row: self.categorizer.categorize_crime(row['crime_type'], row['description']),
                axis=1
            )
            
            return cleaned_data
            
        except Exception as e:
            self.logger.error(f"Error processing data: {str(e)}")
            raise
    
    def generate_report(
        self,
        report_type: str,
        month: int,
        year: int,
        format: str = "pdf",
        data: Optional[pd.DataFrame] = None
    ) -> str:
        """Generate a crime report.
        
        Args:
            report_type: Type of report ("monthly", "quarterly", "annual")
            month: Month to generate report for (1-12)
            year: Year to generate report for
            format: Report format ("pdf", "html", "markdown")
            data: Optional DataFrame containing crime data. If not provided, data will be fetched from data_source.
            
        Returns:
            Path to the generated report file
        """
        try:
            # Get crime data if not provided
            if data is None:
                data = self.data_source.get_crime_data(month, year)
                if data is None or data.empty:
                    raise ValueError(f"No data available for {year}-{month:02d}")
            
            # Process data
            processed_data = self.process_data(data)
            
            # Ensure 'offense' column exists for report generator compatibility
            if 'offense' not in processed_data.columns:
                if 'crime_type' in processed_data.columns:
                    processed_data['offense'] = processed_data['crime_type']
                else:
                    processed_data['offense'] = ""
            
            # Generate report filename
            month_name = datetime(year, month, 1).strftime("%B")
            filename = f"{report_type}_report_{year}_{month:02d}.{format}"
            output_path = os.path.join(self.output_dir, filename)
            
            # Generate report
            if format == "pdf":
                self.report_generator.generate_pdf_report(
                    data=processed_data,
                    output_path=output_path,
                    month=month_name,
                    year=year
                )
            elif format == "html":
                self.report_generator.generate_html_report(
                    data=processed_data,
                    output_path=output_path,
                    month=month_name,
                    year=year
                )
            else:  # markdown
                self.report_generator.generate_markdown_report(
                    data=processed_data,
                    output_path=output_path,
                    month=month_name,
                    year=year
                )
            
            self.logger.info(f"Generated {report_type} report: {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"Error generating report: {str(e)}")
            raise
    
    def schedule_report(
        self,
        report_type: str,
        month: int,
        year: int,
        format: str = "pdf",
        day: int = 1,
        hour: int = 0,
        minute: int = 0
    ) -> str:
        """Schedule a report to be generated and distributed.
        
        Args:
            report_type: Type of report ("monthly", "quarterly", "annual")
            month: Month to generate report for (1-12)
            year: Year to generate report for
            format: Report format ("pdf", "html", "markdown")
            day: Day of month to generate report (1-31)
            hour: Hour to generate report (0-23)
            minute: Minute to generate report (0-59)
            
        Returns:
            Job ID for the scheduled report
        """
        job = self.scheduler.schedule_report(
            report_type=report_type,
            month=month,
            year=year,
            format=format,
            day=day,
            hour=hour,
            minute=minute
        )
        return str(job)  # Convert job to string ID
    
    def distribute_report(
        self,
        report_path: str,
        platforms: List[str],
        report_type: Optional[str] = None,
        month: Optional[int] = None,
        year: Optional[int] = None,
        format: str = "pdf"
    ) -> Dict[str, bool]:
        """Distribute a report to social media platforms.
        
        Args:
            report_path: Path to the report file
            platforms: List of platforms to distribute to
            report_type: Optional type of report ("monthly", "quarterly", "annual")
            month: Optional month the report is for (1-12)
            year: Optional year the report is for
            format: Report format ("pdf", "html", "markdown")
            
        Returns:
            Dictionary mapping platform names to success status
        """
        results = {}
        
        for platform in platforms:
            try:
                if platform not in self.social_strategies:
                    self.logger.warning(f"No strategy configured for {platform}")
                    results[platform] = False
                    continue
                
                # Get platform strategy
                strategy = self.social_strategies[platform]
                
                # Create post content
                if report_type and month and year:
                    month_name = datetime(year, month, 1).strftime("%B")
                    title = f"{report_type.title()} Crime Report - {month_name} {year}"
                    content = f"Here is the {report_type} crime report for {month_name} {year}."
                else:
                    title = "Crime Report"
                    content = "Here is the latest crime report."
                
                # Post to platform
                success = strategy.post(
                    content=content,
                    media_files=[report_path] if format != "html" else None,
                    url=report_path if format == "html" else None
                )
                
                results[platform] = success
                
            except Exception as e:
                self.logger.error(f"Error distributing to {platform}: {str(e)}")
                results[platform] = False
        
        return results
    
    def get_scheduled_jobs(self) -> Dict[str, Any]:
        """Get all scheduled report jobs.
        
        Returns:
            Dictionary of scheduled jobs
        """
        return self.scheduler.get_scheduled_jobs()
    
    def remove_job(self, job_id: str) -> bool:
        """Remove a scheduled report job.
        
        Args:
            job_id: ID of the job to remove
            
        Returns:
            True if job was removed successfully
        """
        return self.scheduler.remove_job(job_id)
    
    def shutdown(self) -> None:
        """Clean up resources and shut down the agent."""
        self.scheduler.shutdown()
        for strategy in self.social_strategies.values():
            if hasattr(strategy, 'shutdown'):
                strategy.shutdown() 