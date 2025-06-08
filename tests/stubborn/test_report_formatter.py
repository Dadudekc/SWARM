"""
Tests for the report formatter module.
"""

import pytest
from crime_report_generator.reports.report_formatter import (
    format_markdown_report,
    format_discord_report,
    format_instagram_report,
    format_report
)


@pytest.fixture
def sample_data():
    """Sample data for testing report formatting."""
    return {
        "arcgis_summary": {
            "total_crimes": 100,
            "crime_categories": {
                "violent": 20,
                "property": 50,
                "drug": 15,
                "traffic": 10,
                "other": 5
            },
            "monthly_trend": {
                "2024-01": 30,
                "2024-02": 40,
                "2024-03": 30
            },
            "key_locations": [
                "Main Street",
                "Park Avenue"
            ]
        },
        "crimegrade_summary": {
            "safety_grade": "B",
            "crime_rate_per_1000": "25.5",
            "summary_stats": {
                "violent_crime": "Low",
                "property_crime": "Medium",
                "overall_safety": "Good"
            }
        },
        "comparison": {
            "data_quality": {
                "arcgis_complete": True,
                "crimegrade_complete": True
            },
            "key_differences": [
                {
                    "metric": "Total Crimes",
                    "arcgis": "100",
                    "crimegrade": "25.5 per 1,000 residents"
                }
            ],
            "recommendations": [
                "Use both sources for comprehensive analysis"
            ]
        }
    }


def test_format_markdown_report(sample_data):
    """Test markdown report formatting."""
    report = format_markdown_report(
        "77373",
        2024,
        sample_data["arcgis_summary"],
        sample_data["crimegrade_summary"],
        sample_data["comparison"]
    )
    
    # Check header
    assert "# Crime Report for Spring, TX (77373)" in report
    
    # Check safety grade
    assert "### Safety Grade: B" in report
    
    # Check total crimes
    assert "### Total Crimes: 100" in report
    
    # Check crime categories
    assert "### Crime Categories" in report
    assert "- Violent: 20" in report
    assert "- Property: 50" in report
    
    # Check monthly trend
    assert "### Monthly Trend" in report
    assert "- 2024-01: 30 incidents" in report
    
    # Check key locations
    assert "### Key Locations" in report
    assert "- Main Street" in report
    
    # Check comparison
    assert "## Data Source Comparison" in report
    assert "### Total Crimes" in report
    
    # Check recommendations
    assert "## Recommendations" in report
    assert "- Use both sources for comprehensive analysis" in report


def test_format_discord_report(sample_data):
    """Test Discord report formatting."""
    report = format_discord_report(
        "77373",
        2024,
        sample_data["arcgis_summary"],
        sample_data["crimegrade_summary"],
        sample_data["comparison"]
    )
    
    # Check header
    assert "**Crime Report for Spring, TX (77373)**" in report
    
    # Check safety grade with emoji
    assert "**Safety Grade:** B 🛡️" in report
    
    # Check total crimes with emoji
    assert "**Total Crimes:** 100 📊" in report
    
    # Check crime categories in code block
    assert "**Crime Categories:**" in report
    assert "```" in report
    assert "Violent: 20" in report
    
    # Check comparison
    assert "**Data Source Comparison:**" in report
    assert "**Total Crimes:**" in report
    
    # Check recommendations
    assert "**Recommendations:**" in report
    assert "• Use both sources for comprehensive analysis" in report


def test_format_instagram_report(sample_data):
    """Test Instagram report formatting."""
    report = format_instagram_report(
        "77373",
        2024,
        sample_data["arcgis_summary"],
        sample_data["crimegrade_summary"],
        sample_data["comparison"]
    )
    
    # Check header
    assert "Crime Report: Spring, TX (77373)" in report
    
    # Check safety grade with emoji
    assert "Safety Grade: B 🛡️" in report
    
    # Check total crimes with emoji
    assert "Total Crimes: 100 📊" in report
    
    # Check crime categories
    assert "Top Crime Categories:" in report
    assert "• Violent: 20" in report
    
    # Check key insight
    assert "Key Insight: Use both sources for comprehensive analysis" in report


def test_format_report_invalid_format(sample_data):
    """Test report formatting with invalid format."""
    report = format_report(
        "77373",
        2024,
        sample_data["arcgis_summary"],
        sample_data["crimegrade_summary"],
        sample_data["comparison"],
        "invalid_format"
    )
    
    # Should default to markdown
    assert "# Crime Report for Spring, TX (77373)" in report


def test_format_report_missing_data():
    """Test report formatting with missing data."""
    report = format_markdown_report(
        "77373",
        2024,
        {"error": "No data available"},
        {"error": "No data available"},
        {
            "data_quality": {
                "arcgis_complete": False,
                "crimegrade_complete": False
            },
            "recommendations": ["No data available from either source"]
        }
    )
    
    # Should handle missing data gracefully
    assert "# Crime Report for Spring, TX (77373)" in report
    assert "## Recommendations" in report
    assert "- No data available from either source" in report 
