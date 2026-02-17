import gspread
from oauth2client.service_account import ServiceAccountCredentials

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

creds = ServiceAccountCredentials.from_json_keyfile_name(
    "service_account.json", scope
)

client = gspread.authorize(creds)

# change to your sheet name
spreadsheet = client.open("streamlit databse")

print("Connected! Worksheets found:")
for ws in spreadsheet.worksheets():
    print("-", ws.title)
