import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from gspread_dataframe import set_with_dataframe
from sqlalchemy import create_engine
from sqlalchemy.engine import URL

# ---------------- SQL SERVER ----------------
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

# ---------------- GOOGLE SHEETS (LOCAL FILE) ----------------
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

creds = ServiceAccountCredentials.from_json_keyfile_name(
    "service_account.json", scope
)

client = gspread.authorize(creds)
spreadsheet = client.open("Streamlit Database")

# ---------------- TABLES ----------------
tables = [
    "daily_expenses",
    "daily_budget",
    "weekly_budget",
    "users"
]

for table in tables:
    print(f"\nSyncing {table}...")

    df = pd.read_sql(f"SELECT * FROM {table}", engine)

    # If table empty -> create dummy header
    if df.empty:
        print("Table empty — creating headers only")
        df = pd.DataFrame(columns=df.columns)

    # Get or create worksheet
    try:
        worksheet = spreadsheet.worksheet(table)
    except gspread.exceptions.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(title=table, rows="100", cols="20")

    # Resize sheet instead of destructive clear
    worksheet.resize(rows=max(len(df) + 1, 2), cols=len(df.columns))

    # Upload data
    set_with_dataframe(worksheet, df, include_index=False)

    print(f"{table} synced ({len(df)} rows)")

print("\nALL TABLES SYNCED SUCCESSFULLY")
