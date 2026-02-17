import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# ---------------- SCOPE ----------------
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

# ---------------- CREDENTIALS ----------------
# Load credentials from environment variable (Streamlit Secret)
creds_dict = json.loads(os.environ["GSHEET_CREDS_JSON"])
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)

# ---------------- CLIENT ----------------
client = gspread.authorize(creds)

# ---------------- OPEN SPREADSHEET ----------------
spreadsheet = client.open("Streamlit Database")  # make sure this matches exactly

print("Connected! Worksheets found:")
for ws in spreadsheet.worksheets():
    print("-", ws.title)
