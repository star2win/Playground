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

def split_and_write_mermaid_files(tables, relationships, out_dir="."):
    # 1. Identify all schemas
    schemas = set(table.split('.', 1)[0] for table in tables)
    schema_tables = {schema: [] for schema in schemas}
    for table in tables:
        schema = table.split('.', 1)[0]
        schema_tables[schema].append(table)
    # 2. Group relationships
    schema_relationships = {schema: [] for schema in schemas}
    cross_schema_relationships = []
    for rel in relationships:
        fk_schema = rel['fk_table'].split('.', 1)[0]
        pk_schema = rel['pk_table'].split('.', 1)[0]
        if fk_schema == pk_schema:
            schema_relationships[fk_schema].append(rel)
        else:
            cross_schema_relationships.append(rel)
    # 3. Write one file per schema
    for schema in schemas:
        file_path = os.path.join(out_dir, f"db_mermaid_{schema}.mmd")
        lines = ["erDiagram"]
        for table in schema_tables[schema]:
            lines.append(f"    {quote_table(table)} {{")
            for column, dtype in tables[table]:
                lines.append(f"        {dtype} {column}")
            lines.append("    }")
        for rel in schema_relationships[schema]:
            lines.append(f"    {quote_table(rel['pk_table'])} ||--o{{ {quote_table(rel['fk_table'])} : \"{rel['constraint_name']}\"")
        # Optionally, add stubs for cross-schema relationships
        for rel in cross_schema_relationships:
            if rel['pk_table'] in schema_tables[schema] or rel['fk_table'] in schema_tables[schema]:
                lines.append(f"    %% Cross-schema: {quote_table(rel['pk_table'])} ||--o{{ {quote_table(rel['fk_table'])} : \"{rel['constraint_name']}\"")
        with open(file_path, "w") as f:
            f.write('\n'.join(lines))
    # 4. Write cross-schema relationships to their own file
    cross_path = os.path.join(out_dir, "db_mermaid_cross_schema.mmd")
    cross_lines = ["erDiagram"]
    involved_tables = set()
    for rel in cross_schema_relationships:
        involved_tables.add(rel['pk_table'])
        involved_tables.add(rel['fk_table'])
    for table in involved_tables:
        cross_lines.append(f"    {quote_table(table)} {{")
        for column, dtype in tables[table]:
            cross_lines.append(f"        {dtype} {column}")
        cross_lines.append("    }")
    for rel in cross_schema_relationships:
        cross_lines.append(f"    {quote_table(rel['pk_table'])} ||--o{{ {quote_table(rel['fk_table'])} : \"{rel['constraint_name']}\"")
    with open(cross_path, "w") as f:
        f.write('\n'.join(cross_lines))

try:
    # Establish connection
    conn = pyodbc.connect(connection_string)
    print("Connection successful!")
    cursor = conn.cursor()

    tables = get_tables_and_columns(cursor)
    relationships = get_foreign_keys(cursor)
    split_and_write_mermaid_files(tables, relationships, out_dir=".")
    print("Mermaid ER diagrams split by schema and cross-schema relationships.")

    # Clean up
    cursor.close()
    conn.close()

except Exception as e:
    print(f"Failed to connect or execute query: {e}")