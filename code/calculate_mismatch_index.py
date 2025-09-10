import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import os

def create_geo_code_mapping():
    return {
        'Quebec': 'QC',
        'Ontario': 'ON',
        'Alberta': 'AB',
        'British Columbia': 'BC',
        'Saskatchewan': 'SK',
        'Manitoba': 'MB',
        'New Brunswick': 'NB',
        'Nova Scotia': 'NS',
        'Prince Edward Island': 'PE',
        'Newfoundland and Labrador': 'NL',
        'Yukon': 'YT',
        'Northwest Territories': 'NT',
        'Nunavut': 'NU'
    }

def convert_ref_date_to_stata_time(ref_date_str):
    try:
        date = pd.to_datetime(ref_date_str)
        base_date = pd.to_datetime('1960-01-01')
        return (date.year - base_date.year) * 12 + (date.month - base_date.month)
    except:
        return np.nan

def calculate_moving_average(series, window=6):
    ma = series.rolling(window=window, min_periods=1).mean()
    return ma.where(~series.isna(), np.nan)

def plot_quebec_only(df, alpha, output_dir='figures'):
    plt.rcParams.update({'font.size': 14})
    qc_data = df[df['region'] == 'QC'].copy()
    if qc_data.empty:
        print("No Quebec data found")
        return

    qc_data = qc_data.dropna(subset=['phi', 'vacancies', 'unemployment'])
    qc_grouped = qc_data.groupby('t').agg({'vacancies':'sum','unemployment':'sum'}).reset_index()
    qc_grouped.rename(columns={'vacancies':'v_agg_t','unemployment':'u_agg_t'}, inplace=True)
    qc_data = qc_data.merge(qc_grouped, on='t')

    qc_data['phi_component'] = (qc_data['phi']**(1/alpha)) * (qc_data['vacancies']/qc_data['v_agg_t'])
    barphi_by_t = qc_data.groupby('t')['phi_component'].sum().reset_index()
    barphi_by_t['barphi'] = barphi_by_t['phi_component']**alpha
    qc_data = qc_data.merge(barphi_by_t[['t','barphi']], on='t')

    qc_data['numerator_component'] = qc_data['phi'] * (qc_data['vacancies']**alpha) * (qc_data['unemployment']**(1-alpha))
    collapsed = qc_data.groupby('t').agg({
        'numerator_component':'sum',
        'v_agg_t':'first',
        'u_agg_t':'first',
        'barphi':'first'
    }).reset_index().rename(columns={'numerator_component':'numerator_sum'})

    collapsed['denominator'] = collapsed['barphi'] * (collapsed['v_agg_t']**alpha) * (collapsed['u_agg_t']**(1-alpha))
    collapsed['M'] = 1 - (collapsed['numerator_sum']/collapsed['denominator'])

    covid_mask = (collapsed['t'] >= 722) & (collapsed['t'] <= 728)
    collapsed.loc[covid_mask,'M'] = np.nan
    collapsed.loc[collapsed['M']==0,'M'] = np.nan

    collapsed = collapsed.sort_values('t')
    collapsed['M_ma6'] = calculate_moving_average(collapsed['M'],6)

    # Force start at April 2015 (t=660)
    collapsed = collapsed[collapsed['t'] >= 660]
    collapsed['date'] = pd.to_datetime('1960-01-01') + pd.to_timedelta(collapsed['t']*30.44, unit='D')

    fig, ax = plt.subplots(figsize=(12,6))
    ax.plot(collapsed['date'], collapsed['M'], color='lightblue', alpha=0.7, label='Monthly')
    ax.plot(collapsed['date'], collapsed['M_ma6'], color='red', linewidth=2, label='6-month MA')
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax.xaxis.set_major_locator(mdates.YearLocator())
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=0)
    ax.legend().set_visible(False)

    os.makedirs(output_dir, exist_ok=True)
    plt.savefig(f'{output_dir}/Mismatch Index in Quebec.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("Quebec mismatch index plot saved")

def plot_regional_qc_on(df, alpha, output_dir='figures'):
    plt.rcParams.update({'font.size': 14})
    regional_data = df[df['region'].isin(['QC','ON'])].copy()
    if regional_data.empty:
        print("No Quebec or Ontario data found")
        return

    regional_data = regional_data.dropna(subset=['phi','vacancies','unemployment'])
    
    # Calculate regional indices for QC and ON
    regional_agg = regional_data.groupby(['t','geo']).agg({'vacancies':'sum','unemployment':'sum'}).reset_index()
    regional_agg.rename(columns={'vacancies':'v_agg_it','unemployment':'u_agg_it'}, inplace=True)
    regional_data = regional_data.merge(regional_agg, on=['t','geo'])

    regional_data['phi_component'] = (regional_data['phi']**(1/alpha)) * (regional_data['vacancies']/regional_data['v_agg_it'])
    barphi_regional = regional_data.groupby(['t','geo'])['phi_component'].sum().reset_index()
    barphi_regional['barphi'] = barphi_regional['phi_component']**alpha
    regional_data = regional_data.merge(barphi_regional[['t','geo','barphi']], on=['t','geo'])

    regional_data['numerator_component'] = regional_data['phi'] * (regional_data['vacancies']**alpha) * (regional_data['unemployment']**(1-alpha))
    regional_collapsed = regional_data.groupby(['t','geo']).agg({
        'numerator_component':'sum',
        'v_agg_it':'first',
        'u_agg_it':'first',
        'barphi':'first'
    }).reset_index().rename(columns={'numerator_component':'numerator_sum_i'})

    regional_collapsed['denominator_i'] = regional_collapsed['barphi'] * (regional_collapsed['v_agg_it']**alpha) * (regional_collapsed['u_agg_it']**(1-alpha))
    regional_collapsed['M_p'] = 1 - (regional_collapsed['numerator_sum_i']/regional_collapsed['denominator_i'])

    regional_wide = regional_collapsed.pivot(index='t', columns='geo', values='M_p').reset_index()
    if 'ON' in regional_wide.columns: regional_wide.rename(columns={'ON':'M_ON'}, inplace=True)
    if 'QC' in regional_wide.columns: regional_wide.rename(columns={'QC':'M_QC'}, inplace=True)

    # Apply COVID mask and zero handling
    covid_mask = (regional_wide['t'] >= 722) & (regional_wide['t'] <= 728)
    for col in ['M_ON','M_QC']:
        if col in regional_wide.columns:
            regional_wide.loc[covid_mask,col] = np.nan
            regional_wide.loc[regional_wide[col]==0,col] = np.nan

    regional_wide = regional_wide.sort_values('t')
    for col in ['M_ON','M_QC']:
        if col in regional_wide.columns:
            regional_wide[f'{col}_ma6'] = calculate_moving_average(regional_wide[col],6)

    # Force start at April 2015
    regional_wide = regional_wide[regional_wide['t']>=660]
    regional_wide['date'] = pd.to_datetime('1960-01-01') + pd.to_timedelta(regional_wide['t']*30.44, unit='D')

    fig, ax = plt.subplots(figsize=(12,6))
    if 'M_ON_ma6' in regional_wide.columns:
        ax.plot(regional_wide['date'], regional_wide['M_ON_ma6'], color='red', linewidth=2, label='Ontario')
    if 'M_QC_ma6' in regional_wide.columns:
        ax.plot(regional_wide['date'], regional_wide['M_QC_ma6'], color='blue', linewidth=2, label='Quebec')

    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax.xaxis.set_major_locator(mdates.YearLocator())
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=0)
    ax.legend(loc='upper center', bbox_to_anchor=(0.5,-0.05), ncol=2, frameon=False)

    os.makedirs(output_dir, exist_ok=True)
    plt.savefig(f'{output_dir}/QC_ON_Mismatch.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("Quebec and Ontario mismatch index plot saved")

def plot_regional_qc_on_french(df, alpha, output_dir='figures'):
    plt.rcParams.update({'font.size': 14})
    regional_data = df[df['region'].isin(['QC','ON'])].copy()
    if regional_data.empty:
        print("No Quebec or Ontario data found")
        return

    regional_data = regional_data.dropna(subset=['phi','vacancies','unemployment'])
    
    # Calculate regional indices for QC and ON
    regional_agg = regional_data.groupby(['t','geo']).agg({'vacancies':'sum','unemployment':'sum'}).reset_index()
    regional_agg.rename(columns={'vacancies':'v_agg_it','unemployment':'u_agg_it'}, inplace=True)
    regional_data = regional_data.merge(regional_agg, on=['t','geo'])

    regional_data['phi_component'] = (regional_data['phi']**(1/alpha)) * (regional_data['vacancies']/regional_data['v_agg_it'])
    barphi_regional = regional_data.groupby(['t','geo'])['phi_component'].sum().reset_index()
    barphi_regional['barphi'] = barphi_regional['phi_component']**alpha
    regional_data = regional_data.merge(barphi_regional[['t','geo','barphi']], on=['t','geo'])

    regional_data['numerator_component'] = regional_data['phi'] * (regional_data['vacancies']**alpha) * (regional_data['unemployment']**(1-alpha))
    regional_collapsed = regional_data.groupby(['t','geo']).agg({
        'numerator_component':'sum',
        'v_agg_it':'first',
        'u_agg_it':'first',
        'barphi':'first'
    }).reset_index().rename(columns={'numerator_component':'numerator_sum_i'})

    regional_collapsed['denominator_i'] = regional_collapsed['barphi'] * (regional_collapsed['v_agg_it']**alpha) * (regional_collapsed['u_agg_it']**(1-alpha))
    regional_collapsed['M_p'] = 1 - (regional_collapsed['numerator_sum_i']/regional_collapsed['denominator_i'])

    regional_wide = regional_collapsed.pivot(index='t', columns='geo', values='M_p').reset_index()
    if 'ON' in regional_wide.columns: regional_wide.rename(columns={'ON':'M_ON'}, inplace=True)
    if 'QC' in regional_wide.columns: regional_wide.rename(columns={'QC':'M_QC'}, inplace=True)

    # Apply COVID mask and zero handling
    covid_mask = (regional_wide['t'] >= 722) & (regional_wide['t'] <= 728)
    for col in ['M_ON','M_QC']:
        if col in regional_wide.columns:
            regional_wide.loc[covid_mask,col] = np.nan
            regional_wide.loc[regional_wide[col]==0,col] = np.nan

    regional_wide = regional_wide.sort_values('t')
    for col in ['M_ON','M_QC']:
        if col in regional_wide.columns:
            regional_wide[f'{col}_ma6'] = calculate_moving_average(regional_wide[col],6)

    # Force start at April 2015
    regional_wide = regional_wide[regional_wide['t']>=660]
    regional_wide['date'] = pd.to_datetime('1960-01-01') + pd.to_timedelta(regional_wide['t']*30.44, unit='D')

    fig, ax = plt.subplots(figsize=(12,6))
    if 'M_ON_ma6' in regional_wide.columns:
        ax.plot(regional_wide['date'], regional_wide['M_ON_ma6'], color='red', linewidth=2, label='Ontario')
    if 'M_QC_ma6' in regional_wide.columns:
        ax.plot(regional_wide['date'], regional_wide['M_QC_ma6'], color='blue', linewidth=2, label='Québec')

    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax.xaxis.set_major_locator(mdates.YearLocator())
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=0)
    ax.legend(loc='upper center', bbox_to_anchor=(0.5,-0.05), ncol=2, frameon=False)

    os.makedirs(output_dir, exist_ok=True)
    plt.savefig(f'{output_dir}/QC_ON_Mismatch_FR.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("Quebec and Ontario mismatch index plot (French) saved")

def plot_quebec_industry_mismatch_contributions(df, alpha, output_dir='figures'):
    plt.rcParams.update({'font.size': 14})
    qc_data = df[df['region'] == 'QC'].copy()
    if qc_data.empty:
        print("No Quebec data found for industry contributions")
        return

    qc_data = qc_data.dropna(subset=['phi', 'vacancies', 'unemployment', 'industry'])

    # Step 1: Compute observed terms from the Stata code
    qc_data['term_obs'] = qc_data['phi'] * (qc_data['vacancies']**alpha) * (qc_data['unemployment']**(1-alpha))

    # Aggregate totals by t
    qc_grouped = qc_data.groupby('t').agg({
        'vacancies': 'sum',
        'unemployment': 'sum',
        'term_obs': 'sum'
    }).reset_index()
    qc_grouped.rename(columns={'vacancies': 'v_agg_t', 'unemployment': 'u_agg_t', 'term_obs': 'numerator_obs'}, inplace=True)
    qc_data = qc_data.merge(qc_grouped, on='t')

    # Compute barphi_t for the denominator
    qc_data['phi_component'] = (qc_data['phi']**(1/alpha)) * (qc_data['vacancies']/qc_data['v_agg_t'])
    barphi_by_t = qc_data.groupby('t')['phi_component'].sum().reset_index()
    barphi_by_t['barphi'] = barphi_by_t['phi_component']**alpha
    qc_data = qc_data.merge(barphi_by_t[['t', 'barphi']], on='t')

    # Denominator
    qc_data['denominator'] = qc_data['barphi'] * (qc_data['v_agg_t']**alpha) * (qc_data['u_agg_t']**(1-alpha))
    qc_data['M_obs'] = 1 - qc_data['numerator_obs']/qc_data['denominator']

    # Step 2: Calculate counterfactual terms from the Stata code
    qc_data['w_cf'] = qc_data['vacancies'] * (qc_data['phi']**(1/alpha))
    qc_grouped_cf = qc_data.groupby('t')['w_cf'].sum().reset_index()
    qc_grouped_cf.rename(columns={'w_cf': 'W_cf'}, inplace=True)
    qc_data = qc_data.merge(qc_grouped_cf, on='t')
    
    qc_data['u_cf'] = qc_data['u_agg_t'] * qc_data['w_cf'] / qc_data['W_cf']

    # Scaling factor 'k'
    qc_data['denom_other'] = qc_data['u_agg_t'] - qc_data['unemployment']
    # Avoid division by zero by using np.where
    qc_data['k'] = np.where(qc_data['denom_other'] > 0, (qc_data['u_agg_t'] - qc_data['u_cf']) / qc_data['denom_other'], np.nan)

    # Counterfactual numerator
    qc_data['self_part'] = qc_data['phi'] * (qc_data['vacancies']**alpha) * (qc_data['u_cf']**(1-alpha))
    qc_data['others_part'] = (qc_data['k']**(1-alpha)) * (qc_data['numerator_obs'] - qc_data['term_obs'])
    qc_data['numerator_cf'] = qc_data['self_part'] + qc_data['others_part']

    # Step 3: Calculate the contribution (delta)
    qc_data['M_cf'] = 1 - qc_data['numerator_cf']/qc_data['denominator']
    qc_data['contribution'] = qc_data['M_obs'] - qc_data['M_cf']

    # Pivot for plotting
    contrib_wide = qc_data.pivot(index='t', columns='industry', values='contribution')

    # Keep only selected industries for plotting
    industries = {
        "Wholesale and retail trade [41, 44-45]": "red",
        "Health care and social assistance [62]": "magenta",
        "Educational services [61]": "green",
        "Construction [23]": "gold",
        "Professional, scientific and technical services [54]": "purple"
    }

    # New dictionary for shortened legend labels
    shortened_industries = {
        "Wholesale and retail trade [41, 44-45]": "Wholesale & retail",
        "Health care and social assistance [62]": "Health care",
        "Educational services [61]": "Education",
        "Construction [23]": "Construction",
        "Professional, scientific and technical services [54]": "Prof. serv."
    }

    # Apply COVID mask
    covid_mask = (contrib_wide.index >= 722) & (contrib_wide.index <= 728)
    contrib_wide.loc[covid_mask] = np.nan

    # Force start at April 2015
    contrib_wide = contrib_wide[contrib_wide.index >= 660]
    contrib_wide['date'] = pd.to_datetime('1960-01-01') + pd.to_timedelta(contrib_wide.index*30.44, unit='D')

    # Smooth each series with 6-month MA
    for col in contrib_wide.columns.drop('date'):
        contrib_wide[col] = calculate_moving_average(contrib_wide[col], 6)

    # Plot multi-line chart
    fig, ax = plt.subplots(figsize=(12,6))
    for ind, color in industries.items():
        if ind in contrib_wide.columns:
            # Use the shortened label for the legend
            ax.plot(contrib_wide['date'], contrib_wide[ind], label=shortened_industries.get(ind, ind), color=color, linewidth=2)

    ax.set_ylabel("Contribution to mismatch index")
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax.xaxis.set_major_locator(mdates.YearLocator())
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=0)
    ax.legend(loc='upper center', bbox_to_anchor=(0.5,-0.10), ncol=3, frameon=False)

    os.makedirs(output_dir, exist_ok=True)
    plt.savefig(f'{output_dir}/QC_Industry_Mismatch_Contributions.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("Quebec industry mismatch contributions (smoothed) plot saved")

def plot_quebec_industry_mismatch_contributions_french(df, alpha, output_dir='figures'):
    plt.rcParams.update({'font.size': 14})
    qc_data = df[df['region'] == 'QC'].copy()
    if qc_data.empty:
        print("No Quebec data found for industry contributions")
        return

    qc_data = qc_data.dropna(subset=['phi', 'vacancies', 'unemployment', 'industry'])

    # Step 1: Compute observed terms from the Stata code
    qc_data['term_obs'] = qc_data['phi'] * (qc_data['vacancies']**alpha) * (qc_data['unemployment']**(1-alpha))

    # Aggregate totals by t
    qc_grouped = qc_data.groupby('t').agg({
        'vacancies': 'sum',
        'unemployment': 'sum',
        'term_obs': 'sum'
    }).reset_index()
    qc_grouped.rename(columns={'vacancies': 'v_agg_t', 'unemployment': 'u_agg_t', 'term_obs': 'numerator_obs'}, inplace=True)
    qc_data = qc_data.merge(qc_grouped, on='t')

    # Compute barphi_t for the denominator
    qc_data['phi_component'] = (qc_data['phi']**(1/alpha)) * (qc_data['vacancies']/qc_data['v_agg_t'])
    barphi_by_t = qc_data.groupby('t')['phi_component'].sum().reset_index()
    barphi_by_t['barphi'] = barphi_by_t['phi_component']**alpha
    qc_data = qc_data.merge(barphi_by_t[['t', 'barphi']], on='t')

    # Denominator
    qc_data['denominator'] = qc_data['barphi'] * (qc_data['v_agg_t']**alpha) * (qc_data['u_agg_t']**(1-alpha))
    qc_data['M_obs'] = 1 - qc_data['numerator_obs']/qc_data['denominator']

    # Step 2: Calculate counterfactual terms from the Stata code
    qc_data['w_cf'] = qc_data['vacancies'] * (qc_data['phi']**(1/alpha))
    qc_grouped_cf = qc_data.groupby('t')['w_cf'].sum().reset_index()
    qc_grouped_cf.rename(columns={'w_cf': 'W_cf'}, inplace=True)
    qc_data = qc_data.merge(qc_grouped_cf, on='t')
    
    qc_data['u_cf'] = qc_data['u_agg_t'] * qc_data['w_cf'] / qc_data['W_cf']

    # Scaling factor 'k'
    qc_data['denom_other'] = qc_data['u_agg_t'] - qc_data['unemployment']
    # Avoid division by zero by using np.where
    qc_data['k'] = np.where(qc_data['denom_other'] > 0, (qc_data['u_agg_t'] - qc_data['u_cf']) / qc_data['denom_other'], np.nan)

    # Counterfactual numerator
    qc_data['self_part'] = qc_data['phi'] * (qc_data['vacancies']**alpha) * (qc_data['u_cf']**(1-alpha))
    qc_data['others_part'] = (qc_data['k']**(1-alpha)) * (qc_data['numerator_obs'] - qc_data['term_obs'])
    qc_data['numerator_cf'] = qc_data['self_part'] + qc_data['others_part']

    # Step 3: Calculate the contribution (delta)
    qc_data['M_cf'] = 1 - qc_data['numerator_cf']/qc_data['denominator']
    qc_data['contribution'] = qc_data['M_obs'] - qc_data['M_cf']

    # Pivot for plotting
    contrib_wide = qc_data.pivot(index='t', columns='industry', values='contribution')

    # Keep only selected industries for plotting
    industries = {
        "Wholesale and retail trade [41, 44-45]": "red",
        "Health care and social assistance [62]": "magenta",
        "Educational services [61]": "green",
        "Construction [23]": "gold",
        "Professional, scientific and technical services [54]": "purple"
    }

    # French dictionary for shortened legend labels
    shortened_industries_french = {
        "Wholesale and retail trade [41, 44-45]": "Commerce de gros et détail",
        "Health care and social assistance [62]": "Soins de santé",
        "Educational services [61]": "Services d'enseignement",
        "Construction [23]": "Construction",
        "Professional, scientific and technical services [54]": "Serv. prof."
    }

    # Apply COVID mask
    covid_mask = (contrib_wide.index >= 722) & (contrib_wide.index <= 728)
    contrib_wide.loc[covid_mask] = np.nan

    # Force start at April 2015
    contrib_wide = contrib_wide[contrib_wide.index >= 660]
    contrib_wide['date'] = pd.to_datetime('1960-01-01') + pd.to_timedelta(contrib_wide.index*30.44, unit='D')

    # Smooth each series with 6-month MA
    for col in contrib_wide.columns.drop('date'):
        contrib_wide[col] = calculate_moving_average(contrib_wide[col], 6)

    # Plot multi-line chart
    fig, ax = plt.subplots(figsize=(12,6))
    for ind, color in industries.items():
        if ind in contrib_wide.columns:
            # Use the French shortened label for the legend
            ax.plot(contrib_wide['date'], contrib_wide[ind], label=shortened_industries_french.get(ind, ind), color=color, linewidth=2)

    ax.set_ylabel("Contribution à l'indice d'inadéquation")
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax.xaxis.set_major_locator(mdates.YearLocator())
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=0)
    ax.legend(loc='upper center', bbox_to_anchor=(0.5,-0.10), ncol=3, frameon=False)

    os.makedirs(output_dir, exist_ok=True)
    plt.savefig(f'{output_dir}/QC_Industry_Mismatch_Contributions_FR.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("Quebec industry mismatch contributions (French) plot saved")

def calculate_mismatch_indices(input_file='processed_data/final_data.csv', alpha=0.491, output_dir='figures'):
    try:
        df = pd.read_csv(input_file)
        print(f"Loaded dataset: {len(df)} rows")

        required_cols = ['phi','vacancies','unemployment','GEO','REF_DATE','industry']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            print(f"Missing required columns: {missing_cols}")
            return False

        geo_mapping = create_geo_code_mapping()
        df['region'] = df['GEO'].map(geo_mapping)
        df['t'] = df['REF_DATE'].apply(convert_ref_date_to_stata_time)
        df['geo'] = df['region']

        initial_rows = len(df)
        df = df.dropna(subset=['phi','t','vacancies','unemployment'])
        print(f"Removed {initial_rows-len(df)} rows with missing values")

        print("Generating Quebec mismatch index plot...")
        plot_quebec_only(df, alpha, output_dir)

        print("Generating Quebec and Ontario mismatch index plot...")
        plot_regional_qc_on(df, alpha, output_dir)
        
        print("Generating Quebec and Ontario mismatch index plot (French)...")
        plot_regional_qc_on_french(df, alpha, output_dir)
        
        print("Generating Quebec industry mismatch contributions plot...")
        plot_quebec_industry_mismatch_contributions(df, alpha, output_dir)

        print("Generating Quebec industry mismatch contributions plot (French)...")
        plot_quebec_industry_mismatch_contributions_french(df, alpha, output_dir)

        return True
    except Exception as e:
        print(f"Error calculating mismatch indices: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    calculate_mismatch_indices()