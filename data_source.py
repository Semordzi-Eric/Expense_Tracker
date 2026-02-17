import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

@st.cache_resource
def connect_gsheet():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]

    creds = ServiceAccountCredentials.from_json_keyfile_dict(
        st.secrets["gcp_service_account"], scope
    )

    client = gspread.authorize(creds)
    return client.open("Streamlit Database")


@st.cache_data(ttl=60)
def load_table(table_name):
    sheet = connect_gsheet()
    ws = sheet.worksheet(table_name)
    data = ws.get_all_records()
    return pd.DataFrame(data)
