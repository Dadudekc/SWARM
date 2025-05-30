#!/usr/bin/env python3
"""
Crime Report Pipeline CLI

Generates crime reports by combining data from ArcGIS and CrimeGrade.org.
"""

import argparse
import sys
from typing import List, Optional
from datetime import datetime
import json
from pathlib import Path

from .arcgis_fetcher import fetch_montgomery_arcgis
from .crimegrade_scraper import fetch_crimegrade_data
from .summarizer import summarize_arcgis_data, summarize_crimegrade_data, compare_sources
from .report_formatter import format_report
from .zip_mapper import get_zip_details


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate crime reports from multiple data sources",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate report for single ZIP
  python crime_report_pipeline.py --zip 77373 --year 2024

  # Generate reports for multiple ZIPs
  python crime_report_pipeline.py --zip 77373 77056 77875 --year 2024

  # Generate Discord-formatted report
  python crime_report_pipeline.py --zip 77373 --year 2024 --format discord

  # Use only ArcGIS data
  python crime_report_pipeline.py --zip 77373 --year 2024 --source arcgis

  # Save output to file
  python crime_report_pipeline.py --zip 77373 --year 2024 --output reports/
        """
    )
    
    parser.add_argument(
        "--zip",
        nargs="+",
        required=True,
        help="One or more ZIP codes to analyze"
    )
    
    parser.add_argument(
        "--year",
        type=int,
        required=True,
        help="Year to analyze"
    )
    
    parser.add_argument(
        "--format",
        choices=["markdown", "discord", "instagram", "json"],
        default="markdown",
        help="Output format (default: markdown)"
    )
    
    parser.add_argument(
        "--source",
        choices=["both", "arcgis", "crimegrade"],
        default="both",
        help="Data source(s) to use (default: both)"
    )
    
    parser.add_argument(
        "--output",
        type=str,
        help="Output directory for reports (default: stdout)"
    )
    
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run CrimeGrade scraper in headless mode"
    )
    
    return parser.parse_args()


def generate_report(
    zip_code: str,
    year: int,
    source: str = "both",
    format_type: str = "markdown",
    headless: bool = True
) -> str:
    """Generate a single crime report."""
    arcgis_data = None
    crimegrade_data = None
    
    # Get location details
    location = get_zip_details(zip_code)
    
    # Fetch data based on source selection
    if source in ["both", "arcgis"]:
        arcgis_data = fetch_montgomery_arcgis(zip_code, year)
        arcgis_summary = summarize_arcgis_data(arcgis_data)
    else:
        arcgis_summary = {"error": "ArcGIS data not requested"}
    
    if source in ["both", "crimegrade"]:
        crimegrade_data = fetch_crimegrade_data(zip_code, headless=headless)
        crimegrade_summary = summarize_crimegrade_data(crimegrade_data)
    else:
        crimegrade_summary = {"error": "CrimeGrade data not requested"}
    
    # Compare sources
    comparison = compare_sources(arcgis_summary, crimegrade_summary)
    
    # Format report
    if format_type == "json":
        report = {
            "location": location,
            "year": year,
            "arcgis": arcgis_data,
            "crimegrade": crimegrade_data,
            "arcgis_summary": arcgis_summary,
            "crimegrade_summary": crimegrade_summary,
            "comparison": comparison
        }
        return json.dumps(report, indent=2)
    else:
        return format_report(
            zip_code,
            year,
            arcgis_summary,
            crimegrade_summary,
            comparison,
            format_type
        )


def main():
    """Main entry point for the crime report generator."""
    args = parse_args()
    
    # Validate year
    if args.year < 1900 or args.year > datetime.now().year:
        print(f"Error: Year must be between 1900 and {datetime.now().year}")
        sys.exit(1)
    
    # Create output directory if specified
    if args.output:
        output_dir = Path(args.output)
        output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate reports for each ZIP code
    for zip_code in args.zip:
        try:
            report = generate_report(
                zip_code,
                args.year,
                args.source,
                args.format,
                args.headless
            )
            
            if args.output:
                # Get location details for filename
                location = get_zip_details(zip_code)
                city = location["city"].lower().replace(" ", "_")
                filename = f"crime_report_{city}_{zip_code}_{args.year}.{args.format}"
                output_file = output_dir / filename
                output_file.write_text(report)
                print(f"Report saved to: {output_file}")
            else:
                print(report)
                print("\n" + "=" * 80 + "\n")
                
        except Exception as e:
            print(f"Error generating report for ZIP {zip_code}: {e}")
            continue


if __name__ == "__main__":
    main() 