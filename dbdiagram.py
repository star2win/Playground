import pyodbc
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Reference the variables
SQL_DATABASE = os.getenv('SQL_DATABASE')
SQL_USERNAME = os.getenv('SQL_USERNAME')
SQL_PASSWORD = os.getenv('SQL_PASSWORD')

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

def get_tables_and_columns(cursor):
    # Query all tables and columns, preserving schema
    cursor.execute('''
        SELECT
            TABLE_SCHEMA,
            TABLE_NAME,
            COLUMN_NAME,
            DATA_TYPE
        FROM INFORMATION_SCHEMA.COLUMNS
        ORDER BY TABLE_SCHEMA, TABLE_NAME, ORDINAL_POSITION
    ''')
    results = cursor.fetchall()
    tables = {}
    for schema, table, column, dtype in results:
        full_table = f"{schema}.{table}"
        if full_table not in tables:
            tables[full_table] = []
        tables[full_table].append((column, dtype))
    return tables

def get_foreign_keys(cursor):
    # Query all foreign key relationships, preserving schema
    cursor.execute('''
        SELECT
            fk.CONSTRAINT_NAME,
            fk.TABLE_SCHEMA AS FK_SCHEMA,
            fk.TABLE_NAME AS FK_TABLE,
            fk.COLUMN_NAME AS FK_COLUMN,
            pk.TABLE_SCHEMA AS PK_SCHEMA,
            pk.TABLE_NAME AS PK_TABLE,
            pk.COLUMN_NAME AS PK_COLUMN
        FROM INFORMATION_SCHEMA.REFERENTIAL_CONSTRAINTS rc
        JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE fk
            ON rc.CONSTRAINT_NAME = fk.CONSTRAINT_NAME
        JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE pk
            ON rc.UNIQUE_CONSTRAINT_NAME = pk.CONSTRAINT_NAME
            AND fk.ORDINAL_POSITION = pk.ORDINAL_POSITION
        ORDER BY fk.TABLE_SCHEMA, fk.TABLE_NAME
    ''')
    results = cursor.fetchall()
    relationships = []
    for (fk_name, fk_schema, fk_table, fk_column, pk_schema, pk_table, pk_column) in results:
        fk_full_table = f"{fk_schema}.{fk_table}"
        pk_full_table = f"{pk_schema}.{pk_table}"
        relationships.append({
            'fk_table': fk_full_table,
            'fk_column': fk_column,
            'pk_table': pk_full_table,
            'pk_column': pk_column,
            'constraint_name': fk_name
        })
    return relationships

def quote_table(table_name):
    return f'"{table_name}"'

def generate_mermaid_er(tables, relationships):
    lines = ["erDiagram"]
    for table, columns in tables.items():
        lines.append(f"    {quote_table(table)} {{")
        for column, dtype in columns:
            lines.append(f"        {dtype} {column}")
        lines.append("    }")
    # Add relationships
    for rel in relationships:
        # Mermaid ER syntax: "TableA" ||--o{ "TableB" : "FK_name"
        lines.append(f"    {quote_table(rel['pk_table'])} ||--o{{ {quote_table(rel['fk_table'])} : \"{rel['constraint_name']}\"")
    return '\n'.join(lines)

try:
    # Establish connection
    conn = pyodbc.connect(connection_string)
    print("Connection successful!")
    cursor = conn.cursor()

    tables = get_tables_and_columns(cursor)
    relationships = get_foreign_keys(cursor)
    print(f"Foreign key relationships found: {relationships}")  # Debug print
    mermaid_text = generate_mermaid_er(tables, relationships)

    # Save to file
    with open("db_mermaid.mmd", "w") as f:
        f.write(mermaid_text)
    print("Mermaid ER diagram with relationships saved to db_mermaid.mmd")

    # Clean up
    cursor.close()
    conn.close()

except Exception as e:
    print(f"Failed to connect or execute query: {e}")