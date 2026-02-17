import streamlit as st
import pandas as pd
from datetime import date
import gspread
from gspread_dataframe import set_with_dataframe
from oauth2client.service_account import ServiceAccountCredentials

st.title("📊 Weekly Budget Setup")

# ---------------- GOOGLE SHEETS ----------------
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

# Use the service account stored in Streamlit secrets
creds_dict = dict(st.secrets["gcp_service_account"])
creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")  # convert escaped newlines

creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)
spreadsheet = client.open("Streamlit Database")
worksheet = spreadsheet.worksheet("weekly_budget")

# ---------------- STREAMLIT FORM ----------------
week_start = st.date_input("Week Start Date", date.today())
money_available = st.number_input("Money Available (₵)", 0.0)
weekly_budget = st.number_input("Budget for the Week (₵)", 0.0)
expected_income = st.number_input("Expected Income (₵)", 0.0)

if st.button("Save Weekly Budget"):
    # Read existing data
    try:
        df_existing = pd.DataFrame(worksheet.get_all_records())
    except gspread.exceptions.APIError:
        df_existing = pd.DataFrame(columns=["week_start","money_available","weekly_budget","expected_income"])

    # Append new entry
    df_new = pd.DataFrame([{
        "week_start": str(week_start),
        "money_available": money_available,
        "weekly_budget": weekly_budget,
        "expected_income": expected_income
    }])
    df_updated = pd.concat([df_existing, df_new], ignore_index=True)

    # Clear worksheet and write updated data
    worksheet.clear()
    set_with_dataframe(worksheet, df_updated, include_index=False)

    st.success("✅ Weekly budget saved!")
