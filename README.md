# Canadian Labour Mismatch Project

An automated GitHub Actions workflow that monitors, downloads, and processes Statistics Canada Labour Force Survey (LFS) and Job Vacancy data to create a combined dataset with mismatch indices and visualizations.

## Overview

This workflow automatically checks for updates to Statistics Canada datasets on a weekly schedule and processes them into a final combined dataset. It calculates mismatch indices between job vacancies and labour force statistics in Quebec and Ontario and generates industry contribution plots for Quebec.

## Features

- **Automated Monitoring**: Runs weekly on Mondays at 7 AM UTC
- **Data Integration**: Combines LFS and Job Vacancy data into a unified dataset
- **Mismatch Analysis**: Calculates mismatch indices between labour supply and demand, and generates industry contribution plots and figures
- **Version Control**: Automatically commits processed data and metadata to the repository
- **Manual Trigger**: Supports manual workflow dispatch with force download option

## Data Sources

The workflow processes two main Statistics Canada datasets:
1. **Labour Force Survey (LFS)** - Employment and labour market statistics
2. **Job Vacancy and Wage Survey (JVWS)** - Job vacancy data by industry

## Workflow Steps

### 1. Environment Setup
- Sets up Python 3.11
- Installs required dependencies

### 2. Data Update Check
- Runs `check_updates.py` to determine if new data is available
- Compares current online data reference dates with stored dates
- Sets workflow flags based on update availability

### 3. Data Processing (if updates available)
- Downloads raw data to temporary directory
- Processes LFS and JVWS data via `process_data.py`
- Runs data subsetting and merging via `subset_and_merge.py`
- Calculates mismatch indices and generates plots via `calculate_mismatch_index.py`
- Cleans up temporary files

### 4. Output Generation
- Creates final dataset (`processed_data/final_data.csv`)
- Generates visualization plots (saved to `figures/` directory)
- Updates metadata files with reference dates and download logs

### 5. Upload and Commit
- Uploads processed data as GitHub artifacts (90-day retention)
- Commits final dataset and metadata to the repository

## Repository Structure

```
├── .github/workflows/
│   └── monitor-statscan-data.yml    # Workflow file
├── code/
│   ├── check_updates.py             # Data update checker
│   ├── process_data.py              # Raw data processor
│   ├── subset_and_merge.py          # Data subsetting and merging
│   └── calculate_mismatch_index.py  # Mismatch analysis and plotting
├── data/
│   ├── last_reference_date_*.txt    # Stored reference dates
│   └── download_log.txt             # Processing log
├── processed_data/
│   └── final_data.csv               # Final combined dataset
└── figures/
    └── *.png                        # Generated plots and visualizations
```

## Manual Execution

You can manually trigger the workflow through the GitHub Actions interface:

1. Go to the "Actions" tab in your repository
2. Select "monitor-statscan-data" workflow
3. Click "Run workflow"
4. Optionally check "Force download" to bypass date checks

## Output Files

### Data Files
- `processed_data/final_data.csv`: Combined LFS and JVWS dataset with calculated fields
- `data/last_reference_date_*.txt`: Reference date tracking files
- `data/download_log.txt`: Processing history and logs

### Visualizations
- `figures/*.png`: Industry contribution plots and mismatch analysis charts in both French and English

## Dependencies

The workflow requires the following Python packages:
- `pandas`: Data manipulation and analysis
- `requests`: HTTP requests for data downloading
- `beautifulsoup4`: Web scraping and HTML parsing
- `numpy`: Numerical computations
- `pyreadstat`: Reading statistical data formats
- `matplotlib`: Plot generation

## Configuration

### Customization Options
- Modify the cron schedule in the workflow file to change execution timing
- Adjust retention days for artifacts (currently set to default 90 days)
- Update Python version or dependencies as needed

## Monitoring and Troubleshooting

### Workflow Status
- Check the "Actions" tab for execution history and status
- Review workflow logs for detailed processing information

### Common Issues
- **No updates**: Workflow will log when no new data is available
- **Processing errors**: Check individual step logs for Python script errors
- **Commit conflicts**: Workflow includes conflict resolution via stash/unstash

## Data Updates

The workflow tracks data freshness through reference dates:
- LFS data reference period
- JVWS data reference period
- Combined processing timestamp

Only processes data when at least one dataset has been updated since the last run.

## License

This workflow processes public data that operates under the Statistics Canada Open License (see https://www.statcan.gc.ca/en/terms-conditions/open-licence-faq)
