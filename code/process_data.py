#!/usr/bin/env python3
"""
Download and process Statistics Canada datasets.
"""

import argparse
import glob
import io
import numpy as np
import os
import pandas as pd
import requests
import zipfile
from datetime import datetime


def download_and_extract_csv(url, dataset_name):
    """Download zip file and extract CSV data to temporary location"""
    print(f"\nDownloading {dataset_name} data from {url}")
    
    response = requests.get(url)
    response.raise_for_status()
    
    # Extract CSV from zip
    with zipfile.ZipFile(io.BytesIO(response.content)) as zip_file:
        csv_files = [f for f in zip_file.namelist() if f.endswith('.csv') and not 'MetaData' in f]
        if csv_files:
            csv_file = csv_files[0]  # Take the first non-metadata CSV
            print(f"Extracting {csv_file}")
            
            with zip_file.open(csv_file) as csv_data:
                df = pd.read_csv(csv_data)
            
            # Save to temporary location (will be cleaned up)
            temp_file = f"temp_raw_data/{dataset_name.lower()}_raw.csv"
            os.makedirs("temp_raw_data", exist_ok=True)
            df.to_csv(temp_file, index=False)
            print(f"Temporarily saved raw data to {temp_file}")
            
            return df
        else:
            raise Exception(f"No CSV file found in {dataset_name} zip")


def clean_vacancies_data(df):
    """Clean vacancies dataset"""
    print("\n=== Cleaning Vacancies Data ===")
    
    # Rename column for consistency
    df = df.rename(columns={'North American Industry Classification System (NAICS)': 'industry'})
    
    # Define baseline categories
    baseline_mapping = {
        'Administrative and support, waste management and remediation services [56]': 'Business, building and other support services [55, 56]',
        'Management of companies and enterprises [55]': 'Business, building and other support services [55, 56]',
        'Mining, quarrying, and oil and gas extraction [21]': 'Forestry, fishing, mining, quarrying, oil and gas [21]',
        'Information and cultural industries [51]': 'Information, culture and recreation [51, 71]',
        'Arts, entertainment and recreation [71]': 'Information, culture and recreation [51, 71]',
        'Wholesale trade [41]': 'Wholesale and retail trade [41, 44-45]',
        'Retail trade [44-45]': 'Wholesale and retail trade [41, 44-45]'
    }
    
    # Apply mappings
    df['industry'] = df['industry'].replace(baseline_mapping)
    
    # Define industries to keep
    keep_industries = [
        "Accommodation and food services [72]",
        "Business, building and other support services [55, 56]", 
        "Construction [23]",
        "Educational services [61]",
        "Finance and insurance [52]",
        "Health care and social assistance [62]",
        "Information, culture and recreation [51, 71]",
        "Other services (except public administration) [81]",
        "Professional, scientific and technical services [54]",
        "Public administration [91]",
        "Real estate and rental and leasing [53]",
        "Transportation and warehousing [48-49]",
        "Wholesale and retail trade [41, 44-45]",
        "Manufacturing [31-33]"
    ]
    
    # Filter to keep only baseline industries
    df = df[df['industry'].isin(keep_industries)].copy()
    
    # Aggregate by industry, date, geography, and statistics
    df = df.groupby(['industry', 'REF_DATE', 'GEO', 'Statistics'])['VALUE'].sum().reset_index()
    
    # Pivot statistics to columns
    df_pivot = df.pivot_table(
        index=['REF_DATE', 'GEO', 'industry'], 
        columns='Statistics', 
        values='VALUE'
    ).reset_index()
    
    # Flatten column names
    df_pivot.columns.name = None
    
    # Rename columns to match Stata output
    column_mapping = {
        'Average offered hourly wage': 'avg_hourly_wage_offer',
        'Job vacancies': 'vacancies', 
        'Job vacancy rate': 'vacancy_rate',
        'Payroll employees': 'payroll_employees'
    }
    df_pivot = df_pivot.rename(columns=column_mapping)
    
    # Expand quarterly data to monthly (duplicate each quarter to 3 months)
    expanded_rows = []
    
    for _, row in df_pivot.iterrows():
        ref_date = row['REF_DATE']
        year = ref_date[:4]
        quarter_month = ref_date[5:7]
        
        # Map quarters to months
        quarter_to_months = {
            '01': ['01', '02', '03'],
            '04': ['04', '05', '06'], 
            '07': ['07', '08', '09'],
            '10': ['10', '11', '12']
        }
        
        if quarter_month in quarter_to_months:
            for month in quarter_to_months[quarter_month]:
                new_row = row.copy()
                new_row['REF_DATE'] = f"{year}-{month}"
                expanded_rows.append(new_row)
    
    result_df = pd.DataFrame(expanded_rows)
    
    print(f"Vacancies data cleaned. Shape: {result_df.shape}")
    return result_df


def clean_lfs_data(df):
    """Clean LFS dataset"""
    print("\n=== Cleaning LFS Data ===")
    
    # Filter for Total Gender and 15 years and over
    df_filtered = df[
        (df['Gender'] == 'Total - Gender') & 
        (df['Age group'] == '15 years and over')
    ].copy()
    
    if df_filtered.shape[0] == 0:
        print("ERROR: No data remains after gender/age filtering!")
        return pd.DataFrame()
    
    # Rename column for consistency
    if 'North American Industry Classification System (NAICS)' in df_filtered.columns:
        df_filtered = df_filtered.rename(columns={'North American Industry Classification System (NAICS)': 'industry'})
    elif 'industry' not in df_filtered.columns:
        print("ERROR: No industry column found!")
        return pd.DataFrame()
    
    # Apply same industry mappings as vacancies
    baseline_mapping = {
        'Administrative and support, waste management and remediation services [56]': 'Business, building and other support services [55, 56]',
        'Management of companies and enterprises [55]': 'Business, building and other support services [55, 56]',
        'Mining, quarrying, and oil and gas extraction [21]': 'Forestry, fishing, mining, quarrying, oil and gas [21]',
        'Information and cultural industries [51]': 'Information, culture and recreation [51, 71]',
        'Arts, entertainment and recreation [71]': 'Information, culture and recreation [51, 71]',
        'Wholesale trade [41]': 'Wholesale and retail trade [41, 44-45]',
        'Retail trade [44-45]': 'Wholesale and retail trade [41, 44-45]'
    }
    
    df_filtered['industry'] = df_filtered['industry'].replace(baseline_mapping)
    
    # Define industries to keep (same as vacancies)
    keep_industries = [
        "Accommodation and food services [72]",
        "Business, building and other support services [55, 56]", 
        "Construction [23]",
        "Educational services [61]",
        "Finance and insurance [52]",
        "Health care and social assistance [62]",
        "Information, culture and recreation [51, 71]",
        "Other services (except public administration) [81]",
        "Professional, scientific and technical services [54]",
        "Public administration [91]",
        "Real estate and rental and leasing [53]",
        "Transportation and warehousing [48-49]",
        "Wholesale and retail trade [41, 44-45]",
        "Manufacturing [31-33]"
    ]
    
    # Filter industries
    df_filtered = df_filtered[df_filtered['industry'].isin(keep_industries)].copy()
    
    if df_filtered.shape[0] == 0:
        print("ERROR: No data remains after industry filtering!")
        return pd.DataFrame()
    
    # Check for required columns
    required_cols = ['industry', 'REF_DATE', 'GEO', 'Labour force characteristics', 'VALUE']
    missing_cols = [col for col in required_cols if col not in df_filtered.columns]
    if missing_cols:
        print(f"ERROR: Missing required columns: {missing_cols}")
        return pd.DataFrame()
    
    # Aggregate by industry, date, geography, and labour force characteristics
    df_agg = df_filtered.groupby(['industry', 'REF_DATE', 'GEO', 'Labour force characteristics'])['VALUE'].sum().reset_index()
    
    # Pivot labour force characteristics to columns
    df_pivot = df_agg.pivot_table(
        index=['REF_DATE', 'GEO', 'industry'], 
        columns='Labour force characteristics', 
        values='VALUE'
    ).reset_index()
    
    # Flatten column names
    df_pivot.columns.name = None
    
    # Rename columns to match Stata output
    column_mapping = {
        'Employment': 'employment',
        'Full-time employment': 'fulltime_employment',
        'Labour force': 'labour_force', 
        'Part-time employment': 'parttime_employment',
        'Unemployment': 'unemployment',
        'Unemployment rate': 'unemployment_rate'
    }
    df_pivot = df_pivot.rename(columns=column_mapping)
    
    # Convert from thousands to individuals (multiply by 1000)
    scale_columns = ['employment', 'fulltime_employment', 'labour_force', 'parttime_employment', 'unemployment']
    for col in scale_columns:
        if col in df_pivot.columns:
            df_pivot[col] = df_pivot[col] * 1000
    
    print(f"LFS data cleaned. Shape: {df_pivot.shape}")
    return df_pivot


def merge_datasets(lfs_df, vacancies_df):
    """Merge LFS and JVWS datasets"""
    print("\n=== Merging Datasets ===")
    
    # Filter out territories (keep only provinces)
    territories = ['Northwest Territories', 'Nunavut', 'Yukon']
    lfs_df = lfs_df[~lfs_df['GEO'].isin(territories)].copy()
    vacancies_df = vacancies_df[~vacancies_df['GEO'].isin(territories)].copy()

    # Perform an inner merge to keep only matching rows from both datasets
    merged_df = pd.merge(
        lfs_df, 
        vacancies_df, 
        on=['REF_DATE', 'GEO', 'industry'], 
        how='inner'
    )
    
    # Handle zero vacancies as missing
    merged_df.loc[merged_df['vacancies'] == 0, 'vacancies'] = np.nan
    merged_df.loc[merged_df['vacancy_rate'] == 0, 'vacancy_rate'] = np.nan
    
    # Drop problematic industries
    drop_industries = [
        'Utilities [22]',
        'Finance, insurance, real estate, rental and leasing [52, 53]',
        'Forestry, fishing, mining, quarrying, oil and gas [21]'
    ]
    merged_df = merged_df[~merged_df['industry'].isin(drop_industries)].copy()
    
    print(f"Final merged dataset shape: {merged_df.shape}")
    return merged_df


def cleanup_temp_files():
    """Remove temporary raw data files after processing"""
    print("Cleaning up temporary files...")
    patterns = ['temp_raw_data/*.csv']
    
    for pattern in patterns:
        for file in glob.glob(pattern):
            try:
                os.remove(file)
            except Exception as e:
                print(f"Could not remove {file}: {e}")
    
    # Remove temp directory if empty
    try:
        os.rmdir('temp_raw_data')
    except:
        pass


def cleanup_old_files():
    """Remove old data files to keep only final merged dataset"""
    print("Cleaning up old data files...")
    
    # Remove old raw data and intermediate files, keep only final merged dataset
    patterns = [
        'data/*SDMX*.zip', 
        'data/metadata*.csv',
        'raw_data/*.csv',
        'processed_data/lfs_clean.csv',
        'processed_data/vacancies_clean.csv'
    ]
    
    for pattern in patterns:
        for file in glob.glob(pattern):
            try:
                os.remove(file)
            except Exception as e:
                print(f"Could not remove {file}: {e}")


def main():
    parser = argparse.ArgumentParser(description='Process Statistics Canada data')
    parser.add_argument('--lfs-needs-update', type=str, required=True,
                       help='Whether LFS data needs updating (true/false)')
    parser.add_argument('--vacancies-needs-update', type=str, required=True,
                       help='Whether vacancies data needs updating (true/false)')
    parser.add_argument('--lfs-current-date', type=str, required=True,
                       help='Current LFS reference date')
    parser.add_argument('--vacancies-current-date', type=str, required=True,
                       help='Current vacancies reference date')
    
    args = parser.parse_args()
    
    # Create necessary directories
    os.makedirs("processed_data", exist_ok=True)
    os.makedirs("data", exist_ok=True)
    
    # Download datasets if needed
    datasets = {
        'LFS': "https://www150.statcan.gc.ca/n1/en/tbl/csv/14100022-eng.zip?st=L0-nktSt",
        'Vacancies': "https://www150.statcan.gc.ca/n1/en/tbl/csv/14100442-eng.zip?st=5EqdQNwS"
    }
    
    lfs_needs_update = args.lfs_needs_update.lower() == "true"
    vacancies_needs_update = args.vacancies_needs_update.lower() == "true"
    
    # Clean up old files first
    cleanup_old_files()
    
    # Download and clean data
    if lfs_needs_update:
        lfs_raw = download_and_extract_csv(datasets['LFS'], 'LFS')
        lfs_clean = clean_lfs_data(lfs_raw)
        # Don't save intermediate clean file
    else:
        print("LFS data not updated, loading existing clean data...")
        if os.path.exists('processed_data/merged_jvws_lfs.csv'):
            # Try to extract LFS data from existing merged file if available
            print("Using existing merged dataset...")
            merged_existing = pd.read_csv('processed_data/merged_jvws_lfs.csv')
            lfs_columns = ['REF_DATE', 'GEO', 'industry', 'employment', 'fulltime_employment', 
                          'labour_force', 'parttime_employment', 'unemployment', 'unemployment_rate']
            lfs_clean = merged_existing[lfs_columns].dropna(subset=['employment']).copy()
        else:
            # If no existing data, download anyway
            print("No existing data found, downloading...")
            lfs_raw = download_and_extract_csv(datasets['LFS'], 'LFS')
            lfs_clean = clean_lfs_data(lfs_raw)
    
    if vacancies_needs_update:
        vacancies_raw = download_and_extract_csv(datasets['Vacancies'], 'Vacancies')
        vacancies_clean = clean_vacancies_data(vacancies_raw)
        # Don't save intermediate clean file
    else:
        print("Vacancies data not updated, loading existing clean data...")
        if os.path.exists('processed_data/merged_jvws_lfs.csv'):
            # Try to extract vacancies data from existing merged file if available
            merged_existing = pd.read_csv('processed_data/merged_jvws_lfs.csv')
            vacancies_columns = ['REF_DATE', 'GEO', 'industry', 'avg_hourly_wage_offer', 
                               'vacancies', 'vacancy_rate', 'payroll_employees']
            vacancies_clean = merged_existing[vacancies_columns].dropna(subset=['vacancies']).copy()
        else:
            # If no existing data, download anyway
            print("No existing vacancies data found, downloading...")
            vacancies_raw = download_and_extract_csv(datasets['Vacancies'], 'Vacancies')
            vacancies_clean = clean_vacancies_data(vacancies_raw)
    
    # Merge datasets and save only final merged dataset
    merged_data = merge_datasets(lfs_clean, vacancies_clean)
    merged_data.to_csv('processed_data/merged_jvws_lfs.csv', index=False)
    print("Saved final merged dataset to processed_data/merged_jvws_lfs.csv")
    
    # Clean up temporary files
    cleanup_temp_files()
    
    # Update reference date files (keep these for tracking)
    if lfs_needs_update:
        with open('data/last_reference_date_lfs.txt', 'w') as f:
            f.write(args.lfs_current_date)
    if vacancies_needs_update:
        with open('data/last_reference_date_vacancies.txt', 'w') as f:
            f.write(args.vacancies_current_date)
    
    # Create download log (keep this for tracking)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open('data/download_log.txt', 'a') as f:
        if lfs_needs_update:
            f.write(f"{timestamp}: Downloaded and processed LFS data (ref period: {args.lfs_current_date})\n")
        if vacancies_needs_update:
            f.write(f"{timestamp}: Downloaded and processed Vacancies data (ref period: {args.vacancies_current_date})\n")
    
    print("\n=== Data Processing Complete ===")
    print("Final file created:")
    print("  processed_data/merged_jvws_lfs.csv")
    print("Tracking files updated:")
    for tracking_file in glob.glob('data/last_reference_date_*.txt') + ['data/download_log.txt']:
        if os.path.exists(tracking_file):
            print(f"  {tracking_file}")


if __name__ == "__main__":
    main()