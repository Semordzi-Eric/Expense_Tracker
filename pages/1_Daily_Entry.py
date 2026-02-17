import streamlit as st
import pandas as pd
from datetime import date
import gspread
from gspread_dataframe import set_with_dataframe
import json

st.title("📅 Daily Expense Entry")

# ---------------- GOOGLE SHEETS ----------------
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

# Load creds from Streamlit secrets
creds_dict = json.loads(st.secrets["GSHEET_CREDS_JSON"])
client = gspread.service_account_from_dict(creds_dict)
spreadsheet = client.open("Streamlit Database")
worksheet = spreadsheet.worksheet("daily_expenses")

with st.form("daily_expense_form"):
    expense_date = st.date_input("Expense Date", date.today())

    col1, col2 = st.columns(2)
    with col1:
        transport = st.number_input("Transport (₵)", 0.0)
        food = st.number_input("Food (₵)", 0.0)

    with col2:
        data = st.number_input("Data (₵)", 0.0)
        other = st.number_input("Other (₵)", 0.0)

    submit = st.form_submit_button("Save Expense")

if submit:
    # Read existing data
    try:
        df_existing = pd.DataFrame(worksheet.get_all_records())
    except gspread.exceptions.APIError:
        df_existing = pd.DataFrame(columns=["expense_date","transport","food","data","other"])

    # Append new entry
    df_new = pd.DataFrame([{
        "expense_date": str(expense_date),
        "transport": transport,
        "food": food,
        "data": data,
        "other": other
    }])
    df_updated = pd.concat([df_existing, df_new], ignore_index=True)

    # Clear worksheet and write updated data
    worksheet.clear()
    set_with_dataframe(worksheet, df_updated, include_index=False)

    st.success("✅ Expense saved successfully!")
