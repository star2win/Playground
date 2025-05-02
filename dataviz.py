import os
from dotenv import load_dotenv
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sqlalchemy import create_engine

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

# SQLAlchemy connection string for SQL Server (ODBC Driver 18)
connection_string = (
    f"mssql+pyodbc://{username}:{password}@{server}/{database}"
    "?driver=ODBC+Driver+18+for+SQL+Server"
    "&Encrypt=yes&TrustServerCertificate=yes&Connection+Timeout=30"
)

# Your provided SQL query
sql_query = '''
WITH LastServiceOrder AS (
    SELECT
        CustId,
        MAX(DatePosted) AS LastServiceDate
    FROM SM.RepairOrder
    WHERE CustId IS NOT NULL
    GROUP BY CustId
)
SELECT
    C.FirstName,
    C.LastName,
    C.EmailAddress,
    MAX(PN.PhoneNum) AS PhoneNumber,
    LSO.LastServiceDate
FROM
    SM.Customers AS C
INNER JOIN
    LastServiceOrder AS LSO
    ON C.CustId = LSO.CustId
LEFT JOIN
    SM.CustomerPhones AS CP
    ON C.CustId = CP.CustId
LEFT JOIN
    SM.PhoneNum AS PN
    ON CP.PhoneId = PN.PhoneId
WHERE
    C.IsDeleted = 0
GROUP BY
    C.CustId,
    C.FirstName,
    C.LastName,
    C.EmailAddress,
    LSO.LastServiceDate
ORDER BY
    LSO.LastServiceDate DESC;
'''

try:
    # Create SQLAlchemy engine
    engine = create_engine(connection_string)
    print("SQLAlchemy engine created!")

    # Fetch data into a pandas DataFrame
    with engine.connect() as conn:
        df = pd.read_sql_query(sql_query, conn)
    print(df.head())

    # Convert LastServiceDate to datetime
    df['LastServiceDate'] = pd.to_datetime(df['LastServiceDate'])
    # Extract year and month for grouping
    df['YearMonth'] = df['LastServiceDate'].dt.to_period('M')

    # Count unique customers serviced per month
    monthly_counts = df.groupby('YearMonth').size().reset_index(name='CustomersServiced')

    # Plotting
    sns.set(style="whitegrid")
    plt.figure(figsize=(12, 6))
    ax = sns.barplot(x=monthly_counts['YearMonth'].astype(str), y=monthly_counts['CustomersServiced'], color='skyblue')
    plt.xticks(rotation=45)
    plt.xlabel('Month')
    plt.ylabel('Number of Customers Serviced')
    plt.title('Customers Serviced by Month')

    # Annotate each bar with the value
    for i, v in enumerate(monthly_counts['CustomersServiced']):
        ax.text(i, v + 0.5, str(v), color='black', ha='center', va='bottom', fontweight='bold')

    plt.tight_layout()
    plt.show()

except Exception as e:
    print(f"An error occurred: {e}")