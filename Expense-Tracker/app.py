import streamlit as st

st.set_page_config(
    page_title="Personal Expense Tracker",
    page_icon="💰",
    layout="wide"
)

st.title("💰 Personal Expense Tracker")

st.markdown("""
Welcome to your **private expense tracking app**.

Use the menu on the left to:
- Add daily expenses
- Set weekly budgets
- View analytics
""")
