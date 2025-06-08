"""
Report generator module for creating crime reports in various formats.
"""

import os
import json
from typing import Dict, Optional
import pandas as pd
from datetime import datetime
import logging
from pathlib import Path
import jinja2
from weasyprint import HTML
from crime_report_generator.visualizations.crime_visualizer import CrimeVisualizer

logger = logging.getLogger(__name__)

class ReportGenerator:
    """Class for generating crime reports in various formats."""
    
    def __init__(self):
        """Initialize the report generator with default templates and visualizer."""
        self.visualizer = CrimeVisualizer()
        self.default_markdown_template = """
# Monthly Crime Report
## {{ month }} {{ year }}

### Overview
Total Crimes: {{ total_crimes }}
Crime Trend: {{ crime_trend }}

## Crime Distribution by Category
![Category Distribution]({{ category_chart }})

## Crime Trends
![Crime Trends]({{ trend_chart }})

## Location Analysis
![Location Distribution]({{ location_chart }})

### Top Locations
{% for location, count in top_locations.items() %}
- {{ location }}: {{ count }} crimes
{% endfor %}

### Category Breakdown
{% for category, count in category_counts.items() %}
- {{ category }}: {{ count }} crimes
{% endfor %}
"""
        
        self.default_html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>Monthly Crime Report - {{ month }} {{ year }}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        h1 { color: #2c3e50; }
        h2 { color: #34495e; }
        .chart { max-width: 800px; margin: 20px 0; }
        .summary { background: #f8f9fa; padding: 20px; border-radius: 5px; }
    </style>
</head>
<body>
    <h1>Monthly Crime Report</h1>
    <h2>{{ month }} {{ year }}</h2>
    
    <div class="summary">
        <h3>Overview</h3>
        <p>Total Crimes: {{ total_crimes }}</p>
        <p>Crime Trend: {{ crime_trend }}</p>
    </div>
    
    <h2>Crime Distribution by Category</h2>
    <img class="chart" src="{{ category_chart }}" alt="Category Distribution">
    
    <h2>Crime Trends</h2>
    <img class="chart" src="{{ trend_chart }}" alt="Crime Trends">
    
    <h2>Location Analysis</h2>
    <img class="chart" src="{{ location_chart }}" alt="Location Distribution">
    
    <h2>Top Locations</h2>
    <ul>
    {% for location, count in top_locations.items() %}
        <li>{{ location }}: {{ count }} crimes</li>
    {% endfor %}
    </ul>
    
    <h2>Category Breakdown</h2>
    <ul>
    {% for category, count in category_counts.items() %}
        <li>{{ category }}: {{ count }} crimes</li>
    {% endfor %}
    </ul>
</body>
</html>
"""
    
    def generate_markdown_report(
        self,
        data: pd.DataFrame,
        output_path: str,
        month: str,
        year: int,
        template: Optional[str] = None
    ) -> None:
        """Generate a markdown report with embedded visualizations.
        
        Args:
            data: DataFrame containing crime data
            output_path: Path where to save the report
            month: Month name for the report
            year: Year for the report
            template: Optional custom template string
            
        Raises:
            ValueError: If DataFrame is empty or missing required columns
        """
        self._validate_dataframe(data)
        
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Generate visualizations
        charts_dir = os.path.join(os.path.dirname(output_path), "charts")
        os.makedirs(charts_dir, exist_ok=True)
        
        category_chart = os.path.join(charts_dir, "category_distribution.png")
        trend_chart = os.path.join(charts_dir, "crime_trends.png")
        location_chart = os.path.join(charts_dir, "location_distribution.png")
        
        self.visualizer.create_category_pie_chart(data).savefig(category_chart)
        self.visualizer.create_trend_line_chart(data).savefig(trend_chart)
        self.visualizer.create_location_bar_chart(data).savefig(location_chart)
        
        # Generate summary statistics
        summary = self.generate_summary_statistics(data)
        
        # Render template
        template_str = template or self.default_markdown_template
        template = jinja2.Template(template_str)
        
        report_content = template.render(
            month=month,
            year=year,
            total_crimes=summary["total_crimes"],
            crime_trend=summary["crime_trend"],
            category_chart=os.path.relpath(category_chart, os.path.dirname(output_path)),
            trend_chart=os.path.relpath(trend_chart, os.path.dirname(output_path)),
            location_chart=os.path.relpath(location_chart, os.path.dirname(output_path)),
            top_locations=summary["top_locations"],
            category_counts=summary["category_counts"]
        )
        
        # Save report
        with open(output_path, "w") as f:
            f.write(report_content)
    
    def generate_html_report(
        self,
        data: pd.DataFrame,
        output_path: str,
        month: str,
        year: int,
        template: Optional[str] = None
    ) -> None:
        """Generate an HTML report with embedded visualizations.
        
        Args:
            data: DataFrame containing crime data
            output_path: Path where to save the report
            month: Month name for the report
            year: Year for the report
            template: Optional custom template string
            
        Raises:
            ValueError: If DataFrame is empty or missing required columns
        """
        self._validate_dataframe(data)
        
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Generate visualizations
        charts_dir = os.path.join(os.path.dirname(output_path), "charts")
        os.makedirs(charts_dir, exist_ok=True)
        
        category_chart = os.path.join(charts_dir, "category_distribution.png")
        trend_chart = os.path.join(charts_dir, "crime_trends.png")
        location_chart = os.path.join(charts_dir, "location_distribution.png")
        
        self.visualizer.create_category_pie_chart(data).savefig(category_chart)
        self.visualizer.create_trend_line_chart(data).savefig(trend_chart)
        self.visualizer.create_location_bar_chart(data).savefig(location_chart)
        
        # Generate summary statistics
        summary = self.generate_summary_statistics(data)
        
        # Render template
        template_str = template or self.default_html_template
        template = jinja2.Template(template_str)
        
        report_content = template.render(
            month=month,
            year=year,
            total_crimes=summary["total_crimes"],
            crime_trend=summary["crime_trend"],
            category_chart=os.path.relpath(category_chart, os.path.dirname(output_path)),
            trend_chart=os.path.relpath(trend_chart, os.path.dirname(output_path)),
            location_chart=os.path.relpath(location_chart, os.path.dirname(output_path)),
            top_locations=summary["top_locations"],
            category_counts=summary["category_counts"]
        )
        
        # Save report
        with open(output_path, "w") as f:
            f.write(report_content)
    
    def generate_pdf_report(
        self,
        data: pd.DataFrame,
        output_path: str,
        month: str,
        year: int,
        template: Optional[str] = None
    ) -> None:
        """Generate a PDF report with embedded visualizations.
        
        Args:
            data: DataFrame containing crime data
            output_path: Path where to save the report
            month: Month name for the report
            year: Year for the report
            template: Optional custom template string
            
        Raises:
            ValueError: If DataFrame is empty or missing required columns
        """
        # First generate HTML report
        html_path = output_path.replace(".pdf", ".html")
        self.generate_html_report(data, html_path, month, year, template)
        
        # Convert HTML to PDF
        HTML(html_path).write_pdf(output_path)
        
        # Clean up temporary HTML file
        os.remove(html_path)

    def generate_json_report(
        self,
        data: pd.DataFrame,
        output_path: str,
        month: str,
        year: int,
    ) -> None:
        """Generate a JSON report containing summary statistics."""
        self._validate_dataframe(data)

        summary = self.generate_summary_statistics(data)
        report = {
            "month": month,
            "year": year,
            **summary,
        }
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
    
    def generate_summary_statistics(self, data: pd.DataFrame) -> Dict:
        """Generate summary statistics for the report.
        
        Args:
            data: DataFrame containing crime data
            
        Returns:
            Dictionary containing summary statistics
            
        Raises:
            ValueError: If DataFrame is empty or missing required columns
        """
        self._validate_dataframe(data)
        
        # Calculate total crimes
        total_crimes = data["count"].sum()
        
        # Convert category to string for grouping
        data = data.copy()
        data["category"] = data["category"].apply(lambda x: x.name if hasattr(x, "name") else str(x))
        
        # Calculate category counts
        category_counts = data.groupby("category")["count"].sum().to_dict()
        
        # Calculate top locations
        top_locations = data.groupby("location")["count"].sum().sort_values(ascending=False).to_dict()
        
        # Determine crime trend
        if not pd.api.types.is_datetime64_any_dtype(data["date"]):
            data["date"] = pd.to_datetime(data["date"])
        
        daily_counts = data.groupby("date")["count"].sum()
        if len(daily_counts) > 1:
            trend = daily_counts.diff().mean()
            if trend > 0.1:
                crime_trend = "increasing"
            elif trend < -0.1:
                crime_trend = "decreasing"
            else:
                crime_trend = "stable"
        else:
            crime_trend = "stable"
        
        return {
            "total_crimes": total_crimes,
            "category_counts": category_counts,
            "top_locations": top_locations,
            "crime_trend": crime_trend
        }
    
    def _validate_dataframe(self, df: pd.DataFrame) -> None:
        """Validate DataFrame for report generation.
        
        Args:
            df: DataFrame to validate
            
        Raises:
            ValueError: If DataFrame is empty or missing required columns
        """
        if df.empty:
            raise ValueError("No data to generate report")
        
        required_columns = ["date", "offense", "description", "category", "location", "count"]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Required column '{missing_columns[0]}' not found") 
