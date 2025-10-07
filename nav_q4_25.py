# =================================== IMPORTS ================================= #

import os

# import json
import numpy as np 
import pandas as pd 
from datetime import datetime, timedelta
from collections import Counter

# import seaborn as sns 
import plotly.graph_objects as go
import plotly.express as px

import time
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
import folium
from folium.plugins import MousePosition

import dash
from dash import dcc, html, dash_table

# Google Web Credentials
import json
import base64
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# 'data/~$bmhc_data_2024_cleaned.xlsx'
# print('System Version:', sys.version)
# =================================== DATA ==================================== #

current_dir = os.getcwd()
current_file = os.path.basename(__file__)
script_dir = os.path.dirname(os.path.abspath(__file__))
# data_path = 'data/Navigation_Responses.xlsx'
# file_path = os.path.join(script_dir, data_path)
# data = pd.read_excel(file_path)
# df = data.copy()

# Define the Google Sheets URL
sheet_url = "https://docs.google.com/spreadsheets/d/1Vi5VQWt9AD8nKbO78FpQdm6TrfRmg0o7az77Hku2i7Y/edit#gid=78776635"
# Define the scope
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

# Load credentials
encoded_key = os.getenv("GOOGLE_CREDENTIALS")
if encoded_key:
    json_key = json.loads(base64.b64decode(encoded_key).decode("utf-8"))
    creds = ServiceAccountCredentials.from_json_keyfile_dict(json_key, scope)
else:
    creds_path = r"C:\Users\CxLos\OneDrive\Documents\BMHC\Data\bmhc-timesheet-4808d1347240.json"
    if os.path.exists(creds_path):
        creds = ServiceAccountCredentials.from_json_keyfile_name(creds_path, scope)
    else:
        raise FileNotFoundError("Service account JSON file not found and GOOGLE_CREDENTIALS is not set.")

# Authorize and load the sheet
client = gspread.authorize(creds)
sheet = client.open_by_url(sheet_url)
data = pd.DataFrame(client.open_by_url(sheet_url).sheet1.get_all_records())
df = data.copy()

# Trim leading and trailing whitespaces from column names
df.columns = df.columns.str.strip()

# Get the reporting month:
current_month = datetime(2025, 10, 1).strftime("%B")
report_year = datetime(2025, 10, 1).year
int_month = 10

df['Date of Activity'] = pd.to_datetime(df['Date of Activity'], errors='coerce')
df = df[(df['Date of Activity'] >= '2025-7-01') & (df['Date of Activity'] <= '2025-9-30')]
df['Month'] = df['Date of Activity'].dt.month_name()

df = df.sort_values(by='Date of Activity', ascending=True)

# Strip whitespace
df.columns = df.columns.str.strip()

# Strip whitespace from string entries in the whole DataFrame
for col in df.select_dtypes(include='object').columns:
    df[col] = df[col].map(lambda x: x.strip() if isinstance(x, str) else x)

# df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)

# Define a discrete color sequence
# color_sequence = px.colors.qualitative.Plotly

# -----------------------------------------------
# print(df.head(15))
# print('Total entries: ', len(df))
# print('Column Names: \n', df.columns.tolist())
# print('Column Names: \n', df1.columns)
# print('DF Shape:', df.shape)
# print('Dtypes: \n', df.dtypes)
# print('Info:', df.info())
# print("Amount of duplicate rows:", df.duplicated().sum())

# print('Current Directory:', current_dir)
# print('Script Directory:', script_dir)
# print('Path to data:',file_path)

# ================================= Columns Navigation ================================= #

columns = [
    'Timestamp', 
    'Date of Activity', 
    'Person submitting this form:', 
    'Activity Duration (minutes):', 
    'Location Encountered:',
    "Individual's First Name:", 
    "Individual's Last Name:"
    "Individual's Date of Birth:", 
    "Individual's Insurance Status:", 
    "Individual's street address:", 
    'City:', 
    'ZIP Code:', 
    'County:', 
    'Type of support given:', 
    'Provide brief support description:', 
    "Individual's Status:", 
    'HMIS SPID Number:', 
    'MAP Card Number', 
    'Gender:', 
    'Race/Ethnicity:',
    'Total travel time (minutes):', 
    'Direct Client Assistance Amount:', 
    'Column 21', 
  ]

# ============================== Data Preprocessing ========================== #

# # Fill missing values for numerical columns with a specific value (e.g., -1)
df['HMIS SPID Number:'] = df['HMIS SPID Number:'].fillna(-1)
df['MAP Card Number'] = df['MAP Card Number'].fillna(-1)

df.rename(
    columns={
        "Activity Duration (minutes):" : "Activity Duration",
        "Total travel time (minutes):" : "Travel",
        "Person submitting this form:" : "Person",
        "Location Encountered:" : "Location",
        "Individual's Insurance Status:" : "Insurance",
        "Individual's Status:" : "Status",
        "Type of support given:" : "Support",
        "Gender:" : "Gender",
        "Race/Ethnicity:" : "Ethnicity",
        "Provide brief support description:" : "Description",
        # "" : "",
    }, 
inplace=True)

# Get the reporting quarter:
def get_custom_quarter(date_obj):
    month = date_obj.month
    if month in [10, 11, 12]:
        return "Q1"  # October–December
    elif month in [1, 2, 3]:
        return "Q2"  # January–March
    elif month in [4, 5, 6]:
        return "Q3"  # April–June
    elif month in [7, 8, 9]:
        return "Q4"  # July–September

# Reporting Quarter (use last month of the quarter)
report_date = datetime(2025, 7, 1) 
month = report_date.month
report_year = report_date.year
current_quarter = get_custom_quarter(report_date)
# print(f"Reporting Quarter: {current_quarter}")

# Adjust the quarter calculation for custom quarters
if month in [10, 11, 12]:
    quarter = 1  # Q1: October–December
elif month in [1, 2, 3]:
    quarter = 2  # Q2: January–March
elif month in [4, 5, 6]:
    quarter = 3  # Q3: April–June
elif month in [7, 8, 9]:
    quarter = 4  # Q4: July–September

# Define a mapping for months to their corresponding quarter
quarter_months = {
    1: ['October', 'November', 'December'],  # Q1
    2: ['January', 'February', 'March'],    # Q2
    3: ['April', 'May', 'June'],            # Q3
    4: ['July', 'August', 'September']      # Q4
}

# Get the months for the current quarter
months_in_quarter = quarter_months[quarter]

# Calculate start and end month indices for the quarter
all_months = [
    'January', 'February', 'March', 
    'April', 'May', 'June',
    'July', 'August', 'September', 
    'October', 'November', 'December'
]
start_month_idx = (quarter - 1) * 3
month_order = all_months[start_month_idx:start_month_idx + 3]

# ------------------------------- Clients Serviced ---------------------------- #

# # Clients Serviced:
clients_served = len(df)
clients_served = str(clients_served)
# print('Patients Served This Month:', clients_served)

df['Clients Served'] = len(df)

clients = []
for month in months_in_quarter:
    clients_in_month = df[df['Month'] == month].shape[0]  # Count the number of rows for each month
    clients.append(clients_in_month)
    # print(f'Clients Served in {month}:', clients_in_month)

# Create a DataFrame with the results for plotting
df_clients = pd.DataFrame(
    {
    'Month': months_in_quarter,
    'Clients Served': clients
    }
)

# print(df_clients)

client_bar = px.bar(
    df_clients, 
    x='Month', 
    y='Clients Served',
    labels={'Clients Served': 'Number of Clients'},
    color='Month',  # Color the bars by month
    text='Clients Served',  # Display the value on top of the bars
).update_layout(
    title_x=0.5,
    xaxis_title='Month',
    yaxis_title='Count',
    title=dict(
        text= f'{current_quarter} Clients Served by Month',
        x=0.5, 
        font=dict(
            size=21,
            family='Calibri',
            color='black',
            )
    ),
    font=dict(
        family='Calibri',
        size=16,
        color='black'
    ),
    xaxis=dict(
        title=dict(
            text=None,
            # text="Month",
            font=dict(size=16),  # Font size for the title
        ),
        tickmode='array',
        tickvals=df_clients['Month'].unique(),
        tickangle=0  # Rotate x-axis labels for better readability
    ),
    legend=dict(
        # title='Administrative Activity',
        title=None,
        orientation="v",  # Vertical legend
        x=1.05,  # Position legend to the right
        xanchor="left",  # Anchor legend to the left
        y=1,  # Position legend at the top
        yanchor="top"  # Anchor legend at the top
    ),
).update_traces(
    texttemplate='%{text}',  # Display the count value above bars
    textfont=dict(size=16),  # Increase text size in each bar
    textposition='auto',  # Automatically position text above bars
    textangle=0, # Ensure text labels are horizontal
    hovertemplate=(  # Custom hover template
        '<b>Name</b>: %{label}<br><b>Count</b>: %{y}<extra></extra>'  
    ),
)

client_pie = px.pie(
    df_clients,
    names='Month',
    values='Clients Served',
    color='Month',
).update_layout(
    title=dict(
        x=0.5,
        text=f'{current_quarter} Ratio of Clients Served',  # Title text
        font=dict(
            size=21,  # Increase this value to make the title bigger
            family='Calibri',  # Optional: specify font family
            color='black'  # Optional: specify font color
        ),
    ),  # Center-align the title
).update_traces(
    rotation=180,  # Rotate pie chart 90 degrees counterclockwise
    textfont=dict(size=19),  # Increase text size in each bar
    # textinfo='value+percent',
    texttemplate='%{value}<br>(%{percent:.0%})',
    hovertemplate='<b>%{label}</b>: %{value}<extra></extra>'
)

# ------------------------------ Navigation Hours ---------------------------- #

# print("Activity Duration Unique: \n", df['Activity Duration'].unique().tolist())

# # Groupby Activity Duration:
df_duration = df['Activity Duration'].sum()/60
df_duration = round(df_duration) 
# # print('Activity Duration:', df_duration/60, 'hours')

# ------------------------------ Travel Time ---------------------------- #

# 0     124
# 60      3
# 30      3
# 45      1

# print('Travel time unique values:', df['Total travel time (minutes):'].unique())
# print(df['Total travel time (minutes):'].value_counts())

# Clean and replace invalid values
df['Travel'] = (
    df['Travel']
    .astype(str)
    .str.strip()
    .replace({'The Bumgalows': '0'})
)

# Convert to float
df['Travel'] = pd.to_numeric(df['Travel'], errors='coerce')

# Fill NaNs with 0
df['Travel'] = df['Travel'].fillna(0)

# Calculate total travel time in hours
travel_time = round(df['Travel'].sum() / 60)

# print('Travel Time dtype:', df['Total travel time (minutes):'].dtype)
# print('Total Travel Time:', travel_time)

# Calculate total travel time per month
travel_hours = []
for month in months_in_quarter:
    hours_in_month = df[df['Month'] == month]['Travel'].sum() / 60
    hours_in_month = round(hours_in_month)
    travel_hours.append(hours_in_month)
    # print(f'Travel Time in {month}:', hours_in_month)

df_travel = pd.DataFrame({
    'Month': months_in_quarter,
    'Travel Time': travel_hours
})

# Bar chart
travel_bar = px.bar(
    df_travel,
    x='Month',
    y='Travel Time',
    barmode='group', 
    color='Month',
    text='Travel Time',
    labels={
        'Travel Time': 'Travel Time (hours)',
        'Month': 'Month'
    }
).update_layout(
    title_x=0.5,
    xaxis_title='Month',
    yaxis_title='Travel Time (hours)',
    title=dict(
        text=f'{current_quarter} Travel Time by Month',
        x=0.5, 
        font=dict(
            size=21,
            family='Calibri',
            color='black',
            )
    ),
    font=dict(
        family='Calibri',
        size=16,
        color='black'
    ),
    xaxis=dict(
        title=dict(
            text=None,
            font=dict(size=16),
        ),
        tickmode='array',
        tickvals=df_travel['Month'].unique(),
        tickangle=0
    ),
).update_traces(
    texttemplate='%{text}',
    textfont=dict(size=16),
    textposition='auto',
    textangle=0,
    hovertemplate='<b>Month</b>: %{label}<br><b>Travel Time</b>: %{y} hours<extra></extra>',
).add_annotation(
    # x='January',  # Specify the x-axis value
    # # y=df_nav_hours.loc[df_nav_hours['Month'] == 'January', 'Minutes'].values[0] - 10,  # Position slightly above the bar
    # text='No data',  # Annotation text
    # showarrow=False,  # Hide the arrow
    # font=dict(size=30, color='red'),  # Customize font size and color
    # align='center',  # Center-align the text
)

# Pie chart
travel_pie = px.pie(
    df_travel,
    names='Month',
    values='Travel Time',
    color='Month',
).update_layout(
    title=dict(
        x=0.5,
        text=f'{current_quarter} Travel Time Ratio',
        font=dict(
            size=21,
            family='Calibri',
            color='black'
        ),
    ),
).update_traces(
    rotation=180,
    textfont=dict(size=16),
    # textinfo='value+percent',
    texttemplate='%{value}<br>(%{percent:.0%})',
    hovertemplate='<b>%{label}</b>: %{value} hours<extra></extra>'
)

# ------------------------------- Race Graphs ---------------------------- #

df['Ethnicity'] = (
    df['Ethnicity']
        .astype(str)
        .str.strip()
        .replace({
            "Hispanic/Latino": "Hispanic/ Latino", 
            "White": "White/ European Ancestry", 
            "Group search": "N/A", 
        })
)

# Calculate race distribution per month
race_data = []
for month in months_in_quarter:
    month_data = df[df['Month'] == month]['Ethnicity'].value_counts().reset_index()
    month_data.columns = ['Ethnicity', 'Count']
    month_data['Month'] = month
    race_data.append(month_data)

# Combine all months
df_race_quarterly = pd.concat(race_data, ignore_index=True)

# Get overall race distribution for pie chart
df_race = df['Ethnicity'].value_counts().reset_index(name='Count')

# Race Bar Chart - Quarterly Format
race_bar = px.bar(
    df_race_quarterly,
    x='Month',
    y='Count',
    color='Ethnicity',
    barmode='group',
    text='Count',
    category_orders={'Month': months_in_quarter}
).update_layout(
    title_x=0.5,
    xaxis_title='Month',
    yaxis_title='Count',
    title=dict(
        text=f'{current_quarter} Race Distribution by Month',
        x=0.5, 
        font=dict(
            size=21,
            family='Calibri',
            color='black',
        )
    ),
    font=dict(
        family='Calibri',
        size=16,
        color='black'
    ),
    xaxis=dict(
        title=dict(
            text=None,
            font=dict(size=20),
        ),
        tickmode='array',
        tickvals=months_in_quarter,
        tickangle=0
    ),
    legend=dict(
        title='Race/Ethnicity',
        orientation="v",
        x=1.05,
        xanchor="left",
        y=1,
        yanchor="top"
    ),
).update_traces(
    texttemplate='%{text}',
    textfont=dict(size=16),
    textposition='auto',
    textangle=0,
    # Fixed hover template - use %{fullData.name} for race instead of %{legendgroup}
    hovertemplate='<b>Month</b>: %{x}<br><b>Race</b>: %{fullData.name}<br><b>Count</b>: %{y}<extra></extra>'
)

# Race Pie Chart - Overall Distribution
race_pie = px.pie(
    df_race,
    names='Ethnicity',
    values='Count'
).update_layout(
    title=dict(
        text=f'{current_quarter} Race Distribution Ratio',
        x=0.5, 
        font=dict(
            size=21,
            family='Calibri',
            color='black',
        )
    ),
    font=dict(
        family='Calibri',
        size=16,
        color='black'
    ),
).update_traces(
    rotation=180,
    textfont=dict(size=16),
    texttemplate='%{value}<br>(%{percent:.1%})',
    hovertemplate='<b>%{label}</b>: %{value}<extra></extra>'
)

# ------------------------------- Gender Distribution ---------------------------- #

# print("Gender Unique Before:", df['Gender'].unique().tolist())

gender_unique =[
    'Male', 
    'Transgender', 
    'Female', 
    'Group search ', 
    'Prefer Not to Say'
]

df['Gender'] = (
    df['Gender']
        .astype(str)
            .str.strip()
            .replace({
                "Group search": "N/A", 
            })
)

# Calculate gender distribution per month
gender_data = []
for month in months_in_quarter:
    month_data = df[df['Month'] == month]['Gender'].value_counts().reset_index()
    month_data.columns = ['Gender', 'Count']
    month_data['Month'] = month
    gender_data.append(month_data)

# Combine all months
df_gender_quarterly = pd.concat(gender_data, ignore_index=True)

# Get overall gender distribution for pie chart
df_gender = df['Gender'].value_counts().reset_index(name='Count')

# Gender Bar Chart - Quarterly Format
gender_bar = px.bar(
    df_gender_quarterly,
    x='Month',
    y='Count',
    color='Gender',
    barmode='group',
    text='Count',
    category_orders={'Month': months_in_quarter}
).update_layout(
    title_x=0.5,
    xaxis_title='Month',
    yaxis_title='Count',
    title=dict(
        text=f'{current_quarter} Gender Distribution by Month',
        x=0.5, 
        font=dict(
            size=21,
            family='Calibri',
            color='black',
        )
    ),
    font=dict(
        family='Calibri',
        size=16,
        color='black'
    ),
    xaxis=dict(
        title=dict(
            text=None,
            font=dict(size=20),
        ),
        tickmode='array',
        tickvals=months_in_quarter,
        tickangle=0
    ),
    legend=dict(
        title='Gender',
        orientation="v",
        x=1.05,
        xanchor="left",
        y=1,
        yanchor="top"
    ),
).update_traces(
    texttemplate='%{text}',
    textfont=dict(size=16),
    textposition='auto',
    textangle=0,
    hovertemplate='<b>Month</b>: %{x}<br><b>Gender</b>: %{fullData.name}<br><b>Count</b>: %{y}<extra></extra>'
)

# Gender Pie Chart - Overall Distribution
gender_pie = px.pie(
    df_gender,
    names='Gender',
    values='Count'
).update_layout(
    title=dict(
        text=f'{current_quarter} Gender Distribution Ratio',
        x=0.5, 
        font=dict(
            size=21,
            family='Calibri',
            color='black',
        )
    ),
    font=dict(
        family='Calibri',
        size=16,
        color='black'
    ),
).update_traces(
    rotation=180,
    textfont=dict(size=16),
    texttemplate='%{value}<br>(%{percent:.1%})',
    hovertemplate='<b>%{label}</b>: %{value}<extra></extra>'
)

# ------------------------------- Age Distribution ---------------------------- #

# Fill missing values for 'Birthdate' with random dates within a specified range
def random_date(start, end):
    return start + timedelta(days=np.random.randint(0, (end - start).days))

start_date = datetime(1950, 1, 1) # Example: start date, e.g., 1950-01-01
end_date = datetime(2000, 12, 31)

def random_date(start, end):
    return start + timedelta(days=np.random.randint(0, (end - start).days))

# Define the date range for random dates
start_date = datetime(1950, 1, 1)
end_date = datetime(2000, 12, 31)

# Convert 'Individual's Date of Birth:' to datetime, coercing errors to NaT
df['Individual\'s Date of Birth:'] = pd.to_datetime(df['Individual\'s Date of Birth:'], errors='coerce')

# Fill missing values in 'Individual's Date of Birth:' with random dates
df['Individual\'s Date of Birth:'] = df['Individual\'s Date of Birth:'].apply(
    lambda x: random_date(start_date, end_date) if pd.isna(x) else x
)

# Calculate 'Client Age' by subtracting the birth year from the current year
df['Client Age'] = pd.to_datetime('today').year - df['Individual\'s Date of Birth:'].dt.year

# Handle NaT values in 'Client Age' if necessary (e.g., fill with a default value or drop rows)
df['Client Age'] = df['Client Age'].apply(lambda x: "N/A" if x < 0 else x)

# Define a function to categorize ages into age groups
def categorize_age(age):
    if age == "N/A":
        return "N/A"
    elif 10 <= age <= 19:
        return '10-19'
    elif 20 <= age <= 29:
        return '20-29'
    elif 30 <= age <= 39:
        return '30-39'
    elif 40 <= age <= 49:
        return '40-49'
    elif 50 <= age <= 59:
        return '50-59'
    elif 60 <= age <= 69:
        return '60-69'
    elif 70 <= age <= 79:
        return '70-79'
    else:
        return '80+'

# Apply the function to create the 'Age_Group' column
df['Age_Group'] = df['Client Age'].apply(categorize_age)

# Calculate age distribution per month
age_data = []
for month in months_in_quarter:
    month_data = df[df['Month'] == month]['Age_Group'].value_counts().reset_index()
    month_data.columns = ['Age_Group', 'Count']
    month_data['Month'] = month
    age_data.append(month_data)

# Combine all months
df_age_quarterly = pd.concat(age_data, ignore_index=True)

# Get overall age distribution for pie chart
df_age_overall = df['Age_Group'].value_counts().reset_index(name='Count')

# Define age order for consistent display
age_order = ['10-19', '20-29', '30-39', '40-49', '50-59', '60-69', '70-79', '80+', 'N/A']

# Age Bar Chart - Quarterly Format
age_bar = px.bar(
    df_age_quarterly,
    x='Month',
    y='Count',
    color='Age_Group',
    barmode='group',
    text='Count',
    category_orders={'Month': months_in_quarter, 'Age_Group': age_order}
).update_layout(
    title_x=0.5,
    xaxis_title='Month',
    yaxis_title='Count',
    title=dict(
        text=f'{current_quarter} Age Distribution by Month',
        x=0.5, 
        font=dict(
            size=21,
            family='Calibri',
            color='black',
        )
    ),
    font=dict(
        family='Calibri',
        size=16,
        color='black'
    ),
    xaxis=dict(
        title=dict(
            text=None,
            font=dict(size=20),
        ),
        tickmode='array',
        tickvals=months_in_quarter,
        tickangle=0
    ),
    legend=dict(
        title='Age Group',
        orientation="v",
        x=1.05,
        xanchor="left",
        y=1,
        yanchor="top"
    ),
).update_traces(
    texttemplate='%{text}',
    textfont=dict(size=16),
    textposition='auto',
    textangle=0,
    hovertemplate='<b>Month</b>: %{x}<br><b>Age Group</b>: %{fullData.name}<br><b>Count</b>: %{y}<extra></extra>'
)

# Age Pie Chart - Overall Distribution
age_pie = px.pie(
    df_age_overall,
    names='Age_Group',
    values='Count',
    category_orders={'Age_Group': age_order}
).update_layout(
    title=dict(
        text=f'{current_quarter} Age Distribution Ratio',
        x=0.5, 
        font=dict(
            size=21,
            family='Calibri',
            color='black',
        )
    ),
    font=dict(
        family='Calibri',
        size=16,
        color='black'
    )
).update_traces(
    rotation=190,
    textfont=dict(size=16),
    texttemplate='%{value}<br>(%{percent:.1%})',
    hovertemplate='<b>%{label}</b>: %{value}<extra></extra>'
)

# ------------------------------- Insurance Status ------------------------- #

# print("Insurance Unique Before:", df["Insurance"].unique().tolist())

insurance_unique = [
    '',
    'Private Insurance', 
    'MAP',
    'None',
    'Unknown', 
    'MAP 100', 
    '30 Day 100', 
    'NAPHCARE', 
    'MAP Basic', 
    'Medicare', 
    'Just got it!!!', 
    'Medicaid', 
    '30 DAY 100'
]

df["Insurance"] = (
    df["Insurance"]
    .str.strip()
    .replace({
        '': 'Unknown',
        'Just got it!!!': 'Private Insurance',
        '30 DAY 100': '30 Day 100',
        'Medicare': 'Medicaid',
        'NONE': 'None',
        'Map 000': 'MAP 100',
    })
)

# Calculate insurance distribution per month
insurance_data = []
for month in months_in_quarter:
    month_data = df[df['Month'] == month]['Insurance'].value_counts().reset_index()
    month_data.columns = ['Insurance', 'Count']
    month_data['Month'] = month
    insurance_data.append(month_data)

# Combine all months
df_insurance_quarterly = pd.concat(insurance_data, ignore_index=True)

# Get overall insurance distribution for pie chart
df_insurance = df['Insurance'].value_counts().reset_index(name='Count')

# Insurance Status Bar Chart - Quarterly Format
insurance_bar = px.bar(
    df_insurance_quarterly,
    x='Month',
    y='Count',
    color='Insurance',
    barmode='group',
    text='Count',
    category_orders={'Month': months_in_quarter}
).update_layout(
    title_x=0.5,
    xaxis_title='Month',
    yaxis_title='Count',
    title=dict(
        text=f'{current_quarter} Insurance Status by Month',
        x=0.5, 
        font=dict(
            size=21,
            family='Calibri',
            color='black',
        )
    ),
    font=dict(
        family='Calibri',
        size=16,
        color='black'
    ),
    xaxis=dict(
        title=dict(
            text=None,
            font=dict(size=20),
        ),
        tickmode='array',
        tickvals=months_in_quarter,
        tickangle=0
    ),
    legend=dict(
        title='Insurance Status',
        orientation="v",
        x=1.05,
        xanchor="left",
        y=1,
        yanchor="top"
    ),
).update_traces(
    texttemplate='%{text}',
    textfont=dict(size=16),
    textposition='auto',
    textangle=0,
    hovertemplate='<b>Month</b>: %{x}<br><b>Insurance</b>: %{fullData.name}<br><b>Count</b>: %{y}<extra></extra>'
)

# Insurance Status Pie Chart - Overall Distribution
insurance_pie = px.pie(
    df_insurance,
    names='Insurance',
    values='Count'
).update_layout(
    title=dict(
        text=f'{current_quarter} Insurance Status Ratio',
        x=0.5, 
        font=dict(
            size=21,
            family='Calibri',
            color='black',
        )
    ),
    font=dict(
        family='Calibri',
        size=16,
        color='black'
    )
).update_traces(
    rotation=100,
    textfont=dict(size=16),
    texttemplate='%{value}<br>(%{percent:.1%})',
    hovertemplate='<b>%{label}</b>: %{value}<extra></extra>'
)

# ------------------------------ Location Encountered --------------------------------- #

# Unique Values:
# print("Locations Unique Before \n:", df['Location'].unique().tolist())

locations_unique = [
"Black Men's Health Clinic", 'Extended Stay America', 'Bungalows', 'Phone call', 'via zoom', 'Cenikor Austin', 'Terrazas Branch Library', 'Cross Creek Hospital', 'Sunrise Navigation Homeless Center', 'Nice project riverside and Montopolis', 'Phone call and visit to 290/35 area where unhoused', 'social security office and DPS (NORTH LAMAR)', 'DPS Meeting (pflugerville locations)', 'GudLife', 'Community First Village', 'Downtown Austin Community Court', 'Trinity Center'
]

location_categories = [
    "Austin Transitional Center",
    "Black Men's Health Clinic",
    "Bungalows",
    "Community First Village",
    "Cross Creek Hospital",
    "Downtown Austin Community Court",
    "Event",
    "Extended Stay America",
    "GudLife",
    "Housing Authority of Travis County",
    "Integral Care - St. John",
    "Kensington",
    "Phone Call",
    "South Bridge",
    "Sunrise Navigation Homeless Center",
    "Terrazas Public Library"
]

df['Location'] = (
    df['Location']
    .str.strip()
    .replace({
        "" : "No Location",
        
        # Terrazas Public Library
        "Terrazas Branch Library": "Terrazas Public Library",
        "Terrezas public Library" : "Terrazas Public Library",
        "Terreaz Public Library" : "Terrazas Public Library",
        
        # Phone
        "Phone call" : "Phone Call",
        "via zoom": "Phone Call",
        "Phone appt" : "Phone Call",
        "over the phone" : "Phone Call",
        "over phone" : "Phone Call",
        "Phone call and visit to 290/35 area where unhoused": "Phone Call",
        
        # Integral Care
        "phone call/Integral care St John location" : "Integral Care - St. John",
        "integral Care- St. John Location" : "Integral Care - St. John",
        
        # Austin Transitional Center
        "Austin transitional Center" : "Austin Transitional Center",
        "Austin Transistional Center" : "Austin Transitional Center",
        "Austin Transitional center" : "Austin Transitional Center",
        "ATC" : "Austin Transitional Center",
        
        # Extended Stay America
        "EXTENDED STAY AMERICA" : "Extended Stay America",
        
        # Capital Villas (not in category list)
        "capital villas apartments" : "Capital Villas Apartments",
        
        # Social Security Office & DPS (not in allowed categories, could be grouped or ignored)
        'ICare and social security office' : "Social Security Office",
        'Social Security office' : "Social Security Office",
        'social security office and DPS (NORTH LAMAR)': "Social Security Office",
        'DPS Meeting (pflugerville locations)': "Social Security Office",
        
        # South Bridge
        "met client at southbridge to complete check in and discussed what options we had for us to be able to obtain missing vital docs" : "South Bridge",
        
        # Encampment Area
        "picking client up from encampment, vital statics appointment and walk in at social security office, then returning client back to encampment area" : "Encampment Area",

        # Other unclear entries
        "Nice project riverside and Montopolis": "Event",
    })
)

location_unexpected = df[~df['Location'].isin(location_categories)]
# print("Location Unexpected: \n", location_unexpected['Location'].unique().tolist())

# Calculate location distribution per month
location_data = []
for month in months_in_quarter:
    month_data = df[df['Month'] == month]['Location'].value_counts().reset_index()
    month_data.columns = ['Location', 'Count']
    month_data['Month'] = month
    location_data.append(month_data)

# Combine all months
df_location_quarterly = pd.concat(location_data, ignore_index=True)

# Get overall location distribution for pie chart
df_location = df['Location'].value_counts().reset_index(name='Count')

# Location Bar Chart - Quarterly Format
location_bar = px.bar(
    df_location_quarterly,
    x='Month',
    y='Count',
    color='Location',
    barmode='group',
    text='Count',
    category_orders={'Month': months_in_quarter}
).update_layout(
    title_x=0.5,
    xaxis_title='Month',
    yaxis_title='Count',
    title=dict(
        text=f'{current_quarter} Location Encountered by Month',
        x=0.5, 
        font=dict(
            size=21,
            family='Calibri',
            color='black',
        )
    ),
    font=dict(
        family='Calibri',
        size=16,
        color='black'
    ),
    xaxis=dict(
        title=dict(
            text=None,
            font=dict(size=20),
        ),
        tickmode='array',
        tickvals=months_in_quarter,
        tickangle=0
    ),
    legend=dict(
        title='Location',
        orientation="v",
        x=1.05,
        xanchor="left",
        y=1,
        yanchor="top"
    ),
).update_traces(
    texttemplate='%{text}',
    textfont=dict(size=16),
    textposition='auto',
    textangle=0,
    hovertemplate='<b>Month</b>: %{x}<br><b>Location</b>: %{fullData.name}<br><b>Count</b>: %{y}<extra></extra>'
)

# Location Pie Chart - Overall Distribution
location_pie = px.pie(
    df_location,
    names='Location',
    values='Count'
).update_layout(
    title=dict(
        text=f'{current_quarter} Location Encountered Ratio',
        x=0.5, 
        font=dict(
            size=21,
            family='Calibri',
            color='black',
        )
    ),
    font=dict(
        family='Calibri',
        size=16,
        color='black'
    )
).update_traces(
    rotation=90,
    textfont=dict(size=16),
    texttemplate='%{value}<br>(%{percent:.1%})',
    hovertemplate='<b>%{label}</b>: %{value}<extra></extra>'
)

# ------------------------------- Type of Support Given ---------------------------- #

# print("Support Unique Before: \n", df["Support"].unique().tolist())
# print("Support Value counts: \n", df["Support"].value_counts())

support_unique = [
    'Specialty Care Referral', 'Behavioral Health Referral', 'Social Determinant of Health Referral, Re-Entry', 'Social Determinant of Health Referral', 'MAP Application', 'Primary Care Appointment', 'Permanent Support Housing', 'Syayus of map application and scheduling appointment ', 'Permanent Support Housing, Primary Care Appointment, homeless resources', 'Behavioral Health Appointment, Permanent Support Housing, Primary Care Appointment, Social Determinant of Health Referral', 'Primary Care Appointment, Specialty Care Referral', 'Behavioral Health Appointment, Primary Care Appointment, Specialty Care Referral', 'Behavioral Health Referral, MAP Application, Permanent Support Housing, Primary Care Appointment, Primary Care Referral, Specialty Care Referral, Social Determinant of Health Referral, coordinated assessment with Sunrise', 'primary care appointment', 'Behavioral Health Appointment, Behavioral Health Referral, MAP Application, Permanent Support Housing, Primary Care Appointment', 'Behavioral Health Appointment, Behavioral Health Referral, MAP Application, Permanent Support Housing', 'MAP Application, Primary Care Appointment', 'Primary Care Appointment, Food bank', 'Behavioral Health Appointment, MAP Application, Primary Care Appointment, Specialty Care Referral', 'Behavioral Health Appointment', 'Primary Care Referral', 'MAP Application, set an appointment for Financial Screening', 'Outreach search last known place ', 'Permanent Support Housing, I have hard copies of votal docs. Searching for client thru outreach ', 'Permanent Support Housing, Client Search and Outreach ', 'Permanent Support Housing, Searching for clients assigned ', 'Behavioral Health Referral, Permanent Support Housing, Primary Care Referral', 'Specialty Care Referral, Permanent Support Housing', 'MAP Application, '
]

support_categories = [
    "Behavioral Health Appointment",
    "Behavioral Health Referral",
    "MAP Application",
    "Permanent Support Housing",
    "Primary Care Appointment",
    "Primary Care Referral",  # Fixed: Added missing comma
    "Specialty Care Referral",  # Fixed: Added missing comma
    "Social Determinant of Health Referral"
]

# Normalize support_categories (lowercase and stripped for consistency)
normalized_categories = {cat.lower().strip(): cat for cat in support_categories}

# Create monthly support data for quarterly view
support_monthly_data = []

for month in months_in_quarter:
    month_df = df[df['Month'] == month]
    month_counter = Counter()
    
    for entry in month_df['Support']:
        # Split and clean each category
        items = [i.strip().lower() for i in entry.split(",")]
        for item in items:
            if item in normalized_categories:
                month_counter[normalized_categories[item]] += 1
    
    # Convert to DataFrame and add month column
    for support_type, count in month_counter.items():
        support_monthly_data.append({
            'Month': month,
            'Support': support_type,
            'Count': count
        })

# Create DataFrame for quarterly support data
df_support_quarterly = pd.DataFrame(support_monthly_data)

# Overall support data (for pie chart)
counter = Counter()
for entry in df['Support']:
    items = [i.strip().lower() for i in entry.split(",")]
    for item in items:
        if item in normalized_categories:
            counter[normalized_categories[item]] += 1

df_support = pd.DataFrame(counter.items(), columns=['Support', 'Count']).sort_values(by='Count', ascending=False)

# Support Bar Chart - Quarterly Format
support_bar = px.bar(
    df_support_quarterly,
    x='Month',
    y='Count',
    color='Support',
    barmode='group',
    text='Count',
    category_orders={'Month': months_in_quarter}
).update_layout(
    title_x=0.5,
    xaxis_title='Month',
    yaxis_title='Count',
    title=dict(
        text=f'{current_quarter} Support Provided by Month',
        x=0.5, 
        font=dict(
            size=21,
            family='Calibri',
            color='black',
        )
    ),
    font=dict(
        family='Calibri',
        size=16,
        color='black'
    ),
    xaxis=dict(
        title=dict(
            text=None,
            font=dict(size=20),
        ),
        tickmode='array',
        tickvals=months_in_quarter,
        tickangle=0
    ),
    legend=dict(
        title='Support Type',
        orientation="v",
        x=1.05,
        xanchor="left",
        y=1,
        yanchor="top"
    ),
    height=600,
    bargap=0.08,
    bargroupgap=0,
).update_traces(
    texttemplate='%{text}',
    textfont=dict(size=16),
    textposition='auto',
    textangle=0,
    hovertemplate='<b>Month</b>: %{x}<br><b>Support</b>: %{fullData.name}<br><b>Count</b>: %{y}<extra></extra>'
)

# Support Pie Chart - Overall Distribution
support_pie = px.pie(
    df_support,
    names='Support',
    values='Count',
).update_layout(
    title=dict(
        text=f'{current_quarter} Support Distribution Ratio',
        x=0.5, 
        font=dict(
            size=21,
            family='Calibri',
            color='black',
        )
    ),
    font=dict(
        family='Calibri',
        size=16,
        color='black'
    )
).update_traces(
    rotation=20,
    textfont=dict(size=16),
    texttemplate='%{value}<br>(%{percent:.1%})',
    hovertemplate='<b>%{label}</b>: %{value}<extra></extra>'
)

# ------------------------ Individuals' Status (New vs. Returning) --------------------- #

# Calculate status distribution per month
status_data = []
for month in months_in_quarter:
    month_data = df[df['Month'] == month]['Status'].value_counts().reset_index()
    month_data.columns = ['Status', 'Count']
    month_data['Month'] = month
    status_data.append(month_data)

# Combine all months
df_status_quarterly = pd.concat(status_data, ignore_index=True)

# Get overall status distribution for pie chart
df_status = df['Status'].value_counts().reset_index(name='Count')

# Status Bar Chart - Quarterly Format
status_bar = px.bar(
    df_status_quarterly,
    x='Month',
    y='Count',
    color='Status',
    barmode='group',
    text='Count',
    category_orders={'Month': months_in_quarter}
).update_layout(
    title_x=0.5,
    xaxis_title='Month',
    yaxis_title='Count',
    title=dict(
        text=f'{current_quarter} New vs. Returning Clients by Month',
        x=0.5, 
        font=dict(
            size=21,
            family='Calibri',
            color='black',
        )
    ),
    font=dict(
        family='Calibri',
        size=16,
        color='black'
    ),
    xaxis=dict(
        title=dict(
            text=None,
            font=dict(size=20),
        ),
        tickmode='array',
        tickvals=months_in_quarter,
        tickangle=0
    ),
    legend=dict(
        title='Status',
        orientation="v",
        x=1.05,
        xanchor="left",
        y=1,
        yanchor="top"
    ),
    bargap=0.08,
    bargroupgap=0,
).update_traces(
    texttemplate='%{text}',
    textfont=dict(size=16),
    textposition='auto',
    textangle=0,
    hovertemplate='<b>Month</b>: %{x}<br><b>Status</b>: %{fullData.name}<br><b>Count</b>: %{y}<extra></extra>'
)

# Status Pie Chart - Overall Distribution
status_pie = px.pie(
    df_status,
    names="Status",
    values='Count'
).update_layout(
    title=dict(
        text=f'{current_quarter} Ratio of New vs. Returning',
        x=0.5, 
        font=dict(
            size=21,
            family='Calibri',
            color='black',
        )
    ),
    font=dict(
        family='Calibri',
        size=16,
        color='black'
    )
).update_traces(
    rotation=-90,
    textfont=dict(size=16),
    texttemplate='%{value}<br>(%{percent:.1%})',
    hovertemplate='<b>%{label} Status</b>: %{value}<extra></extra>',
)

# ----------------------- Person Filling Out This Form ------------------------ #

# print("Person Unique Before: \n", df["Person"].unique().tolist())

person_unique = [
    'Dominique Street',
    'Dr Larry Wallace Jr',
    'Eric Roberts',
    'Eric roberts',
    'EricRoberts',
    'Jaqueline Oviedo',
    'Kimberly Holiday',
    'Larry Wallace Jr',
    'Michael Lambert',
    'Michael Lambert ',
    'Rishit Yokananth',
    'Sonya Hosey',
    'Toya Craney',
    'Tramisha Pete',
    'Viviana Varela',
]

df['Person'] = (
    df['Person']
    .str.strip()
    .replace({
        'Dominique': 'Dominique Street',
        'Jaqueline Ovieod': 'Jaqueline Oviedo',
        'Eric roberts': 'Eric Roberts',
        'EricRoberts': 'Eric Roberts',
        'Dr Larry Wallace Jr': 'Larry Wallace Jr',
        'Sonya': 'Sonya Hosey',
        })
    )

# Calculate person distribution per month
person_data = []
for month in months_in_quarter:
    month_data = df[df['Month'] == month]['Person'].value_counts().reset_index()
    month_data.columns = ['Person', 'Count']
    month_data['Month'] = month
    person_data.append(month_data)

# Combine all months
df_person_quarterly = pd.concat(person_data, ignore_index=True)

# Get overall person distribution for pie chart
df_person = df['Person'].value_counts().reset_index(name='Count')

# Person Bar Chart - Quarterly Format
person_bar = px.bar(
    df_person_quarterly,
    x='Month',
    y='Count',
    color='Person',
    barmode='group',
    text='Count',
    category_orders={'Month': months_in_quarter}
).update_layout(
    title_x=0.5,
    xaxis_title='Month',
    yaxis_title='Count',
    title=dict(
        text=f'{current_quarter} Forms Submitted by Month',
        x=0.5, 
        font=dict(
            size=21,
            family='Calibri',
            color='black',
        )
    ),
    font=dict(
        family='Calibri',
        size=16,
        color='black'
    ),
    xaxis=dict(
        title=dict(
            text=None,
            font=dict(size=20),
        ),
        tickmode='array',
        tickvals=months_in_quarter,
        tickangle=0
    ),
    legend=dict(
        title='Person',
        orientation="v",
        x=1.05,
        xanchor="left",
        y=1,
        yanchor="top"
    ),
    bargap=0.08,
    bargroupgap=0,
).update_traces(
    texttemplate='%{text}',
    textfont=dict(size=16),
    textposition='auto',
    textangle=0,
    hovertemplate='<b>Month</b>: %{x}<br><b>Person</b>: %{fullData.name}<br><b>Count</b>: %{y}<extra></extra>'
)

# Person Pie Chart - Overall Distribution
person_pie = px.pie(
    df_person,
    names="Person",
    values='Count'
).update_layout(
    title=dict(
        text=f'{current_quarter} Forms Submitted Ratio',
        x=0.5, 
        font=dict(
            size=21,
            family='Calibri',
            color='black',
        )
    ),
    font=dict(
        family='Calibri',
        size=16,
        color='black'
    )
).update_traces(
    rotation=140,
    textfont=dict(size=16),
    texttemplate='%{value}<br>(%{percent:.1%})',
    hovertemplate='<b>%{label}</b>: %{value}<extra></extra>',
)

# ---------------------- Zip 2 --------------------- #

# df['ZIP2'] = df['ZIP Code:']
# print('ZIP2 Unique Before: \n', df['ZIP2'].unique().tolist())

# zip2_unique =[
# 78753, '', 78721, 78664, 78725, 78758, 78724, 78660, 78723, 78748, 78744, 78752, 78745, 78617, 78754, 78653, 78727, 78747, 78659, 78759, 78741, 78616, 78644, 78757, 'UnKnown', 'Unknown', 'uknown', 'Unknown ', 78729
# ]

# zip2_mode = df['ZIP2'].mode()[0]

# df['ZIP2'] = (
#     df['ZIP2']
#     .astype(str)
#     .str.strip()
#     .replace({
#         'Texas': zip2_mode,
#         'Unhoused': zip2_mode,
#         'UNHOUSED': zip2_mode,
#         'UnKnown': zip2_mode,
#         'Unknown': zip2_mode,
#         'uknown': zip2_mode,
#         'Unknown': zip2_mode,
#         'NA': zip2_mode,
#         'nan': zip2_mode,
#         '': zip2_mode,
#         ' ': zip2_mode,
#     })
# )

# df['ZIP2'] = df['ZIP2'].fillna(zip2_mode)
# df_z = df['ZIP2'].value_counts().reset_index(name='Count')

# print('ZIP2 Unique After: \n', df_z['ZIP2'].unique().tolist())
# print('ZIP2 Value Counts After: \n', df_z['ZIP2'].value_counts())

df['ZIP2'] = df['ZIP Code:'].astype(str).str.strip()

valid_zip_mask = df['ZIP2'].str.isnumeric()
zip2_mode = df.loc[valid_zip_mask, 'ZIP2'].mode()[0]  # still a string

invalid_zip_values = [
    'Texas', 'Unhoused', 'UNHOUSED', 'UnKnown', 'Unknown', 'uknown',
    'Unknown ', 'NA', 'nan', 'NaN', 'None', '', ' '
]
df['ZIP2'] = df['ZIP2'].replace(invalid_zip_values, zip2_mode)

# Step 3: Coerce to numeric, fill any remaining NaNs, then convert back to string
df['ZIP2'] = pd.to_numeric(df['ZIP2'], errors='coerce')
df['ZIP2'] = df['ZIP2'].fillna(int(zip2_mode)).astype(int).astype(str)

# Step 4: Create value count dataframe for the bar chart
df_z = df['ZIP2'].value_counts().reset_index(name='Count')
df_z.columns = ['ZIP2', 'Count']  # Rename columns for Plotly

df_z['Percentage'] = (df_z['Count'] / df_z['Count'].sum()) * 100
df_z['text_label'] = df_z['Count'].astype(str) + ' (' + df_z['Percentage'].round(1).astype(str) + '%)'
# df_z['text_label'] = df_z['Percentage'].round(1).astype(str) + '%'


zip_fig =px.bar(
    df_z,
    x='Count',
    y='ZIP2',
    color='ZIP2',
    text='text_label',
    # text='Count',
    orientation='h'  # Horizontal bar chart
).update_layout(
    title='Number of Clients by Zip Code',
    xaxis_title='Residents',
    yaxis_title='Zip Code',
    title_x=0.5,
    # height=950,
    # width=1500,
    font=dict(
        family='Calibri',
        size=17,
        color='black'
    ),
        yaxis=dict(
        tickangle=0  # Keep y-axis labels horizontal for readability
    ),
        legend=dict(
        title='ZIP Code',
        orientation="v",  # Vertical legend
        x=1.05,  # Position legend to the right
        xanchor="left",  # Anchor legend to the left
        y=1,  # Position legend at the top
        yanchor="top"  # Anchor legend at the top
    ),
).update_traces(
    textposition='auto',  # Place text labels inside the bars
    textfont=dict(size=30),  # Increase text size in each bar
    # insidetextanchor='middle',  # Center text within the bars
    textangle=0,            # Ensure text labels are horizontal
    hovertemplate='<b>ZIP Code</b>: %{y}<br><b>Count</b>: %{x}<extra></extra>'
)

zip_pie = px.pie(
    df_z,
    names='ZIP2',
    values='Count',
    color_discrete_sequence=px.colors.qualitative.Safe
).update_layout(
    title=dict(
        text='Ratio of ZIP Code Distribution',
        x=0.5, 
        font=dict(
            size=21,
            family='Calibri',
            color='black',
        )
    ),
    font=dict(
        family='Calibri',
        size=16,
        color='black'
    ),
    legend_title='ZIP Code'
).update_traces(
    rotation=90,
    texttemplate='%{value}<br>(%{percent:.1%})',
    textfont_size=16,
    hovertemplate='<b>ZIP Code</b>: %{label}<br><b>Count</b>: %{value}<br><b>Percent</b>: %{percent}<extra></extra>'
)

# -----------------------------------------------------------------------------

# Get the distinct values in column

# distinct_service = df['What service did/did not complete?'].unique()
# print('Distinct:\n', distinct_service)

# =============================== Folium ========================== #

# empty_strings = df[df['ZIP Code:'].str.strip() == ""]
# # print("Empty strings: \n", empty_strings.iloc[:, 10:12])

# # Filter df to exclued all rows where there is no value for "ZIP Code:"
# df = df[df['ZIP Code:'].str.strip() != ""]

# mode_value = df['ZIP Code:'].mode()[0]
# df['ZIP Code:'] = df['ZIP Code:'].fillna(mode_value)

# # print("ZIP value counts:", df['ZIP Code:'].value_counts())
# # print("Zip Unique Before: \n", df['ZIP Code:'].unique().tolist())

# # Check for non-numeric values in the 'ZIP Code:' column
# # print("ZIP non-numeric values:", df[~df['ZIP Code:'].str.isnumeric()]['ZIP Code:'].unique())

# df['ZIP Code:'] = df['ZIP Code:'].astype(str).str.strip()

# df['ZIP Code:'] = (
#     df['ZIP Code:']
#     .astype(str).str.strip()
#         .replace({
#             'Texas': mode_value,
#             'Unhoused': mode_value,
#             'unknown': mode_value,
#             'Unknown': mode_value,
#             'UnKnown': mode_value,
#             'uknown': mode_value,
#             'NA': mode_value,
#             "": mode_value,
#             'nan': mode_value
# }))

# df['ZIP Code:'] = df['ZIP Code:'].where(df['ZIP Code:'].str.isdigit(), mode_value)
# df['ZIP Code:'] = df['ZIP Code:'].astype(int)

# df_zip = df['ZIP Code:'].value_counts().reset_index(name='Residents')
# # df_zip['ZIP Code:'] = df_zip['index'].astype(int)
# df_zip['Residents'] = df_zip['Residents'].astype(int)
# # df_zip.drop('index', axis=1, inplace=True)

# # print("Zip Unique After: \n", df['ZIP Code:'].unique().tolist())

# # print(df_zip.head())

# # Create a folium map
# m = folium.Map([30.2672, -97.7431], zoom_start=10)

# # Add different tile sets
# folium.TileLayer('OpenStreetMap', attr='© OpenStreetMap contributors').add_to(m)
# folium.TileLayer('Stamen Terrain', attr='Map tiles by Stamen Design, under CC BY 3.0. Data by OpenStreetMap, under ODbL.').add_to(m)
# folium.TileLayer('Stamen Toner', attr='Map tiles by Stamen Design, under CC BY 3.0. Data by OpenStreetMap, under ODbL.').add_to(m)
# folium.TileLayer('Stamen Watercolor', attr='Map tiles by Stamen Design, under CC BY 3.0. Data by OpenStreetMap, under ODbL.').add_to(m)
# folium.TileLayer('CartoDB positron', attr='Map tiles by CartoDB, under CC BY 3.0. Data by OpenStreetMap, under ODbL.').add_to(m)
# folium.TileLayer('CartoDB dark_matter', attr='Map tiles by CartoDB, under CC BY 3.0. Data by OpenStreetMap, under ODbL.').add_to(m)

# # Available map styles
# map_styles = {
#     'OpenStreetMap': {
#         'tiles': 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
#         'attribution': '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
#     },
#     'Stamen Terrain': {
#         'tiles': 'https://stamen-tiles.a.ssl.fastly.net/terrain/{z}/{x}/{y}.jpg',
#         'attribution': 'Map tiles by <a href="http://stamen.com">Stamen Design</a>, under <a href="http://creativecommons.org/licenses/by/3.0">CC BY 3.0</a>. Data by <a href="http://openstreetmap.org">OpenStreetMap</a>, under ODbL.'
#     },
#     'Stamen Toner': {
#         'tiles': 'https://stamen-tiles.a.ssl.fastly.net/toner/{z}/{x}/{y}.png',
#         'attribution': 'Map tiles by <a href="http://stamen.com">Stamen Design</a>, under <a href="http://creativecommons.org/licenses/by/3.0">CC BY 3.0</a>. Data by <a href="http://openstreetmap.org">OpenStreetMap</a>, under ODbL.'
#     },
#     'Stamen Watercolor': {
#         'tiles': 'https://stamen-tiles.a.ssl.fastly.net/watercolor/{z}/{x}/{y}.jpg',
#         'attribution': 'Map tiles by <a href="http://stamen.com">Stamen Design</a>, under <a href="http://creativecommons.org/licenses/by/3.0">CC BY 3.0</a>. Data by <a href="http://openstreetmap.org">OpenStreetMap</a>, under ODbL.'
#     },
#     'CartoDB positron': {
#         'tiles': 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png',
#         'attribution': '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
#     },
#     'CartoDB dark_matter': {
#         'tiles': 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png',
#         'attribution': '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
#     },
#     'ESRI Imagery': {
#         'tiles': 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
#         'attribution': 'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community'
#     }
# }

# # Add tile layers to the map
# for style, info in map_styles.items():
#     folium.TileLayer(tiles=info['tiles'], attr=info['attribution'], name=style).add_to(m)

# # Select a style
# # selected_style = 'OpenStreetMap'
# # selected_style = 'Stamen Terrain'
# # selected_style = 'Stamen Toner'
# # selected_style = 'Stamen Watercolor'
# selected_style = 'CartoDB positron'
# # selected_style = 'CartoDB dark_matter'
# # selected_style = 'ESRI Imagery'

# # Apply the selected style
# if selected_style in map_styles:
#     style_info = map_styles[selected_style]
#     # print(f"Selected style: {selected_style}")
#     folium.TileLayer(
#         tiles=style_info['tiles'],
#         attr=style_info['attribution'],
#         name=selected_style
#     ).add_to(m)
# else:
#     print(f"Selected style '{selected_style}' is not in the map styles dictionary.")
#      # Fallback to a default style
#     folium.TileLayer('OpenStreetMap').add_to(m)
    
# geolocator = Nominatim(user_agent="your_app_name", timeout=10)

# # Function to get coordinates from zip code
# # def get_coordinates(zip_code):
# #     geolocator = Nominatim(user_agent="response_q4_2024.py", timeout=10) # Add a timeout parameter to prevent long waits
# #     location = geolocator.geocode({"postalcode": zip_code, "country": "USA"})
# #     if location:
# #         return location.latitude, location.longitude
# #     else:
# #         print(f"Could not find coordinates for zip code: {zip_code}")
# #         return None, None
    
# def get_coordinates(zip_code):
#     for _ in range(3):  # Retry up to 3 times
#         try:
#             location = geolocator.geocode({"postalcode": zip_code, "country": "USA"})
#             if location:
#                 return location.latitude, location.longitude
#         except GeocoderTimedOut:
#             time.sleep(2)  # Wait before retrying
#     return None, None  # Return None if all retries fail

# # Apply function to dataframe to get coordinates
# df_zip['Latitude'], df_zip['Longitude'] = zip(*df_zip['ZIP Code:'].apply(get_coordinates))

# # Filter out rows with NaN coordinates
# df_zip = df_zip.dropna(subset=['Latitude', 'Longitude'])
# # print(df_zip.head())
# # print(df_zip[['Zip Code', 'Latitude', 'Longitude']].head())
# # print(df_zip.isnull().sum())

# # instantiate a feature group for the incidents in the dataframe
# incidents = folium.map.FeatureGroup()

# for index, row in df_zip.iterrows():
#     lat, lng = row['Latitude'], row['Longitude']

#     if pd.notna(lat) and pd.notna(lng):  
#         incidents.add_child(# Check if both latitude and longitude are not NaN
#         folium.vector_layers.CircleMarker(
#             location=[lat, lng],
#             radius=row['Residents'] * 1.2,  # Adjust the multiplication factor to scale the circle size as needed,
#             color='blue',
#             fill=True,
#             fill_color='blue',
#             fill_opacity=0.4
#         ))

# # add pop-up text to each marker on the map
# latitudes = list(df_zip['Latitude'])
# longitudes = list(df_zip['Longitude'])

# # labels = list(df_zip[['Zip Code', 'Residents_In_Zip_Code']])
# labels = df_zip.apply(lambda row: f"ZIP Code: {row['ZIP Code:']}, Patients: {row['Residents']}", axis=1)

# for lat, lng, label in zip(latitudes, longitudes, labels):
#     if pd.notna(lat) and pd.notna(lng):
#         folium.Marker([lat, lng], popup=label).add_to(m)
 
# formatter = "function(num) {return L.Util.formatNum(num, 5);};"
# mouse_position = MousePosition(
#     position='topright',
#     separator=' Long: ',
#     empty_string='NaN',
#     lng_first=False,
#     num_digits=20,
#     prefix='Lat:',
#     lat_formatter=formatter,
#     lng_formatter=formatter,
# )

# m.add_child(mouse_position)

# # add incidents to map
# m.add_child(incidents)

# map_path = 'zip_code_map.html'
# map_file = os.path.join(script_dir, map_path)
# m.save(map_file)
# map_html = open(map_file, 'r').read()

# # # ========================== DataFrame Table ========================== #

df = df.sort_values('Date of Activity', ascending=True)

# create a display index column and prepare table data/columns
# reset index to ensure contiguous numbering after any filtering/sorting upstream
df_indexed = df.reset_index(drop=True).copy()
# Insert '#' as the first column (1-based row numbers)
df_indexed.insert(0, '#', df_indexed.index + 1)

# Convert to records for DataTable
data = df_indexed.to_dict('records')
columns = [{"name": col, "id": col} for col in df_indexed.columns]

# ============================== Dash Application ========================== #

app = dash.Dash(__name__)
server= app.server

app.layout = html.Div(
    children=[ 
        html.Div(
            className='divv', 
            children=[ 
                html.H1(
                    'Client Navigation Report', 
                    className='title'),
                html.H1(
                    f'Q4 {report_year}', 
                    className='title2'),
                html.Div(
                    className='btn-box', 
                    children=[
                        html.A(
                            'Repo',
                            href=f'https://github.com/CxLos/Navigation_{current_quarter}_{report_year}',
                            className='btn'
                        ),
                    ]
                ),
            ]
        ),  

# ============================ Rollups ========================== #

# ROW 1
html.Div(
    className='rollup-row',
    children=[
        
        html.Div(
            className='rollup-box-tl',
            children=[
                html.Div(
                    className='title-box',
                    children=[
                        html.H3(
                            className='rollup-title',
                            children=[f'{current_quarter} Clients Served']
                        ),
                    ]
                ),

                html.Div(
                    className='circle-box',
                    children=[
                        html.Div(
                            className='circle-1',
                            children=[
                                html.H1(
                                className='rollup-number',
                                children=[clients_served]
                                ),
                            ]
                        )
                    ],
                ),
            ]
        ),
        html.Div(
            className='rollup-box-tr',
            children=[
                html.Div(
                    className='title-box',
                    children=[
                        html.H3(
                            className='rollup-title',
                            children=[f'{current_quarter} Navigation Hours']
                        ),
                    ]
                ),
                html.Div(
                    className='circle-box',
                    children=[
                        html.Div(
                            className='circle-2',
                            children=[
                                html.H1(
                                className='rollup-number',
                                children=[df_duration]
                                ),
                            ]
                        )
                    ],
                ),
            ]
        ),
    ]
),

html.Div(
    className='rollup-row',
    children=[
        html.Div(
            className='rollup-box-bl',
            children=[
                html.Div(
                    className='title-box',
                    children=[
                        html.H3(
                            className='rollup-title',
                            children=[f'{current_quarter} Travel Hours']
                        ),
                    ]
                ),

                html.Div(
                    className='circle-box',
                    children=[
                        html.Div(
                            className='circle-3',
                            children=[
                                html.H1(
                                className='rollup-number',
                                children=[travel_time]
                                ),
                            ]
                        )
                    ],
                ),
            ]
        ),
        html.Div(
            className='rollup-box-br',
            children=[
                html.Div(
                    className='title-box',
                    children=[
                        html.H3(
                            className='rollup-title',
                            children=['Placeholder']
                        ),
                    ]
                ),
                html.Div(
                    className='circle-box',
                    children=[
                        html.Div(
                            className='circle-4',
                            children=[
                                html.H1(
                                className='rollup-number',
                                children=['-']
                                ),
                            ]
                        )
                    ],
                ),
            ]
        ),
    ]
),

# ============================ Visuals ========================== #

html.Div(
    className='graph-container',
    children=[
        
        html.H1(
            className='visuals-text',
            children='Visuals'
        ),
        
        html.Div(
            className='graph-row',
            children=[
                html.Div(
                    className='graph-box',
                    children=[
                        dcc.Graph(
                            className='graph',
                            figure=client_bar
                        )
                    ]
                ),
                html.Div(
                    className='graph-box',
                    children=[
                        dcc.Graph(
                            className='graph',
                            figure=client_pie
                        )
                    ]
                ),
            ]
        ),
        
        html.Div(
            className='graph-row',
            children=[
                html.Div(
                    className='graph-box',
                    children=[
                        dcc.Graph(
                            className='graph',
                            figure=travel_bar
                        )
                    ]
                ),
                html.Div(
                    className='graph-box',
                    children=[
                        dcc.Graph(
                            className='graph',
                            figure=travel_pie
                        )
                    ]
                ),
            ]
        ),
        
        html.Div(
            className='graph-row',
            children=[
                html.Div(
                    className='graph-box',
                    children=[
                        dcc.Graph(
                            className='graph',
                            figure=race_bar
                        )
                    ]
                ),
                html.Div(
                    className='graph-box',
                    children=[
                        dcc.Graph(
                            className='graph',
                            figure=race_pie
                        )
                    ]
                ),
            ]
        ),
        
        html.Div(
            className='graph-row',
            children=[
                html.Div(
                    className='graph-box',
                    children=[
                        dcc.Graph(
                            className='graph',
                            figure=gender_bar
                        )
                    ]
                ),
                html.Div(
                    className='graph-box',
                    children=[
                        dcc.Graph(
                            className='graph',
                            figure=gender_pie
                        )
                    ]
                ),
            ]
        ),
        
        html.Div(
            className='graph-row',
            children=[
                html.Div(
                    className='wide-box',
                    children=[
                        dcc.Graph(
                            className='wide-graph',
                            figure=age_bar
                        )
                    ]
                ),
            ]
        ),
        
        html.Div(
            className='graph-row',
            children=[
                html.Div(
                    className='wide-box',
                    children=[
                        dcc.Graph(
                            className='wide-graph',
                            figure=age_pie
                        )
                    ]
                ),
            ]
        ),
        
        html.Div(
            className='graph-row',
            children=[
                html.Div(
                    className='wide-box',
                    children=[
                        dcc.Graph(
                            className='wide-graph',
                            figure=support_bar
                        )
                    ]
                ),
            ]
        ),
        
        html.Div(
            className='graph-row',
            children=[
                html.Div(
                    className='wide-box',
                    children=[
                        dcc.Graph(
                            className='wide-graph',
                            figure=support_pie
                        )
                    ]
                ),
            ]
        ),
        
        html.Div(
            className='graph-row',
            children=[
                html.Div(
                    className='wide-box',
                    children=[
                        dcc.Graph(
                            className='wide-graph',
                            figure=insurance_bar
                        )
                    ]
                ),
            ]
        ),
        
        html.Div(
            className='graph-row',
            children=[
                html.Div(
                    className='wide-box',
                    children=[
                        dcc.Graph(
                            className='wide-graph',
                            figure=insurance_pie
                        )
                    ]
                ),
            ]
        ),
        
        html.Div(
            className='graph-row',
            children=[
                html.Div(
                    className='wide-box',
                    children=[
                        dcc.Graph(
                            className='wide-graph',
                            figure=location_bar
                        )
                    ]
                ),
            ]
        ),
        
        html.Div(
            className='graph-row',
            children=[
                html.Div(
                    className='wide-box',
                    children=[
                        dcc.Graph(
                            className='wide-graph',
                            figure=location_pie
                        )
                    ]
                ),
            ]
        ),
        
        html.Div(
            className='graph-row',
            children=[
                html.Div(
                    className='wide-box',
                    children=[
                        dcc.Graph(
                            className='wide-graph',
                            figure=person_bar
                        )
                    ]
                ),
            ]
        ),
        
        html.Div(
            className='graph-row',
            children=[
                html.Div(
                    className='wide-box',
                    children=[
                        dcc.Graph(
                            className='wide-graph',
                            figure=person_pie
                        )
                    ]
                ),
            ]
        ),
        
        html.Div(
            className='graph-row',
            children=[
                html.Div(
                    className='graph-box',
                    children=[
                        dcc.Graph(
                            className='graph',
                            figure=status_bar
                        )
                    ]
                ),
                html.Div(
                    className='graph-box',
                    children=[
                        dcc.Graph(
                            className='graph',
                            figure=status_pie
                        )
                    ]
                ),
            ]
        ),
        
        html.Div(
            className='graph-row',
            children=[
                html.Div(
                    className='wide-box',
                    children=[
                        dcc.Graph(
                            className='zip-graph',
                            figure=zip_fig
                        )
                    ]
                ),
            ]
        ),
        
        html.Div(
            className='graph-row',
            children=[
                html.Div(
                    className='wide-box',
                    children=[
                        dcc.Graph(
                            className='zip-graph',
                            figure=zip_pie
                        )
                    ]
                ),
            ]
        ),
        html.Div(
            className='folium-row',
            children=[
                html.Div(
                    className='folium-box',
                    children=[
                        html.H1(
                            'Visitors by Zip Code Map', 
                            className='zip'
                        ),
                        html.Iframe(
                            className='folium',
                            id='folium-map',
                            # srcDoc=map_html
                        )
                    ]
                ),
            ]
        ),
    ]
),

# ============================ Data Table ========================== #

    html.Div(
        className='data-box',
        children=[
            html.H1(
                className='data-title',
                children='Navigation Table'
            ),
            dash_table.DataTable(
                id='applications-table',
                data=data,
                columns=columns,
                page_size=10,
                sort_action='native',
                filter_action='native',
                row_selectable='multi',
                style_table={
                    'overflowX': 'auto',
                    # 'border': '3px solid #000',
                    # 'borderRadius': '0px'
                },
                style_cell={
                    'textAlign': 'left',
                    'minWidth': '100px', 
                    'whiteSpace': 'normal'
                },
                style_header={
                    'textAlign': 'center', 
                    'fontWeight': 'bold',
                    'backgroundColor': '#34A853', 
                    'color': 'white'
                },
                style_data={
                    'whiteSpace': 'normal',
                    'height': 'auto',
                },
                style_cell_conditional=[
                    # make the index column narrow and centered
                    {'if': {'column_id': '#'},
                    'width': '20px', 'minWidth': '60px', 'maxWidth': '60px', 'textAlign': 'center'},
                    {'if': {'column_id': 'Timestamp'},
                    'width': '50px', 'minWidth': '100px', 'maxWidth': '200px', 'textAlign': 'center'},
                    {'if': {'column_id': 'Date of Activity'},
                    'width': '160px', 'minWidth': '160px', 'maxWidth': '160px', 'textAlign': 'center'},
                    {'if': {'column_id': 'Description'},
                    'width': '200px', 'minWidth': '400px', 'maxWidth': '200px', 'textAlign': 'center'},
                ]
            ),
        ]
    ),
])

print(f"Serving Flask app '{current_file}'! 🚀")

if __name__ == '__main__':
    app.run(debug=
                   True)
                #    False)
                
# ----------------------------------------------- Updated Database --------------------------------------

# updated_path = f'data/Navigation_{current_month}_{report_year}.xlsx'
# data_path = os.path.join(script_dir, updated_path)
# sheet_name=f'{current_month} {report_year}'

# with pd.ExcelWriter(data_path, engine='xlsxwriter') as writer:
#     df.to_excel(
#             writer, 
#             sheet_name=sheet_name, 
#             startrow=1, 
#             index=False
#         )

#     # Access the workbook and each worksheet
#     workbook = writer.book
#     sheet1 = writer.sheets[sheet_name]
    
#     # Define the header format
#     header_format = workbook.add_format({
#         'bold': True, 
#         'font_size': 16, 
#         'align': 'center', 
#         'valign': 'vcenter',
#         'border': 1, 
#         'font_color': 'black', 
#         'bg_color': '#B7B7B7',
#     })
    
#     # Set column A (Name) to be left-aligned, and B-E to be right-aligned
#     left_align_format = workbook.add_format({
#         'align': 'left',  # Left-align for column A
#         'valign': 'vcenter',  # Vertically center
#         'border': 0  # No border for individual cells
#     })

#     right_align_format = workbook.add_format({
#         'align': 'right',  # Right-align for columns B-E
#         'valign': 'vcenter',  # Vertically center
#         'border': 0  # No border for individual cells
#     })
    
#     # Create border around the entire table
#     border_format = workbook.add_format({
#         'border': 1,  # Add border to all sides
#         'border_color': 'black',  # Set border color to black
#         'align': 'center',  # Center-align text
#         'valign': 'vcenter',  # Vertically center text
#         'font_size': 12,  # Set font size
#         'font_color': 'black',  # Set font color to black
#         'bg_color': '#FFFFFF'  # Set background color to white
#     })

#     # Merge and format the first row (A1:E1) for each sheet
#     sheet1.merge_range('A1:AB1', f'Client Navigation Report {current_month} {report_year}', header_format)

#     # Set column alignment and width
#     # sheet1.set_column('A:A', 20, left_align_format)  

#     print(f"Navigation Excel file saved to {data_path}")

# -------------------------------------------- KILL PORT ---------------------------------------------------

# netstat -ano | findstr :8050
# taskkill /PID 24772 /F
# npx kill-port 8050


# ---------------------------------------------- Host Application -------------------------------------------

# 1. pip freeze > requirements.txt
# 2. add this to procfile: 'web: gunicorn impact_11_2024:server'
# 3. heroku login
# 4. heroku create
# 5. git push heroku main

# Create venv 
# virtualenv venv 
# source venv/bin/activate # uses the virtualenv

# Update PIP Setup Tools:
# pip install --upgrade pip setuptools

# Install all dependencies in the requirements file:
# pip install -r requirements.txt

# Check dependency tree:
# pipdeptree
# pip show package-name

# Remove
# pypiwin32
# pywin32
# jupytercore

# ----------------------------------------------------

# Name must start with a letter, end with a letter or digit and can only contain lowercase letters, digits, and dashes.

# Heroku Setup:
# heroku login
# heroku create nav-jul-2025
# heroku git:remote -a nav-jul-2025
# git remote set-url heroku git@heroku.com:nav-jan-2025.git
# git push heroku main

# Clear Heroku Cache:
# heroku plugins:install heroku-repo
# heroku repo:purge_cache -a nav-nov-2024

# Set buildpack for heroku
# heroku buildpacks:set heroku/python

# Heatmap Colorscale colors -----------------------------------------------------------------------------

#   ['aggrnyl', 'agsunset', 'algae', 'amp', 'armyrose', 'balance',
            #  'blackbody', 'bluered', 'blues', 'blugrn', 'bluyl', 'brbg',
            #  'brwnyl', 'bugn', 'bupu', 'burg', 'burgyl', 'cividis', 'curl',
            #  'darkmint', 'deep', 'delta', 'dense', 'earth', 'edge', 'electric',
            #  'emrld', 'fall', 'geyser', 'gnbu', 'gray', 'greens', 'greys',
            #  'haline', 'hot', 'hsv', 'ice', 'icefire', 'inferno', 'jet',
            #  'magenta', 'magma', 'matter', 'mint', 'mrybm', 'mygbm', 'oranges',
            #  'orrd', 'oryel', 'oxy', 'peach', 'phase', 'picnic', 'pinkyl',
            #  'piyg', 'plasma', 'plotly3', 'portland', 'prgn', 'pubu', 'pubugn',
            #  'puor', 'purd', 'purp', 'purples', 'purpor', 'rainbow', 'rdbu',
            #  'rdgy', 'rdpu', 'rdylbu', 'rdylgn', 'redor', 'reds', 'solar',
            #  'spectral', 'speed', 'sunset', 'sunsetdark', 'teal', 'tealgrn',
            #  'tealrose', 'tempo', 'temps', 'thermal', 'tropic', 'turbid',
            #  'turbo', 'twilight', 'viridis', 'ylgn', 'ylgnbu', 'ylorbr',
            #  'ylorrd'].

# rm -rf ~$bmhc_data_2024_cleaned.xlsx
# rm -rf ~$bmhc_data_2024.xlsx
# rm -rf ~$bmhc_q4_2024_cleaned2.xlsx