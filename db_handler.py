import sqlite3
from datetime import datetime
import pandas as pd
import os

def connect_to_sqlite():
    """Establish connection to SQLite database"""
    try:
        db_path = os.path.join(os.path.dirname(__file__), 'weather_data.db')
        connection = sqlite3.connect(db_path)
        return connection
    except sqlite3.Error as err:
        print(f"Error connecting to SQLite: {err}")
        return None

def initialize_database():
    """Create database and tables if they don't exist"""
    try:
        conn = connect_to_sqlite()
        if not conn:
            return False
        
        cursor = conn.cursor()
        
        # Create weather_records table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS weather_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            location_name TEXT,
            latitude REAL,
            longitude REAL,
            date_time TEXT,
            temperature REAL,
            feels_like REAL,
            humidity INTEGER,
            wind_speed REAL,
            condition_text TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except sqlite3.Error as err:
        print(f"Error initializing database: {err}")
        return False

def save_weather_data(weather_data, datetime_obj):
    """Save weather data to the database"""
    try:
        conn = connect_to_sqlite()
        if not conn:
            return False
        
        cursor = conn.cursor()
        
        # Extract location data
        location_info = weather_data['location']
        location_name = f"{location_info['name']}, {location_info['country']}"
        latitude = location_info['lat']
        longitude = location_info['lon']
        
        # Extract weather data
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
        
        # Format date_time
        date_time = datetime_obj.strftime('%Y-%m-%d %H:%M:%S')
        
        # Insert data into the database
        query = """
        INSERT INTO weather_records 
        (location_name, latitude, longitude, date_time, temperature, feels_like, humidity, wind_speed, condition_text)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        values = (
            location_name,
            latitude,
            longitude,
            date_time,
            current_data['temp_c'],
            current_data['feelslike_c'],
            current_data['humidity'],
            current_data['wind_kph'],
            current_data['condition']['text']
        )
        
        cursor.execute(query, values)
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Error saving weather data: {e}")
        import traceback
        traceback.print_exc()
        return False

def get_saved_weather_data():
    """Retrieve all saved weather data from the database"""
    try:
        conn = connect_to_sqlite()
        if not conn:
            return None
        
        query = "SELECT * FROM weather_records ORDER BY date_time DESC"
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except Exception as e:
        print(f"Error retrieving weather data: {e}")
        return None

def get_weather_history():
    """Get saved weather data for display in the app"""
    try:
        df = get_saved_weather_data()
        if df is None or df.empty:
            return None
        
        # Format the data for display
        df['date_time'] = pd.to_datetime(df['date_time'])
        df['formatted_date'] = df['date_time'].dt.strftime('%Y-%m-%d %H:%M')
        
        return df
    except Exception as e:
        print(f"Error getting weather history: {e}")
        return None