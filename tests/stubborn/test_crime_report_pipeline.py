"""
Integration tests for the crime report pipeline.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, Mock
from crime_report_generator.reports.crime_report_pipeline import (
    generate_report,
    main
)
import json
import sys


@pytest.fixture
def mock_data():
    """Mock data for testing."""
    return {
        "arcgis_data": {
            "total_crimes": 100,
            "crimes": [
                {
                    "type": "violent",
                    "date": "2024-01-01",
                    "status": "Open",
                    "location": "Main Street"
                }
            ]
        },
        "crimegrade_data": {
            "safety_grade": "B",
            "crime_rate_per_1000": "25.5",
            "summary_stats": {
                "violent_crime": "Low",
                "property_crime": "Medium"
            }
        }
    }


@patch("crime_report_generator.reports.crime_report_pipeline.fetch_montgomery_arcgis")
@patch("crime_report_generator.reports.crime_report_pipeline.fetch_crimegrade_data")
def test_generate_report_both_sources(
    mock_crimegrade,
    mock_arcgis,
    mock_data
):
    """Test report generation with both data sources."""
    # Setup mocks
    mock_arcgis.return_value = mock_data["arcgis_data"]
    mock_crimegrade.return_value = mock_data["crimegrade_data"]
    
    # Generate report
    report = generate_report("77373", 2024)
    
    # Verify mocks were called
    mock_arcgis.assert_called_once_with("77373", 2024)
    mock_crimegrade.assert_called_once_with("77373", headless=True)
    
    # Verify report content
    assert "Crime Report for Spring, TX (77373)" in report
    assert "Safety Grade: B" in report
    assert "Total Crimes: 100" in report


@patch("crime_report_generator.reports.crime_report_pipeline.fetch_montgomery_arcgis")
@patch("crime_report_generator.reports.crime_report_pipeline.fetch_crimegrade_data")
def test_generate_report_arcgis_only(
    mock_crimegrade,
    mock_arcgis,
    mock_data
):
    """Test report generation with ArcGIS data only."""
    # Setup mocks
    mock_arcgis.return_value = mock_data["arcgis_data"]
    
    # Generate report
    report = generate_report("77373", 2024, source="arcgis")
    
    # Verify mocks
    mock_arcgis.assert_called_once()
    mock_crimegrade.assert_not_called()
    
    # Verify report content
    assert "Crime Report for Spring, TX (77373)" in report
    assert "Total Crimes: 100" in report
    assert "Safety Grade" not in report


@patch("crime_report_generator.reports.crime_report_pipeline.fetch_montgomery_arcgis")
@patch("crime_report_generator.reports.crime_report_pipeline.fetch_crimegrade_data")
def test_generate_report_json_format(
    mock_crimegrade,
    mock_arcgis,
    mock_data
):
    """Test report generation in JSON format."""
    # Setup mocks
    mock_arcgis.return_value = mock_data["arcgis_data"]
    mock_crimegrade.return_value = mock_data["crimegrade_data"]
    
    # Generate report
    report = generate_report("77373", 2024, format_type="json")
    
    # Parse JSON
    data = json.loads(report)  # Use json.loads instead of eval
    
    # Verify structure
    assert data["location"]["zip"] == "77373"
    assert data["location"]["city"] == "Spring"
    assert data["year"] == 2024
    assert "arcgis" in data
    assert "crimegrade" in data
    assert "arcgis_summary" in data
    assert "crimegrade_summary" in data
    assert "comparison" in data


def test_main_stdout(capsys):
    """Test main function with stdout output."""
    with patch('crime_report_generator.reports.crime_report_pipeline.generate_report') as mock_generate:
        mock_generate.return_value = "Test Report"
        sys.argv = ['script.py', '--zip', '77373', '--year', '2024', '--headless']
        main()
        captured = capsys.readouterr()
        assert "Test Report" in captured.out
        mock_generate.assert_called_once_with(
            "77373", 2024, "both", "markdown", True
        )


def test_main_file_output(tmp_path):
    """Test main function with file output."""
    with patch('crime_report_generator.reports.crime_report_pipeline.generate_report') as mock_generate:
        mock_generate.return_value = "Test Report"
        output_dir = tmp_path / "test_output"
        output_dir.mkdir()
        sys.argv = ['script.py', '--zip', '77373', '--year', '2024', 
                   '--output', str(output_dir), '--headless']
        main()
        mock_generate.assert_called_once_with(
            "77373", 2024, "both", "markdown", True
        )


def test_main_invalid_year():
    """Test main function with invalid year."""
    with patch('sys.exit') as mock_exit:
        sys.argv = ['script.py', '--zip', '77373', '--year', '1899']
        main()
        mock_exit.assert_called_once_with(1)


def test_main_multiple_zips():
    """Test main function with multiple ZIP codes."""
    with patch('crime_report_generator.reports.crime_report_pipeline.generate_report') as mock_generate:
        mock_generate.return_value = "Test Report"
        sys.argv = ['script.py', '--zip', '77373', '77001', '--year', '2024', 
                   '--format', 'discord', '--headless']
        main()
        mock_generate.assert_any_call("77373", 2024, "both", "discord", True)
        mock_generate.assert_any_call("77001", 2024, "both", "discord", True) 
