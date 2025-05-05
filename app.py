import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image
import db_handler

# Set page configuration
st.set_page_config(
    page_title="Weather Data Explorer",
    page_icon="🌤️",
    layout="wide"
)

# App title and description
st.title("Weather Data Explorer")
st.markdown("Get current and historical weather data for any location")

# Initialize the database
if st.sidebar.button("Initialize Database"):
    if db_handler.initialize_database():
        st.sidebar.success("Database initialized successfully!")
    else:
        st.sidebar.error("Failed to initialize database")

# Sidebar for inputs
with st.sidebar:
    st.header("Location Settings")
    location = st.text_input("Enter Location", "London")
    
    st.header("Date Settings")
    current_date = datetime.now().date()
    selected_date1 = st.date_input("Select Date", current_date)
    selected_hour1 = st.slider("Select Hour (24-hour format)", 0, 23, datetime.now().hour)
    
    # Combine date and hour
    selected_datetime1 = datetime.combine(selected_date1, datetime.min.time()) + timedelta(hours=selected_hour1)
    
    # Option to compare with another date
    compare_dates = st.checkbox("Compare with another date")
    
    if compare_dates:
        selected_date2 = st.date_input("Select Second Date", current_date - timedelta(days=1))
        selected_hour2 = st.slider("Select Second Hour (24-hour format)", 0, 23, datetime.now().hour)
        selected_datetime2 = datetime.combine(selected_date2, datetime.min.time()) + timedelta(hours=selected_hour2)
    
    # Option to view saved data
    view_saved_data = st.checkbox("View Saved Weather Data")

# API key and base URL
api_key = "38088080bc24403b8cd182109251404"
base_url = "http://api.weatherapi.com/v1"

# Function to get weather data
def get_weather_data(location, datetime_obj):
    # Check if the date is current or historical
    if datetime_obj.date() == current_date and datetime_obj.hour >= datetime.now().hour - 1:
        # Current weather
        endpoint = f"{base_url}/current.json"
        params = {
            "key": api_key,
            "q": location,
        }
    else:
        # Historical weather
        date_str = datetime_obj.strftime("%Y-%m-%d")
        endpoint = f"{base_url}/history.json"
        params = {
            "key": api_key,
            "q": location,
            "dt": date_str,
        }
    
    try:
        response = requests.get(endpoint, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching weather data: {e}")
        return None

# Function to display weather data
def display_weather_data(weather_data, datetime_obj, column):
    with column:
        if 'location' in weather_data:
            location_info = weather_data['location']
            st.subheader(f"Weather in {location_info['name']}, {location_info['country']}")
            st.write(f"Date & Time: {datetime_obj.strftime('%Y-%m-%d %H:00')}")
            
            # Extract current data
            if 'current' in weather_data:
                current_data = weather_data['current']
            else:
                # Find the hour closest to the selected time
                historical_hour = min(
                    weather_data['forecast']['forecastday'][0]['hour'],
                    key=lambda x: abs(datetime.strptime(x['time'], '%Y-%m-%d %H:%M').time().hour - 
                                   datetime_obj.time().hour)
                )
                current_data = historical_hour
            
            # Display weather condition with icon
            condition = current_data['condition']['text']
            icon_url = f"https:{current_data['condition']['icon']}"
            col1, col2 = st.columns([1, 3])
            with col1:
                st.image(icon_url, width=80)
            with col2:
                st.write(f"**Condition:** {condition}")
                st.write(f"**Temperature:** {current_data['temp_c']}°C / {current_data['temp_f']}°F")
                st.write(f"**Feels Like:** {current_data['feelslike_c']}°C / {current_data['feelslike_f']}°F")
            
            # More weather details
            st.write(f"**Humidity:** {current_data['humidity']}%")
            st.write(f"**Wind:** {current_data['wind_kph']} km/h, {current_data['wind_dir']}")
            st.write(f"**Pressure:** {current_data['pressure_mb']} mb")
            st.write(f"**Visibility:** {current_data['vis_km']} km")
            st.write(f"**UV Index:** {current_data['uv']}")
            
            # Create a gauge chart for temperature
            fig = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = current_data['temp_c'],
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': "Temperature (°C)"},
                gauge = {
                    'axis': {'range': [-20, 50]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [-20, 0], 'color': "lightblue"},
                        {'range': [0, 15], 'color': "lightgreen"},
                        {'range': [15, 25], 'color': "yellow"},
                        {'range': [25, 35], 'color': "orange"},
                        {'range': [35, 50], 'color': "red"}
                    ],
                }
            ))
            st.plotly_chart(fig, use_container_width=True)
            
            # Create a gauge chart for humidity
            fig = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = current_data['humidity'],
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': "Humidity (%)"},
                gauge = {
                    'axis': {'range': [0, 100]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, 30], 'color': "yellow"},
                        {'range': [30, 70], 'color': "lightgreen"},
                        {'range': [70, 100], 'color': "lightblue"}
                    ],
                }
            ))
            st.plotly_chart(fig, use_container_width=True)

# Display saved weather data
if view_saved_data:
    st.header("Saved Weather Data")
    weather_history = db_handler.get_weather_history()
    
    if weather_history is not None and not weather_history.empty:
        # Display as a table
        st.subheader("Weather Records")
        st.dataframe(weather_history[['formatted_date', 'location_name', 'temperature', 'humidity', 'condition_text']])
        
        # Create a temperature chart
        st.subheader("Temperature History")
        fig = px.line(
            weather_history, 
            x='date_time', 
            y='temperature',
            color='location_name',
            labels={'temperature': 'Temperature (°C)', 'date_time': 'Date & Time'},
            title='Temperature History'
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Create a humidity chart
        st.subheader("Humidity History")
        fig = px.line(
            weather_history, 
            x='date_time', 
            y='humidity',
            color='location_name',
            labels={'humidity': 'Humidity (%)', 'date_time': 'Date & Time'},
            title='Humidity History'
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No saved weather data found. Save some weather data first!")
else:
    # Get and display weather data
    if location:
        weather_data1 = get_weather_data(location, selected_datetime1)
        
        if compare_dates:
            weather_data2 = get_weather_data(location, selected_datetime2)
            col1, col2 = st.columns(2)
            
            if weather_data1:
                display_weather_data(weather_data1, selected_datetime1, col1)
                
                # Add save button for first date
                with col1:
                    if st.button("Save First Date Weather Data"):
                        save_success = db_handler.save_weather_data(weather_data1, selected_datetime1)
                        if save_success:
                            st.success("Weather data saved to database successfully!")
                        else:
                            st.error("Failed to save weather data to database")
            
            if weather_data2:
                display_weather_data(weather_data2, selected_datetime2, col2)
                
                # Add save button for second date
                with col2:
                    if st.button("Save Second Date Weather Data"):
                        save_success = db_handler.save_weather_data(weather_data2, selected_datetime2)
                        if save_success:
                            st.success("Second date weather data saved to database successfully!")
                        else:
                            st.error("Failed to save second date weather data to database")
        else:
            if weather_data1:
                # Create a container for single date view
                single_view = st.container()
                display_weather_data(weather_data1, selected_datetime1, single_view)
                
                # Add save button
                if st.button("Save Weather Data to Database"):
                    save_success = db_handler.save_weather_data(weather_data1, selected_datetime1)
                    if save_success:
                        st.success("Weather data saved to database successfully!")
                    else:
                        st.error("Failed to save weather data to database")