from sqlalchemy import create_engine
from sqlalchemy.engine import URL

server = r"HFTL-RA-0013\SQLEXPRESS03"
database = "expense_tracker"

connection_url = URL.create(
    "mssql+pyodbc",
    host=server,
    database=database,
    query={
        "driver": "ODBC Driver 17 for SQL Server",
        "Trusted_Connection": "yes"
    }
)

engine = create_engine(connection_url)

try:
    with engine.connect() as connection:
        print("Connection successful!")
except Exception as e:
    print("Connection failed:", e)
