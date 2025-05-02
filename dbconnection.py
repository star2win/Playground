import pyodbc
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Reference the variables
SQL_DATABASE = os.getenv('SQL_DATABASE')
SQL_USERNAME = os.getenv('SQL_USERNAME')
SQL_PASSWORD = os.getenv('SQL_PASSWORD')

# Example usage: print or use these variables in your DB connection logic
print(f"Database: {SQL_DATABASE}")
print(f"Username: {SQL_USERNAME}")
print(f"Password: {SQL_PASSWORD}")

# Connection parameters
server = '192.168.0.7'  # Replace with your Windows PC's IP address
database = SQL_DATABASE  # Use the loaded environment variable
username = SQL_USERNAME      # Use the loaded environment variable
password = SQL_PASSWORD  # Use the loaded environment variable

# Connection string
connection_string = (
    f'DRIVER={{ODBC Driver 18 for SQL Server}};'
    f'SERVER={server};'
    f'DATABASE={database};'
    f'UID={username};'
    f'PWD={password};'
    'Encrypt=yes;'
    'TrustServerCertificate=yes;'
    'Connection Timeout=30;'
)

try:
    # Establish connection
    conn = pyodbc.connect(connection_string)
    print("Connection successful!")
    cursor = conn.cursor()

    # Execute a sample query
    cursor.execute("SELECT * FROM SM.Customers")  # Replace with your table name
    rows = cursor.fetchall()

    # Print results
    for row in rows:
        print(row)

    # Clean up
    cursor.close()
    conn.close()

except Exception as e:
    print(f"Failed to connect or execute query: {e}")