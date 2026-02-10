import streamlit as st
import pandas as pd
from datetime import date
from db import engine

st.title("🎯 Daily Budget Setup")

budget_date = st.date_input("Budget Date", date.today())
budget_amount = st.number_input("Daily Budget Amount (₵)", min_value=0.0)

if st.button("Save Daily Budget"):
    df = pd.DataFrame([{
        "budget_date": budget_date,
        "budget_amount": budget_amount
    }])

    df.to_sql("daily_budget", engine, if_exists="append", index=False)
    st.success("✅ Daily budget saved")
