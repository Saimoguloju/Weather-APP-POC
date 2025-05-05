import sqlite3
import os
import pandas as pd
from tabulate import tabulate  # Import the function, not just the module

def print_weather_table():
    """Print the contents of the weather_records table in a formatted way"""
    try:
        # Connect to the SQLite database
        db_path = os.path.join(os.path.dirname(__file__), 'weather_data.db')
        if not os.path.exists(db_path):
            print(f"Database file not found at: {db_path}")
            return False
            
        connection = sqlite3.connect(db_path)
        
        # Get table info
        cursor = connection.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print("Available tables in the database:")
        for table in tables:
            print(f"- {table[0]}")
        
        # Query the weather_records table
        query = "SELECT * FROM weather_records ORDER BY date_time DESC"
        df = pd.read_sql_query(query, connection)
        
        if df.empty:
            print("No records found in the weather_records table.")
            return False
        
        # Print table info
        print(f"\nTotal records: {len(df)}")
        print(f"Columns: {', '.join(df.columns)}")
        
        # Format the data for better display
        display_df = df.copy()
        display_df['date_time'] = pd.to_datetime(display_df['date_time'])
        display_df['formatted_date'] = display_df['date_time'].dt.strftime('%Y-%m-%d %H:%M')
        
        # Select only the most relevant columns for display
        display_columns = ['id', 'location_name', 'formatted_date', 'temperature', 
                          'humidity', 'condition_text', 'created_at']
        
        # Print the table in a nice format - FIX: Use tabulate function correctly
        print("\nWeather Records:")
        print(tabulate(display_df[display_columns].values, 
                      headers=display_columns, 
                      tablefmt='pretty', 
                      showindex=False))
        
        # Close the connection
        connection.close()
        return True
        
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False

def analyze_database():
    """Print database statistics and analysis"""
    try:
        # Connect to the SQLite database
        db_path = os.path.join(os.path.dirname(__file__), 'weather_data.db')
        if not os.path.exists(db_path):
            print(f"Database file not found at: {db_path}")
            return False
            
        connection = sqlite3.connect(db_path)
        cursor = connection.cursor()
        
        # Get database file size
        db_size = os.path.getsize(db_path)
        print(f"\nDatabase file size: {db_size/1024:.2f} KB")
        
        # Get table info
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        for table in tables:
            table_name = table[0]
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            print(f"\nTable: {table_name}")
            print(f"Columns: {len(columns)}")
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            row_count = cursor.fetchone()[0]
            print(f"Row count: {row_count}")
            
            # Get column details
            print("\nColumn details:")
            col_info = []
            for col in columns:
                col_info.append({
                    "cid": col[0],
                    "name": col[1],
                    "type": col[2],
                    "notnull": "NOT NULL" if col[3] else "",
                    "default": col[4] if col[4] is not None else "",
                    "pk": "PRIMARY KEY" if col[5] else ""
                })
            
            # FIX: Use tabulate function correctly
            headers = ["cid", "name", "type", "notnull", "default", "pk"]
            col_info_list = [[item[key] for key in headers] for item in col_info]
            print(tabulate(col_info_list, headers=headers, tablefmt="pretty"))
            
            # If it's the weather_records table, show some statistics
            if table_name == 'weather_records' and row_count > 0:
                print("\nWeather statistics:")
                
                # Average temperature
                cursor.execute("SELECT AVG(temperature) FROM weather_records")
                avg_temp = cursor.fetchone()[0]
                print(f"Average temperature: {avg_temp:.2f}°C")
                
                # Min/Max temperature
                cursor.execute("SELECT MIN(temperature), MAX(temperature) FROM weather_records")
                min_temp, max_temp = cursor.fetchone()
                print(f"Temperature range: {min_temp}°C to {max_temp}°C")
                
                # Average humidity
                cursor.execute("SELECT AVG(humidity) FROM weather_records")
                avg_humidity = cursor.fetchone()[0]
                print(f"Average humidity: {avg_humidity:.2f}%")
                
                # Most common condition
                cursor.execute("""
                    SELECT condition_text, COUNT(*) as count 
                    FROM weather_records 
                    GROUP BY condition_text 
                    ORDER BY count DESC 
                    LIMIT 3
                """)
                conditions = cursor.fetchall()
                print("\nMost common weather conditions:")
                for condition in conditions:
                    print(f"- {condition[0]}: {condition[1]} records")
                
                # Most recorded location
                cursor.execute("""
                    SELECT location_name, COUNT(*) as count 
                    FROM weather_records 
                    GROUP BY location_name 
                    ORDER BY count DESC 
                    LIMIT 3
                """)
                locations = cursor.fetchall()
                print("\nMost recorded locations:")
                for location in locations:
                    print(f"- {location[0]}: {location[1]} records")
        
        connection.close()
        return True
        
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    print("Weather Database Utility")
    print("=======================")
    
    # Check if tabulate is installed
    try:
        from tabulate import tabulate
    except ImportError:
        print("The 'tabulate' package is required. Installing...")
        import subprocess
        subprocess.check_call(["pip", "install", "tabulate"])
        from tabulate import tabulate
    
    print_weather_table()
    analyze_database()
    
    print("\nDone!")