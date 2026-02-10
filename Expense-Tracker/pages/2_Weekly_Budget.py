import streamlit as st
import pandas as pd
from datetime import date
from db import engine

st.title("📊 Weekly Budget Setup")

week_start = st.date_input("Week Start Date", date.today())

money_available = st.number_input("Money Available (₵)", 0.0)
weekly_budget = st.number_input("Budget for the Week (₵)", 0.0)
expected_income = st.number_input("Expected Income (₵)", 0.0)

if st.button("Save Weekly Budget"):
    df = pd.DataFrame([{
        "week_start": week_start,
        "money_available": money_available,
        "weekly_budget": weekly_budget,
        "expected_income": expected_income
    }])

    df.to_sql("weekly_budget", engine, if_exists="append", index=False)
    st.success("✅ Weekly budget saved!")
    

