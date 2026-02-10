import streamlit as st
import pandas as pd
from datetime import date
from db import engine
from sqlalchemy import text

st.title("📅 Daily Expense Entry")

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
    with engine.begin() as conn:
        conn.execute(
            text("""
            INSERT INTO daily_expenses (expense_date, transport, food, data, other)
            VALUES (:expense_date, :transport, :food, :data, :other)
            """),
            {
                "expense_date": expense_date,  # stays DATE
                "transport": transport,
                "food": food,
                "data": data,
                "other": other
            }
        )
    st.success("✅ Expense saved successfully!")
