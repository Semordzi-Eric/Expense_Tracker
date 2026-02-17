import streamlit as st
import pandas as pd
from datetime import date
import gspread
from gspread_dataframe import set_with_dataframe
from oauth2client.service_account import ServiceAccountCredentials
import os
import json

st.title("Daily Budget Setup")

# ---------------- GOOGLE SHEETS ----------------
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

# Load creds from Streamlit secrets
creds_dict = json.loads(st.secrets["GSHEET_CREDS_JSON"])
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)
spreadsheet = client.open("Streamlit Database")
worksheet = spreadsheet.worksheet("daily_budget")

# ---------------- STREAMLIT FORM ----------------
budget_date = st.date_input("Budget Date", date.today())
budget_amount = st.number_input("Daily Budget Amount (₵)", min_value=0.0)

if st.button("Save Daily Budget"):
    # Create new row
    df_new = pd.DataFrame([{
        "budget_date": str(budget_date),  # convert date to string
        "budget_amount": budget_amount
    }])

    # Read existing data
    try:
        df_existing = pd.DataFrame(worksheet.get_all_records())
    except gspread.exceptions.APIError:
        df_existing = pd.DataFrame(columns=["budget_date", "budget_amount"])

    # Append new row
    df_updated = pd.concat([df_existing, df_new], ignore_index=True)

    # Clear and write back
    worksheet.clear()
    set_with_dataframe(worksheet, df_updated, include_index=False)

    st.success("✅ Daily budget saved")
