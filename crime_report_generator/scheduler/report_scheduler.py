"""
Scheduler module for automating crime report generation and distribution.
"""

import os
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import pandas as pd
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from crime_report_generator.reports.report_generator import ReportGenerator

logger = logging.getLogger(__name__)

class ReportScheduler:
    """Class for scheduling and automating crime report generation and distribution."""
    
    VALID_REPORT_TYPES = ["monthly", "quarterly", "annual"]
    VALID_FORMATS = ["pdf", "html", "markdown"]
    
    def __init__(
        self,
        data_source: Any,
        distributor: Any,
        output_dir: str = "reports",
        timezone: str = "UTC"
    ):
        """Initialize the report scheduler.
        
        Args:
            data_source: Object that provides crime data (must implement get_crime_data())
            distributor: Object that handles report distribution (must implement distribute_report())
            output_dir: Directory where reports will be saved
            timezone: Timezone for scheduling (default: UTC)
        """
        self.data_source = data_source
        self.distributor = distributor
        self.output_dir = output_dir
        self.timezone = timezone
        self.report_generator = ReportGenerator()
        self.scheduler = BackgroundScheduler(timezone=timezone)
        self.scheduler.start()
        self.running = True
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
    
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
            
        Raises:
            ValueError: If report_type or format is invalid
        """
        if report_type not in self.VALID_REPORT_TYPES:
            raise ValueError(f"Invalid report type: {report_type}")
        if format not in self.VALID_FORMATS:
            raise ValueError(f"Invalid report format: {format}")
        
        # Create job ID
        job_id = f"{report_type}_{year}_{month:02d}"
        
        # Schedule the job
        self.scheduler.add_job(
            self.generate_and_distribute_report,
            CronTrigger(
                year=year,
                month=month,
                day=day,
                hour=hour,
                minute=minute
            ),
            args=[report_type, month, year, format],
            id=job_id,
            replace_existing=True
        )
        
        logger.info(f"Scheduled {report_type} report for {year}-{month:02d}")
        return job_id
    
    def generate_report(
        self,
        report_type: str,
        month: int,
        year: int,
        format: str = "pdf"
    ) -> bool:
        """Generate a report without distribution.
        
        Args:
            report_type: Type of report ("monthly", "quarterly", "annual")
            month: Month to generate report for (1-12)
            year: Year to generate report for
            format: Report format ("pdf", "html", "markdown")
            
        Returns:
            bool: True if report was generated successfully
        """
        try:
            # Get crime data
            data = self.data_source.get_crime_data(month, year)
            if data is None or data.empty:
                logger.error(f"No data available for {year}-{month:02d}")
                return False
            
            # Generate report filename
            month_name = datetime(year, month, 1).strftime("%B")
            filename = f"{report_type}_report_{year}_{month:02d}.{format}"
            output_path = os.path.join(self.output_dir, filename)
            
            # Generate report
            if format == "pdf":
                self.report_generator.generate_pdf_report(
                    data=data,
                    output_path=output_path,
                    month=month_name,
                    year=year
                )
            elif format == "html":
                self.report_generator.generate_html_report(
                    data=data,
                    output_path=output_path,
                    month=month_name,
                    year=year
                )
            else:  # markdown
                self.report_generator.generate_markdown_report(
                    data=data,
                    output_path=output_path,
                    month=month_name,
                    year=year
                )
            
            logger.info(f"Generated {report_type} report: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error generating report: {str(e)}")
            return False
    
    def generate_and_distribute_report(
        self,
        report_type: str,
        month: int,
        year: int,
        format: str = "pdf"
    ) -> bool:
        """Generate and distribute a report.
        
        Args:
            report_type: Type of report ("monthly", "quarterly", "annual")
            month: Month to generate report for (1-12)
            year: Year to generate report for
            format: Report format ("pdf", "html", "markdown")
            
        Returns:
            bool: True if report was generated and distributed successfully
        """
        try:
            # Generate report
            if not self.generate_report(report_type, month, year, format):
                return False
            
            # Get report path
            filename = f"{report_type}_report_{year}_{month:02d}.{format}"
            report_path = os.path.join(self.output_dir, filename)
            
            # Distribute report
            success = self.distributor.distribute_report(
                report_path=report_path,
                report_type=report_type,
                month=month,
                year=year,
                format=format
            )
            
            if success:
                logger.info(f"Distributed {report_type} report: {report_path}")
            else:
                logger.error(f"Failed to distribute {report_type} report: {report_path}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error generating and distributing report: {str(e)}")
            return False
    
    def get_scheduled_jobs(self) -> Dict[str, Any]:
        """Get all scheduled report jobs.
        
        Returns:
            Dictionary of scheduled jobs
        """
        jobs = {}
        for job in self.scheduler.get_jobs():
            jobs[job.id] = {
                'next_run_time': job.next_run_time,
                'trigger': str(job.trigger)
            }
        return jobs
    
    def remove_job(self, job_id: str) -> bool:
        """Remove a scheduled report job.
        
        Args:
            job_id: ID of the job to remove
            
        Returns:
            True if job was removed successfully
        """
        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"Removed job {job_id}")
            return True
        except Exception as e:
            logger.error(f"Error removing job {job_id}: {str(e)}")
            return False
    
    def shutdown(self) -> None:
        """Shut down the scheduler."""
        self.scheduler.shutdown()
        self.running = False
        logger.info("Report scheduler shut down") 
