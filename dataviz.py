import os
from dotenv import load_dotenv
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sqlalchemy import create_engine
import yaml

# Load environment variables from .env file
load_dotenv()

# Reference the variables
SQL_DATABASE = os.getenv('SQL_DATABASE')
SQL_USERNAME = os.getenv('SQL_USERNAME')
SQL_PASSWORD = os.getenv('SQL_PASSWORD')

#print(f"Database: {SQL_DATABASE}")
#print(f"Username: {SQL_USERNAME}")
#print(f"Password: {SQL_PASSWORD}")
print("\n\n")

# Connection parameters
server = '192.168.0.7'  # Replace with your Windows PC's IP address
database = SQL_DATABASE  # Use the loaded environment variable
username = SQL_USERNAME      # Use the loaded environment variable
password = SQL_PASSWORD  # Use the loaded environment variable

# SQLAlchemy connection string for SQL Server (ODBC Driver 18)
connection_string = (
    f"mssql+pyodbc://{username}:{password}@{server}/{database}"
    "?driver=ODBC+Driver+18+for+SQL+Server"
    "&Encrypt=yes&TrustServerCertificate=yes&Connection+Timeout=30"
)

# Load SQL queries from YAML file
with open('sql_queries.yaml', 'r') as f:
    queries = yaml.safe_load(f)

# List queries and prompt user to select
labels = list(queries.keys())
print("Available SQL Queries:")
for idx, label in enumerate(labels, 1):
    print(f"{idx}. {label}")

while True:
    try:
        selection = int(input(f"Select a query to run (1-{len(labels)}): "))
        if 1 <= selection <= len(labels):
            break
        else:
            print("Invalid selection. Try again.")
    except ValueError:
        print("Please enter a number.")

selected_label = labels[selection - 1]
sql_query = queries[selected_label]
print(f"Running query: {selected_label}")

try:
    # Create SQLAlchemy engine
    engine = create_engine(connection_string)
    print("SQLAlchemy engine created!")

    # Fetch data into a pandas DataFrame
    with engine.connect() as conn:
        df = pd.read_sql_query(sql_query, conn)
    print(df.head())

    # Determine which date column to use
    date_col = None
    if 'LastServiceDate' in df.columns:
        date_col = 'LastServiceDate'
        plot_title = 'Customers Serviced by Month'
        ylabel = 'Number of Customers Serviced'
    elif 'CompletionDate' in df.columns:
        date_col = 'CompletionDate'
        plot_title = 'Completed Repair Orders by Month'
        ylabel = 'Number of Completed Orders'
    elif 'OrderDate' in df.columns:
        date_col = 'OrderDate'
        plot_title = 'Repair Orders by Month'
        ylabel = 'Number of Repair Orders'
    else:
        print('No suitable date column found for time-based visualization.')
        print(df)
        exit(0)

    # Convert date column to datetime
    df[date_col] = pd.to_datetime(df[date_col])
    # Extract year and month for grouping
    df['YearMonth'] = df[date_col].dt.to_period('M')

    # Count records per month
    monthly_counts = df.groupby('YearMonth').size().reset_index(name='Count')

    # Plotting
    sns.set(style="whitegrid")
    plt.figure(figsize=(12, 6))
    ax = sns.barplot(x=monthly_counts['YearMonth'].astype(str), y=monthly_counts['Count'], color='skyblue')
    plt.xticks(rotation=90)  # Make x-axis labels vertical
    plt.xlabel('Month')
    plt.ylabel(ylabel)
    plt.title(plot_title)

    # Annotate each bar with the value
    for i, v in enumerate(monthly_counts['Count']):
        ax.text(i, v + 0.5, str(v), color='black', ha='center', va='bottom', fontweight='bold')

    plt.tight_layout()
    plt.show()

except Exception as e:
    print(f"An error occurred: {e}")