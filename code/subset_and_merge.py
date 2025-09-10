import pandas as pd

def create_geo_mapping():
    """
    Create mapping from phi dataset geo codes to main dataset geo names.
    """
    return {
        'AB': 'Alberta',
        'BC': 'British Columbia', 
        'ON': 'Ontario',
        'QC': 'Quebec',
        'SK': 'Saskatchewan',
        'MB': 'Manitoba',
        'NB': 'New Brunswick',
        'NS': 'Nova Scotia',
        'PE': 'Prince Edward Island',
        'NL': 'Newfoundland and Labrador',
        'YT': 'Yukon',
        'NT': 'Northwest Territories',
        'NU': 'Nunavut',
        # Regional groupings
        'Prairies': ['Alberta', 'Saskatchewan', 'Manitoba'],
        'Maritimes': ['New Brunswick', 'Nova Scotia', 'Prince Edward Island']
    }

def subset_and_merge():
    """
    Simple function to merge phi data with the main dataset.
    Expands phi values across all time periods for each geo x industry combination.
    """
    try:
        # Load the main dataset
        main_df = pd.read_csv('processed_data/merged_jvws_lfs.csv')
        print(f"Loaded main dataset: {len(main_df)} rows")
        
        # Load phi data from Stata file
        phi_df = pd.read_stata('data/phi.dta', preserve_dtypes=False)
        print(f"Loaded phi dataset: {len(phi_df)} rows")
        
        # Get unique REF_DATE values and geo mapping
        unique_dates = main_df['REF_DATE'].unique()
        geo_mapping = create_geo_mapping()
        print(f"Found {len(unique_dates)} unique dates")
        
        # Create expanded phi dataset (time-invariant values across all periods)
        expanded_phi_list = []
        
        for _, phi_row in phi_df.iterrows():
            phi_region = phi_row['region']
            
            # Handle regional groupings (Prairies, Maritimes)
            if phi_region in ['Prairies', 'Maritimes'] and isinstance(geo_mapping[phi_region], list):
                # For regional groupings, create entries for each province in the group
                mapped_geos = geo_mapping[phi_region]
            else:
                # For individual provinces, map to the full name
                mapped_geos = [geo_mapping.get(phi_region, phi_region)]  # fallback to original if not in mapping
            
            # Create entries for each mapped GEO and all REF_DATE values
            for mapped_geo in mapped_geos:
                for date in unique_dates:
                    expanded_row = {
                        'GEO': mapped_geo,
                        'industry': phi_row['i'],   # Map 'i' to 'industry' 
                        'REF_DATE': date,
                        'phi': phi_row['phi']
                    }
                    expanded_phi_list.append(expanded_row)
        
        # Convert to DataFrame
        expanded_phi_df = pd.DataFrame(expanded_phi_list)
        print(f"Created expanded phi dataset: {len(expanded_phi_df)} rows")
        
        # Merge with main dataset
        merged_df = main_df.merge(
            expanded_phi_df[['GEO', 'industry', 'REF_DATE', 'phi']], 
            on=['GEO', 'industry', 'REF_DATE'], 
            how='left'
        )
        
        print(f"Merged dataset: {len(merged_df)} rows")
        print(f"Non-null phi values: {merged_df['phi'].notna().sum()}")
        print(f"Null phi values: {merged_df['phi'].isna().sum()}")
        
        # Save the final result
        merged_df.to_csv('processed_data/final_data.csv', index=False)
        print("Successfully saved to processed_data/final_data.csv")
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    subset_and_merge()