#!/usr/bin/env python3
"""
Check for updates to Statistics Canada datasets.
"""

import argparse
import csv
import os
import requests
import sys
from datetime import datetime
from io import StringIO


def check_dataset_updates(dataset_name, metadata_url, data_url):
    """Check if a dataset has been updated"""
    print(f"\n=== Checking {dataset_name} ===")
    
    # Download current metadata
    print(f"Downloading current metadata for {dataset_name}...")
    response = requests.get(metadata_url)
    response.raise_for_status()
    
    # Save current metadata
    metadata_file = f'current_metadata_{dataset_name.lower()}.csv'
    with open(metadata_file, 'wb') as f:
        f.write(response.content)
    
    # Read the metadata to get the latest reference period
    try:
        # Read the first few lines to find the cube info
        with open(metadata_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Find the line with cube information (should be line 2, index 1)
        cube_info = None
        for i, line in enumerate(lines[:10]):  # Check first 10 lines
            if any(id_str in line for id_str in ['14100022', '14100442']) or 'Labour force characteristics' in line or 'Job vacancies' in line:
                cube_info = line
                break
        
        if cube_info:
            # Parse the CSV line to extract end reference period
            reader = csv.reader(StringIO(cube_info))
            row = list(reader)[0]
            
            # The end reference period should be in column 8 (index 8)
            if len(row) > 8:
                current_end_date = row[8].strip('"')
                print(f"Current end reference period for {dataset_name}: {current_end_date}")
            else:
                print(f"Could not find end reference period in expected position for {dataset_name}")
                current_end_date = None
        else:
            print(f"Could not find cube information in metadata for {dataset_name}")
            current_end_date = None
            
    except Exception as e:
        print(f"Error parsing metadata for {dataset_name}: {e}")
        current_end_date = None
    
    # Check if we have stored metadata from previous run
    stored_end_date = None
    stored_date_file = f'data/last_reference_date_{dataset_name.lower()}.txt'
    if os.path.exists(stored_date_file):
        with open(stored_date_file, 'r') as f:
            stored_end_date = f.read().strip()
            print(f"Stored end reference period for {dataset_name}: {stored_end_date}")
    else:
        print(f"No previous reference date found for {dataset_name}")
    
    return current_end_date, stored_end_date, metadata_file


def main():
    parser = argparse.ArgumentParser(description='Check for Statistics Canada data updates')
    parser.add_argument('--force-download', type=str, default='false', 
                       help='Force download regardless of date check')
    parser.add_argument('--output-file', type=str, required=True,
                       help='File to write GitHub Actions outputs to')
    
    args = parser.parse_args()
    
    # Dataset configurations
    datasets = {
        'LFS': {
            'metadata_url': "https://www150.statcan.gc.ca/t1/tbl1/en/dtl!downloadCubeMetaData-nonTraduit.action?pid=1410002201&csvLocale=en",
            'data_url': "https://www150.statcan.gc.ca/n1/en/tbl/csv/14100022-eng.zip?st=L0-nktSt"
        },
        'Vacancies': {
            'metadata_url': "https://www150.statcan.gc.ca/t1/tbl1/en/dtl!downloadCubeMetaData-nonTraduit.action?pid=1410044201&csvLocale=en", 
            'data_url': "https://www150.statcan.gc.ca/n1/en/tbl/csv/14100442-eng.zip?st=5EqdQNwS"
        }
    }
    
    # Check updates for both datasets
    updates_needed = {}
    current_dates = {}
    stored_dates = {}
    
    for name, config in datasets.items():
        current_date, stored_date, metadata_file = check_dataset_updates(
            name, config['metadata_url'], config['data_url']
        )
        
        force_download = args.force_download.lower() == "true"
        need_download = force_download or (current_date != stored_date and current_date is not None)
        
        updates_needed[name] = need_download
        current_dates[name] = current_date or 'unknown'
        stored_dates[name] = stored_date or 'none'
        
        print(f"Force download: {force_download}")
        print(f"Need download for {name}: {need_download}")
    
    # Determine if any updates are needed
    any_updates = any(updates_needed.values())
    
    # Create a combined date string for tagging
    if any_updates:
        # Use the most recent date for tagging
        valid_dates = [date for date in current_dates.values() if date != 'unknown']
        if valid_dates:
            combined_date = max(valid_dates)  # Use most recent date
        else:
            combined_date = datetime.now().strftime('%Y-%m')
    else:
        combined_date = 'no-update'
    
    # Set outputs for next step
    with open(args.output_file, 'a') as f:
        f.write(f"need_download={str(any_updates).lower()}\n")
        f.write(f"lfs_current_date={current_dates['LFS']}\n")
        f.write(f"lfs_stored_date={stored_dates['LFS']}\n")
        f.write(f"vacancies_current_date={current_dates['Vacancies']}\n")
        f.write(f"vacancies_stored_date={stored_dates['Vacancies']}\n")
        f.write(f"lfs_needs_update={str(updates_needed['LFS']).lower()}\n")
        f.write(f"vacancies_needs_update={str(updates_needed['Vacancies']).lower()}\n")
        f.write(f"combined_date={combined_date}\n")
    
    print(f"\nSummary:")
    print(f"Any updates needed: {any_updates}")
    print(f"LFS needs update: {updates_needed['LFS']}")
    print(f"Vacancies needs update: {updates_needed['Vacancies']}")
    print(f"Combined date: {combined_date}")


if __name__ == "__main__":
    main()