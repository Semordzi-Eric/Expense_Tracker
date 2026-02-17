import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from gspread_dataframe import set_with_dataframe
from sqlalchemy import create_engine
from sqlalchemy.engine import URL

# ... SQL Server connection stays the same ...

# ---------------- GOOGLE SHEETS (STREAMLIT SECRETS) ----------------
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

# Use the service account stored in Streamlit secrets
creds_dict = dict(st.secrets["gcp_service_account"])
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)

client = gspread.authorize(creds)
spreadsheet = client.open("Streamlit Database")
