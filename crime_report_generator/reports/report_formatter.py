from typing import Dict, Any, List
from datetime import datetime
from .zip_mapper import format_location


def format_markdown_report(
    zip_code: str,
    year: int,
    arcgis_summary: Dict[str, Any],
    crimegrade_summary: Dict[str, Any],
    comparison: Dict[str, Any]
) -> str:
    """Format crime report in Markdown."""
    location = format_location(zip_code)
    report = [
        f"# Crime Report for {location} ({zip_code})",
        f"\nGenerated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "\n## Overview",
    ]
    
    # Add safety grade if available
    if crimegrade_summary.get("safety_grade"):
        report.append(f"\n### Safety Grade: {crimegrade_summary['safety_grade']}")
    
    # Add total crimes
    if "total_crimes" in arcgis_summary:
        report.append(f"\n### Total Crimes: {arcgis_summary['total_crimes']}")
    
    # Add neighborhood safety if available
    if "neighborhood_safety" in crimegrade_summary:
        safety = crimegrade_summary["neighborhood_safety"]
        report.append(f"\n### Neighborhood Safety")
        report.append(f"- {safety['safe_count']} out of {safety['total_count']} neighborhoods rated A- or better")
        report.append(f"- {safety['safe_percentage']:.1f}% of neighborhoods are considered safe")
    
    # Add crime categories
    if "crime_categories" in arcgis_summary:
        report.append("\n### Crime Categories")
        for category, count in arcgis_summary["crime_categories"].items():
            if count > 0:
                report.append(f"- {category.title()}: {count}")
    
    # Add crime type breakdown if available
    if "crime_types" in crimegrade_summary:
        report.append("\n### Crime Type Breakdown")
        for crime_type, rate in crimegrade_summary["crime_types"].items():
            report.append(f"- {crime_type}: {rate}")
    
    # Add monthly trend
    if "monthly_trend" in arcgis_summary:
        report.append("\n### Monthly Trend")
        for month, count in sorted(arcgis_summary["monthly_trend"].items()):
            report.append(f"- {month}: {count} incidents")
    
    # Add key locations
    if "key_locations" in arcgis_summary:
        report.append("\n### Key Locations")
        for location in arcgis_summary["key_locations"]:
            report.append(f"- {location}")
    
    # Add comparison section
    if comparison.get("key_differences"):
        report.append("\n## Data Source Comparison")
        for diff in comparison["key_differences"]:
            report.append(f"\n### {diff['metric']}")
            report.append(f"- ArcGIS: {diff['arcgis']}")
            report.append(f"- CrimeGrade: {diff['crimegrade']}")
    
    # Add recommendations
    if comparison.get("recommendations"):
        report.append("\n## Recommendations")
        for rec in comparison["recommendations"]:
            report.append(f"- {rec}")
    
    return "\n".join(report)


def format_discord_report(
    zip_code: str,
    year: int,
    arcgis_summary: Dict[str, Any],
    crimegrade_summary: Dict[str, Any],
    comparison: Dict[str, Any]
) -> str:
    """Format crime report for Discord with emojis and code blocks."""
    location = format_location(zip_code)
    report = [
        f"**Crime Report for {location} ({zip_code})**",
        f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "\n**Overview**",
    ]
    
    # Add safety grade
    if crimegrade_summary.get("safety_grade"):
        report.append(f"\n**Safety Grade:** {crimegrade_summary['safety_grade']} 🛡️")
    
    # Add total crimes
    if "total_crimes" in arcgis_summary:
        report.append(f"\n**Total Crimes:** {arcgis_summary['total_crimes']} 📊")
    
    # Add neighborhood safety if available
    if "neighborhood_safety" in crimegrade_summary:
        safety = crimegrade_summary["neighborhood_safety"]
        report.append(f"\n**Neighborhood Safety:** 🏘️")
        report.append(f"• {safety['safe_count']} out of {safety['total_count']} neighborhoods rated A- or better")
        report.append(f"• {safety['safe_percentage']:.1f}% of neighborhoods are considered safe")
    
    # Add crime categories in code block
    if "crime_categories" in arcgis_summary:
        report.append("\n**Crime Categories:**")
        categories = []
        for category, count in arcgis_summary["crime_categories"].items():
            if count > 0:
                categories.append(f"{category.title()}: {count}")
        report.append(f"```\n{chr(10).join(categories)}\n```")
    
    # Add crime type breakdown if available
    if "crime_types" in crimegrade_summary:
        report.append("\n**Crime Type Breakdown:**")
        types = []
        for crime_type, rate in crimegrade_summary["crime_types"].items():
            types.append(f"{crime_type}: {rate}")
        report.append(f"```\n{chr(10).join(types)}\n```")
    
    # Add comparison
    if comparison.get("key_differences"):
        report.append("\n**Data Source Comparison:**")
        for diff in comparison["key_differences"]:
            report.append(f"\n**{diff['metric']}:**")
            report.append(f"ArcGIS: {diff['arcgis']}")
            report.append(f"CrimeGrade: {diff['crimegrade']}")
    
    # Add recommendations
    if comparison.get("recommendations"):
        report.append("\n**Recommendations:**")
        for rec in comparison["recommendations"]:
            report.append(f"• {rec}")
    
    return "\n".join(report)


def format_instagram_report(
    zip_code: str,
    year: int,
    arcgis_summary: Dict[str, Any],
    crimegrade_summary: Dict[str, Any],
    comparison: Dict[str, Any]
) -> str:
    """Format crime report for Instagram with emojis and concise text."""
    location = format_location(zip_code)
    report = [
        f"Crime Report: {location} ({zip_code})",
        f"Generated: {datetime.now().strftime('%Y-%m-%d')}",
    ]
    
    # Add safety grade
    if crimegrade_summary.get("safety_grade"):
        report.append(f"\nSafety Grade: {crimegrade_summary['safety_grade']} 🛡️")
    
    # Add total crimes
    if "total_crimes" in arcgis_summary:
        report.append(f"Total Crimes: {arcgis_summary['total_crimes']} 📊")
    
    # Add neighborhood safety if available
    if "neighborhood_safety" in crimegrade_summary:
        safety = crimegrade_summary["neighborhood_safety"]
        report.append(f"\nNeighborhood Safety: 🏘️")
        report.append(f"• {safety['safe_percentage']:.1f}% safe neighborhoods")
    
    # Add top crime categories
    if "crime_categories" in arcgis_summary:
        report.append("\nTop Crime Categories:")
        for category, count in arcgis_summary["crime_categories"].items():
            if count > 0:
                report.append(f"• {category.title()}: {count}")
    
    # Add key insight
    if comparison.get("recommendations"):
        report.append(f"\nKey Insight: {comparison['recommendations'][0]}")
    
    return "\n".join(report)


def format_report(
    zip_code: str,
    year: int,
    arcgis_summary: Dict[str, Any],
    crimegrade_summary: Dict[str, Any],
    comparison: Dict[str, Any],
    format_type: str = "markdown"
) -> str:
    """Format crime report in the specified format."""
    formatters = {
        "markdown": format_markdown_report,
        "discord": format_discord_report,
        "instagram": format_instagram_report
    }
    
    formatter = formatters.get(format_type.lower(), format_markdown_report)
    return formatter(zip_code, year, arcgis_summary, crimegrade_summary, comparison) 