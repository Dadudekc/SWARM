# Monthly Crime Report Generator

A Python-based tool for generating monthly crime reports for Houston and Austin, TX. This project automates the collection, processing, and visualization of crime data from official city sources.

## Features

- Automated data collection from HPD and APD sources
- Data cleaning and categorization
- Statistical analysis and trend detection
- Interactive maps and visualizations
- PDF report generation
- Monthly automated execution

## Project Structure

```
crime_report_generator/
├── data_sources/          # Data collection modules
│   ├── houston_scraper.py
│   ├── austin_scraper.py
│   └── download_manager.py
│
├── processors/            # Data processing modules
│   ├── cleaner.py
│   ├── categorizer.py
│   └── aggregator.py
│
├── visualizations/        # Visualization modules
│   ├── map_generator.py
│   └── trend_charts.py
│
├── reports/              # Report generation
│   ├── templates/
│   │   └── monthly_report_template.html
│   ├── generator.py
│   └── exporter.py
│
├── scheduler/            # Automation
│   └── monthly_job.py
│
├── config/              # Configuration
│   └── source_links.yaml
│
├── logs/               # Log files
│   └── crime_report.log
│
├── main.py            # Main execution script
└── README.md
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/crime_report_generator.git
cd crime_report_generator
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Manual Execution

To generate a report for a specific month:

```bash
python main.py --month 01 --year 2024
```

Generate reports for a range of months in a single year:

```bash
python main.py --year 2024 --range 1 3
```

This command will create reports for January through March.

### Automated Execution

The report can be automatically generated on the first day of each month using the scheduler:

```bash
python scheduler/monthly_job.py
```

## Data Sources

- Houston Police Department: https://www.houstontx.gov/police/cs/stats2.htm
- Austin Police Department: https://data.austintexas.gov/Public-Safety/APD-Crime-Data/7g8v-xxte

## Output

The generator produces:
1. Raw data files in CSV format
2. Processed data with crime categorization
3. Visualizations (maps and charts)
4. A comprehensive PDF report

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Houston Police Department for providing crime statistics
- Austin Police Department for maintaining the Open Data Portal
- Contributors and maintainers of the Python libraries used in this project 