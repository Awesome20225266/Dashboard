# Imports
import os
from datetime import datetime
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# Configuration
# DC capacity per inverter (example values)
DC_CAPACITY = {
    'INV1': 100,  # kW
    'INV2': 100,
    'INV3': 100,
    'INV4': 100,
    'INV5': 100,
    'INV6': 100,
}

data_folder = 'data'

# Data Processing
def get_file_signatures(folder: str) -> tuple:
    """Return a tuple of (file, mtime) for Excel files in the folder."""
    files = [os.path.join(folder, f) for f in os.listdir(folder)
             if f.lower().endswith(('.xls', '.xlsx'))]
    return tuple(sorted((f, os.path.getmtime(f)) for f in files))


@st.cache_data(show_spinner=False)
def load_data(folder: str, signatures: tuple) -> pd.DataFrame:
    """Load and merge all Excel files from a folder. If none found, generate
    dummy data."""
    files = [f for f, _ in signatures]
    if not files:
        # Generate dummy data when no Excel files found
        dates = pd.date_range(end=datetime.today(), periods=7)
        data = []
        sites = ['Site_A', 'Site_B', 'Site_C']
        inverters = list(DC_CAPACITY.keys())
        for date in dates:
            for site in sites:
                for inv in inverters:
                    record = {
                        'date': date.date(),
                        'site_name': site,
                        'inverter_id': inv,
                        'mppt_number': np.random.randint(1, 5),
                        'scb_id': np.random.choice([np.nan, f'SCB{np.random.randint(1,3)}']),
                        'energy_generated_kwh': np.random.uniform(300, 700),
                        'irradiance_kwh_m2': np.random.uniform(3, 7),
                        'dc_voltage_v': np.random.uniform(600, 800),
                        'dc_current_a': np.random.uniform(100, 200),
                        'ac_power_kw': np.random.uniform(80, 100),
                        'temperature_c': np.random.uniform(25, 55),
                    }
                    data.append(record)
        df = pd.DataFrame(data)
        return df

    df_list = [pd.read_excel(f) for f in files]
    df = pd.concat(df_list, ignore_index=True)
    return df


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """Standardize column names and handle date formats and missing values."""
    df = df.copy()
    # Lowercase column names and replace spaces with underscores
    df.columns = [c.strip().lower().replace(' ', '_') for c in df.columns]

    # Rename common variations if present
    rename_map = {
        'date': 'date',
        'site': 'site_name',
        'site_name': 'site_name',
        'inverter': 'inverter_id',
        'inverter_id': 'inverter_id',
        'energy_generated_(kwh)': 'energy_generated_kwh',
        'energy_generated': 'energy_generated_kwh',
        'irradiance_(kwh/m²)': 'irradiance_kwh_m2',
        'irradiance_kwh/m2': 'irradiance_kwh_m2',
        'dc_voltage_(v)': 'dc_voltage_v',
        'dc_current_(a)': 'dc_current_a',
        'ac_power_(kw)': 'ac_power_kw',
        'temperature_(°c)': 'temperature_c',
    }
    df.rename(columns=rename_map, inplace=True)

    # Parse dates
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date']).dt.date

    # Fill missing numeric values with 0
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    df[numeric_cols] = df[numeric_cols].fillna(0)

    return df


def compute_kpis(df: pd.DataFrame) -> pd.DataFrame:
    """Compute CUF, PR and Inverter Efficiency."""
    df = df.copy()
    df['dc_capacity'] = df['inverter_id'].map(DC_CAPACITY).fillna(0)
    df['cuf'] = (df['energy_generated_kwh'] / (df['dc_capacity'] * 24)) * 100
    df['pr'] = (df['energy_generated_kwh'] / (df['irradiance_kwh_m2'] * df['dc_capacity'])) * 100
    df['inverter_efficiency'] = (
        df['ac_power_kw'] / (df['dc_voltage_v'] * df['dc_current_a'])
    ) * 100
    return df


def detect_faults(df: pd.DataFrame) -> pd.DataFrame:
    """Detect faults based on rules and add fault_type column."""
    df = df.copy()
    fault_list = []
    for _, row in df.iterrows():
        faults = []
        if row['cuf'] < 15:
            faults.append('Low CUF')
        if row['pr'] < 75:
            faults.append('Low PR')
        if row['inverter_efficiency'] < 96:
            faults.append('Efficiency Loss')
        if row['dc_current_a'] == 0 and row['dc_voltage_v'] > 0:
            faults.append('String Disconnected')
        if row['temperature_c'] > 50:
            faults.append('High Temp')
        fault_list.append(', '.join(faults))
    df['fault_type'] = fault_list
    return df


# Export Functionality
def export_excel(df: pd.DataFrame, filename: str) -> None:
    """Export given DataFrame to Excel."""
    df.to_excel(filename, index=False)


# Dashboard UI
st.set_page_config(page_title='Solar Dashboard', layout='wide')
st.title('Solar Plant Performance Dashboard')

# Load and process data
signatures = get_file_signatures(data_folder)
raw_df = load_data(data_folder, signatures)
df = clean_data(raw_df)
df = compute_kpis(df)
df = detect_faults(df)

# Sidebar Filters
st.sidebar.header('Filters')
sites = df['site_name'].unique().tolist()
selected_site = st.sidebar.multiselect('Select Site', sites, default=sites)
min_date, max_date = df['date'].min(), df['date'].max()
start_date = st.sidebar.date_input('Start Date', min_value=min_date, max_value=max_date, value=min_date)
end_date = st.sidebar.date_input('End Date', min_value=min_date, max_value=max_date, value=max_date)
metric = st.sidebar.selectbox('Select Metric', ['cuf', 'pr', 'energy_generated_kwh'])

filtered_df = df[
    (df['site_name'].isin(selected_site)) &
    (df['date'] >= start_date) &
    (df['date'] <= end_date)
]

# Top Summary Cards
col1, col2, col3, col4 = st.columns(4)
with col1:
    total_energy = filtered_df['energy_generated_kwh'].sum()
    st.metric('Total Energy (kWh)', f"{total_energy:,.2f}")
with col2:
    avg_cuf = filtered_df['cuf'].mean()
    st.metric('Average CUF (%)', f"{avg_cuf:.2f}")
with col3:
    avg_pr = filtered_df['pr'].mean()
    st.metric('Average PR (%)', f"{avg_pr:.2f}")
with col4:
    fault_count = filtered_df[filtered_df['fault_type'] != ''].shape[0]
    st.metric('Number of Faults', int(fault_count))

st.divider()

# Visualization
st.header('Generation Overview')

# Line chart: Daily Generation per Site
line_data = filtered_df.groupby(['date', 'site_name'])['energy_generated_kwh'].sum().reset_index()
fig_line = px.line(line_data, x='date', y='energy_generated_kwh', color='site_name',
                   labels={'energy_generated_kwh': 'Energy (kWh)', 'date': 'Date', 'site_name': 'Site'})
st.plotly_chart(fig_line, use_container_width=True)

# Bar chart: CUF & PR by Inverter
bar_data = filtered_df.groupby('inverter_id').agg({'cuf': 'mean', 'pr': 'mean'}).reset_index()
fig_bar = px.bar(bar_data, x='inverter_id', y=['cuf', 'pr'], barmode='group',
                 labels={'value': 'Percentage', 'inverter_id': 'Inverter'})
fig_bar.update_layout(yaxis_title='%', legend_title='Metric')
st.plotly_chart(fig_bar, use_container_width=True)

# Heatmap: CUF over Dates (Site × Date)
heat_data = filtered_df.pivot_table(index='site_name', columns='date', values='cuf', aggfunc='mean')
fig_heat = px.imshow(heat_data, aspect='auto', color_continuous_scale='Viridis',
                     labels={'color': 'CUF (%)'})
st.plotly_chart(fig_heat, use_container_width=True)

# Efficiency Trend line: per inverter
eff_data = filtered_df.groupby(['date', 'inverter_id'])['inverter_efficiency'].mean().reset_index()
fig_eff = px.line(eff_data, x='date', y='inverter_efficiency', color='inverter_id',
                  labels={'inverter_efficiency': 'Efficiency (%)', 'inverter_id': 'Inverter'})
fig_eff.update_yaxes(range=[eff_data['inverter_efficiency'].min() - 1, eff_data['inverter_efficiency'].max() + 1])
st.plotly_chart(fig_eff, use_container_width=True)

# String-wise voltage/current graph (if data available)
if 'mppt_number' in filtered_df.columns:
    vc_data = filtered_df.groupby(['date', 'mppt_number']).agg({'dc_voltage_v': 'mean', 'dc_current_a': 'mean'}).reset_index()
    fig_vc = px.line(vc_data, x='date', y=['dc_voltage_v', 'dc_current_a'], color='mppt_number',
                     labels={'value': 'Value', 'mppt_number': 'MPPT', 'date': 'Date'})
    st.plotly_chart(fig_vc, use_container_width=True)

st.divider()

# Faults Table
st.header('Detected Faults')
fault_table = filtered_df[filtered_df['fault_type'] != ''][
    ['date', 'site_name', 'inverter_id', 'fault_type']
]
st.dataframe(fault_table, use_container_width=True)

# Export Buttons
st.sidebar.header('Export Data')
if st.sidebar.button('Export Filtered Data to Excel'):
    export_excel(filtered_df, 'filtered_data.xlsx')
    st.sidebar.success('Filtered data exported to filtered_data.xlsx')

if st.sidebar.button('Export Fault Table to Excel'):
    export_excel(fault_table, 'fault_table.xlsx')
    st.sidebar.success('Fault table exported to fault_table.xlsx')

# Auto refresh note
st.sidebar.info('Data refreshes automatically when new files are added to the data folder.')
