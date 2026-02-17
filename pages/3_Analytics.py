import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import calendar
from datetime import datetime, timedelta
from io import BytesIO
from utils import export_pdf
from data_source import load_table  # new import for Google Sheets

# try sklearn, but continue gracefully if not available
try:
    from sklearn.ensemble import IsolationForest
    from sklearn.cluster import KMeans
    SKLEARN_AVAILABLE = True
except Exception:
    SKLEARN_AVAILABLE = False

st.set_page_config(page_title="💰 Smart Spending Analytics", layout="wide", page_icon="💰")
st.title("💰 Smart Spending Analytics Dashboard")
st.markdown("### Track, Analyze, and Optimize Your Expenses")

# ---------------------
# Helpers & Configuration
# ---------------------
def to_excel_bytes(df_dict):
    """Export multiple dataframes to Excel"""
    b = BytesIO()
    with pd.ExcelWriter(b, engine="openpyxl") as writer:
        for sheet, df in df_dict.items():
            df.to_excel(writer, sheet_name=sheet, index=False)
    return b.getvalue()

def style_metric_card(value, label, delta=None, delta_color="auto"):
    """Create styled metric cards with proper type handling"""
    try:
        if delta is not None:
            # Convert delta to string if it's not None
            delta_str = str(delta)
            
            if delta_color == "auto":
                # Try to extract numeric value from delta for color determination
                try:
                    # Remove non-numeric characters (except minus, plus, and decimal)
                    delta_clean = ''.join(c for c in delta_str if c.isdigit() or c in ['-', '+', '.', '%'])
                    delta_numeric = float(delta_clean.replace('%', '')) if delta_clean else 0
                    color = "normal" if delta_numeric >= 0 else "inverse"
                except:
                    color = "normal"
            else:
                color = delta_color
                
            return st.metric(label, value, delta=delta_str, delta_color=color)
        else:
            return st.metric(label, value)
    except Exception as e:
        # Fallback to simple metric if styling fails
        st.metric(label, value)

def categorize_spending_behavior(avg_daily, volatility, burn_rate):
    """Categorize spending behavior"""
    try:
        if burn_rate > 120:
            return "🚨 Overspending", "red"
        elif burn_rate > 90:
            return "⚠️ Near Limit", "orange"
        elif volatility > avg_daily * 0.7:
            return "📊 Volatile", "blue"
        elif avg_daily < 20:
            return "✅ Frugal", "green"
        else:
            return "📈 Balanced", "green"
    except:
        return "📊 Analyzing", "blue"

def detect_spending_patterns(df):
    """Detect recurring patterns and habits"""
    patterns = []
    
    try:
        if 'expense_date' in df.columns and 'total' in df.columns:
            # Check for daily patterns
            daily_pattern = df.groupby(df['expense_date'].dt.dayofweek)['total'].mean()
            if len(daily_pattern) > 1 and daily_pattern.max() > 0:
                if daily_pattern.max() / daily_pattern.min() > 2:
                    peak_day = daily_pattern.idxmax()
                    patterns.append(f"Peak spending on {calendar.day_name[peak_day]}s (+{((daily_pattern.max()/daily_pattern.min())-1)*100:.0f}%)")
            
            # Check for weekend vs weekday
            df['is_weekend'] = df['expense_date'].dt.dayofweek >= 5
            weekend_spend = df[df['is_weekend']]['total'].sum() if not df[df['is_weekend']].empty else 0
            weekday_spend = df[~df['is_weekend']]['total'].sum() if not df[~df['is_weekend']].empty else 1
            weekend_ratio = weekend_spend / weekday_spend if weekday_spend > 0 else 0
            if weekend_ratio > 1.5:
                patterns.append(f"Weekend spending is {weekend_ratio:.1f}x higher than weekdays")
    except Exception as e:
        st.warning(f"Could not detect patterns: {str(e)}")
    
    return patterns

def generate_insights(df, weekly_budget, burn_rate):
    """Generate actionable insights with error handling"""
    insights = []
    
    try:
        # Category insights
        category_cols = ["transport", "food", "data", "other"]
        existing_cats = [col for col in category_cols if col in df.columns]
        
        if existing_cats:
            category_totals = df[existing_cats].sum()
            if len(category_totals) > 0 and category_totals.sum() > 0:
                max_cat = category_totals.idxmax()
                max_pct = (category_totals.max() / category_totals.sum()) * 100
                
                if max_pct > 40:
                    insights.append({
                        "type": "category",
                        "message": f"**{max_cat.title()}** accounts for {max_pct:.0f}% of total spending",
                        "suggestion": f"Consider setting a specific budget for {max_cat} or finding alternatives"
                    })
        
        # Weekly insights
        if burn_rate > 100:
            try:
                days_left = 7 - (datetime.now().date() - pd.Timestamp('today').date()).weekday()
                if days_left > 0:
                    daily_limit = (weekly_budget - df['total'].sum()) / days_left
                    insights.append({
                        "type": "budget",
                        "message": f"**Budget Alert**: You've spent {burn_rate:.0f}% of weekly budget",
                        "suggestion": f"Limit daily spending to ₵{daily_limit:.2f} for the remaining {days_left} days"
                    })
            except:
                pass
        
        # Trend insights
        if 'expense_date' in df.columns and 'total' in df.columns:
            weekly_trend = df.set_index('expense_date').resample('W')['total'].sum()
            if len(weekly_trend) > 2:
                trend = (weekly_trend.iloc[-1] - weekly_trend.iloc[-2]) / weekly_trend.iloc[-2] * 100 if weekly_trend.iloc[-2] > 0 else 0
                if abs(trend) > 10:
                    insights.append({
                        "type": "trend",
                        "message": f"Weekly spending {'increased' if trend > 0 else 'decreased'} by {abs(trend):.0f}%",
                        "suggestion": "Review what caused this change to understand your spending habits"
                    })
    except Exception as e:
        st.warning(f"Could not generate insights: {str(e)}")
    
    return insights

# ---------------------
# Load data with caching
# ---------------------
@st.cache_data(ttl=300)
def load_data(start=None, end=None):
    """Load expense and budget data from Google Sheets"""

    try:
        expenses = load_table("daily_expenses")
        budget = load_table("weekly_budget")
        daily_budget = load_table("daily_budget")

        # ensure dates are datetime
        if "expense_date" in expenses.columns:
            expenses["expense_date"] = pd.to_datetime(expenses["expense_date"])

        if "budget_date" in daily_budget.columns:
            daily_budget["budget_date"] = pd.to_datetime(daily_budget["budget_date"])

        # filter range
        if start and end and not expenses.empty:
            expenses = expenses[
                (expenses["expense_date"] >= pd.to_datetime(start)) &
                (expenses["expense_date"] <= pd.to_datetime(end))
            ]

        return expenses, budget, daily_budget

    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

# ---------------------
# Sidebar Configuration
# ---------------------
with st.sidebar:
    st.header("⚙️ Dashboard Settings")
    
    # Date range with presets
    st.subheader("Date Range")
    date_preset = st.selectbox(
        "Quick Select",
        ["Last 30 days", "Last 90 days", "Last 6 months", "Year to Date", "Custom"]
    )
    
    if date_preset == "Custom":
        dr_default_end = pd.to_datetime("today")
        dr_default_start = dr_default_end - pd.Timedelta(days=90)
        date_range = st.date_input("Select Range", [dr_default_start.date(), dr_default_end.date()])
    else:
        end_date = pd.to_datetime("today")
        if date_preset == "Last 30 days":
            start_date = end_date - pd.Timedelta(days=30)
        elif date_preset == "Last 90 days":
            start_date = end_date - pd.Timedelta(days=90)
        elif date_preset == "Last 6 months":
            start_date = end_date - pd.Timedelta(days=180)
        else:  # Year to Date
            start_date = pd.to_datetime(f"{end_date.year}-01-01")
        date_range = [start_date.date(), end_date.date()]
    
    # Visualization settings
    st.subheader("Visualization")
    theme = st.selectbox("Chart Theme", ["plotly", "plotly_white", "plotly_dark", "seaborn"])
    color_scheme = st.selectbox("Color Scheme", ["Set1", "Set2", "Set3", "Pastel1", "Dark2"])
    
    # Analysis settings
    st.subheader("Analysis")
    anomaly_sensitivity = st.slider("Anomaly Detection Sensitivity", 1, 10, 5)
    enable_forecasting = st.checkbox("Enable Spending Forecast", value=True)
    enable_clustering = st.checkbox("Enable Transaction Clustering", value=False)
    
    # Budget settings
    weekly_budget_input = st.number_input("Weekly Budget (₵)", min_value=0, value=1000, step=50)
    
    st.markdown("---")
    st.caption("💡 *Use filters to focus on specific aspects of your spending*")

# Load data
try:
    start, end = date_range[0].isoformat(), date_range[1].isoformat()
    expenses, budget, daily_budget_df = load_data(start, end)
except:
    # Fallback if date_range is not properly set
    start = (datetime.now() - timedelta(days=30)).date().isoformat()
    end = datetime.now().date().isoformat()
    expenses, budget, daily_budget_df = load_data(start, end)

if expenses.empty:
    st.warning("⚠️ No expense data found for the selected date range.")
    st.info("Please check your database or adjust the date range.")
    st.stop()

# ---------------------
# Data Preparation with Error Handling
# ---------------------
try:
    # Ensure all required columns exist
    if "expense_date" not in expenses.columns:
        st.error("Column 'expense_date' not found in data. Please check your database schema.")
        st.stop()
    
    expenses["expense_date"] = pd.to_datetime(expenses["expense_date"])
    
    # Initialize category columns if they don't exist
    category_cols = ["transport", "food", "data", "other"]
    for col in category_cols:
        if col not in expenses.columns:
            expenses[col] = 0.0
    
    # Calculate totals
    expenses["total"] = expenses[category_cols].sum(axis=1)
    
    # Add derived columns
    expenses["day_name"] = expenses["expense_date"].dt.day_name()
    expenses["day_of_week"] = expenses["expense_date"].dt.dayofweek
    expenses["week_number"] = expenses["expense_date"].dt.isocalendar().week
    expenses["month"] = expenses["expense_date"].dt.month
    expenses["month_name"] = expenses["expense_date"].dt.month_name()
    expenses["is_weekend"] = expenses["day_of_week"] >= 5
    
    # Filter by date range
    filtered = expenses[
        (expenses["expense_date"] >= pd.to_datetime(start)) & 
        (expenses["expense_date"] <= pd.to_datetime(end))
    ].copy()
    
except Exception as e:
    st.error(f"Error preparing data: {str(e)}")
    st.stop()

# ---------------------
# Key Metrics Calculation with Error Handling
# ---------------------
try:
    total_spend = filtered["total"].sum()
    daily_spends = filtered.groupby("expense_date")["total"].sum()
    avg_daily_spend = daily_spends.mean() if not daily_spends.empty else 0
    max_daily_spend = daily_spends.max() if not daily_spends.empty else 0
    min_daily_spend = daily_spends.min() if not daily_spends.empty else 0
    total_days = filtered["expense_date"].nunique()
    transactions_count = len(filtered)
    
    # Weekly context
    weekly_budget = weekly_budget_input
    current_week_start = pd.to_datetime("today") - pd.Timedelta(days=pd.to_datetime("today").weekday())
    current_week_end = current_week_start + pd.Timedelta(days=6)
    weekly_expenses = filtered[
        (filtered["expense_date"] >= current_week_start) & 
        (filtered["expense_date"] <= current_week_end)
    ]
    weekly_spend = weekly_expenses["total"].sum()
    burn_rate = (weekly_spend / weekly_budget) * 100 if weekly_budget > 0 else 0
    
    # Previous period comparison
    try:
        period_duration = (pd.to_datetime(end) - pd.to_datetime(start)).days
        prev_period_start = pd.to_datetime(start) - pd.Timedelta(days=period_duration)
        prev_period_end = pd.to_datetime(start) - pd.Timedelta(days=1)
        
        prev_period_spend = expenses[
            (expenses["expense_date"] >= prev_period_start) & 
            (expenses["expense_date"] <= prev_period_end)
        ]["total"].sum()
        
        spend_change = total_spend - prev_period_spend
        spend_change_pct = (spend_change / prev_period_spend * 100) if prev_period_spend > 0 else 0
    except:
        prev_period_spend = 0
        spend_change = 0
        spend_change_pct = 0
    
except Exception as e:
    st.error(f"Error calculating metrics: {str(e)}")
    total_spend = 0
    avg_daily_spend = 0
    max_daily_spend = 0
    min_daily_spend = 0
    total_days = 0
    transactions_count = 0
    weekly_spend = 0
    burn_rate = 0
    spend_change = 0
    spend_change_pct = 0

# ---------------------
# Dashboard Header with Key Metrics
# ---------------------
st.markdown("## 📊 Executive Summary")

# Top metrics row
col1, col2, col3, col4 = st.columns(4)
with col1:
    style_metric_card(
        f"₵{total_spend:,.0f}",
        "Total Spend",
        f"{spend_change_pct:+.0f}%" if not pd.isna(spend_change_pct) else None,
        delta_color="auto"
    )
with col2:
    style_metric_card(
        f"₵{avg_daily_spend:.0f}",
        "Avg Daily Spend",
        f"Max: ₵{max_daily_spend:.0f}"
    )
with col3:
    behavior, color = categorize_spending_behavior(avg_daily_spend, filtered["total"].std(), burn_rate)
    style_metric_card(behavior, "Spending Profile")
with col4:
    style_metric_card(
        f"{burn_rate:.0f}%",
        "Weekly Budget Used",
        delta_color="inverse"
    )

# Insights row
st.markdown("## 💡 Key Insights")
insights = generate_insights(filtered, weekly_budget, burn_rate)

if insights:
    cols = st.columns(min(len(insights), 3))
    for idx, insight in enumerate(insights):
        if idx < len(cols):
            with cols[idx]:
                with st.container():
                    st.markdown(f"**{insight['message']}**")
                    st.caption(insight['suggestion'])
else:
    st.info("💎 Your spending patterns look healthy. Keep monitoring to maintain good habits!")

# ---------------------
# Main Dashboard Tabs
# ---------------------
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈 Overview", 
    "🗂️ Categories", 
    "📅 Timeline", 
    "🔍 Anomalies", 
    "💾 Export"
])

with tab1:
    # Spending Distribution
    st.subheader("💰 Spending Distribution")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Daily spending distribution
        try:
            daily_totals = filtered.groupby("expense_date")["total"].sum().reset_index()
            if not daily_totals.empty:
                fig1 = px.histogram(
                    daily_totals, 
                    x="total", 
                    nbins=20,
                    title="Distribution of Daily Spending",
                    labels={"total": "Daily Amount (₵)"},
                    color_discrete_sequence=['#636EFA']
                )
                fig1.update_layout(bargap=0.1)
                st.plotly_chart(fig1, use_container_width=True)
            else:
                st.info("No daily spending data available.")
        except Exception as e:
            st.error(f"Error creating histogram: {str(e)}")
    
    with col2:
        # Cumulative spending
        try:
            if 'daily_totals' in locals() and not daily_totals.empty:
                daily_totals["cumulative"] = daily_totals["total"].cumsum()
                fig2 = px.area(
                    daily_totals, 
                    x="expense_date", 
                    y="cumulative",
                    title="Cumulative Spending Over Time",
                    labels={"cumulative": "Total Spend (₵)"}
                )
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info("No data for cumulative spending chart.")
        except Exception as e:
            st.error(f"Error creating area chart: {str(e)}")
    
    # Weekly breakdown
    st.subheader("📆 Weekly Pattern Analysis")
    
    try:
        # Day of week analysis
        if not filtered.empty:
            dow_spending = filtered.groupby(["day_name", "day_of_week"])["total"].agg(["sum", "count", "mean"]).reset_index()
            dow_spending = dow_spending.sort_values("day_of_week")
            
            # Create day order mapping
            day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            dow_spending['day_name'] = pd.Categorical(dow_spending['day_name'], categories=day_order, ordered=True)
            dow_spending = dow_spending.sort_values('day_name')
            
            fig3 = make_subplots(
                rows=1, cols=2,
                subplot_titles=("Average Spend by Day", "Transaction Count by Day"),
                specs=[[{"type": "bar"}, {"type": "bar"}]]
            )
            
            fig3.add_trace(
                go.Bar(x=dow_spending["day_name"], y=dow_spending["mean"], name="Avg Spend", marker_color='#2E91E5'),
                row=1, col=1
            )
            
            fig3.add_trace(
                go.Bar(x=dow_spending["day_name"], y=dow_spending["count"], name="Transaction Count", marker_color='#E15A97'),
                row=1, col=2
            )
            
            fig3.update_layout(height=400, showlegend=False)
            st.plotly_chart(fig3, use_container_width=True)
        else:
            st.info("No data for weekly pattern analysis.")
    except Exception as e:
        st.error(f"Error creating weekly pattern chart: {str(e)}")

with tab2:
    # Category Analysis
    st.subheader("📊 Category Breakdown")
    
    try:
        category_cols = ["transport", "food", "data", "other"]
        existing_cats = [col for col in category_cols if col in filtered.columns]
        
        if existing_cats:
            cat_totals = filtered[existing_cats].sum().reset_index()
            cat_totals.columns = ["Category", "Amount"]
            cat_totals["Percentage"] = (cat_totals["Amount"] / cat_totals["Amount"].sum() * 100).round(1)
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Treemap for category visualization
                if not cat_totals.empty:
                    fig4 = px.treemap(
                        cat_totals, 
                        path=['Category'], 
                        values='Amount',
                        title="Category Spending (Treemap)",
                        color='Amount',
                        color_continuous_scale='Blues'
                    )
                    fig4.update_layout(margin=dict(t=50, l=25, r=25, b=25))
                    st.plotly_chart(fig4, use_container_width=True)
                else:
                    st.info("No category data available for treemap.")
            
            with col2:
                # Donut chart
                if not cat_totals.empty:
                    fig5 = px.pie(
                        cat_totals, 
                        values='Amount', 
                        names='Category',
                        hole=0.6,
                        title="Spending Distribution"
                    )
                    fig5.update_traces(textposition='inside', textinfo='percent+label')
                    st.plotly_chart(fig5, use_container_width=True)
                else:
                    st.info("No category data available for pie chart.")
            
            # Category trends over time
            st.subheader("📈 Category Trends")
            
            # Resample to weekly for smoother trends
            try:
                weekly_cats = filtered.set_index("expense_date").resample("W")[existing_cats].sum().reset_index()
                weekly_cats_melted = weekly_cats.melt(
                    id_vars=["expense_date"], 
                    value_vars=existing_cats,
                    var_name="Category", 
                    value_name="Amount"
                )
                
                if not weekly_cats_melted.empty:
                    fig6 = px.line(
                        weekly_cats_melted, 
                        x="expense_date", 
                        y="Amount", 
                        color="Category",
                        title="Weekly Category Spending Trends",
                        markers=True
                    )
                    fig6.update_layout(hovermode="x unified")
                    st.plotly_chart(fig6, use_container_width=True)
                else:
                    st.info("No data for category trends chart.")
            except Exception as e:
                st.error(f"Error creating category trends chart: {str(e)}")
        else:
            st.info("No category columns found in the data.")
    except Exception as e:
        st.error(f"Error in category analysis: {str(e)}")

with tab3:
    # Timeline Analysis
    st.subheader("⏳ Spending Timeline")
    
    try:
        # Interactive timeline with range selector
        if not filtered.empty:
            daily_agg = filtered.groupby("expense_date").agg({
                "total": "sum"
            }).reset_index()
            
            # Add category columns if they exist
            category_cols = ["transport", "food", "data", "other"]
            for col in category_cols:
                if col in filtered.columns:
                    daily_agg[col] = filtered.groupby("expense_date")[col].sum().values
            
            fig7 = go.Figure()
            
            # Add main total line
            fig7.add_trace(go.Scatter(
                x=daily_agg["expense_date"],
                y=daily_agg["total"],
                name="Total Spend",
                line=dict(color='#1F77B4', width=2),
                fill='tozeroy',
                fillcolor='rgba(31, 119, 180, 0.1)'
            ))
            
            # Add 7-day moving average
            daily_agg["moving_avg"] = daily_agg["total"].rolling(window=7, min_periods=1).mean()
            fig7.add_trace(go.Scatter(
                x=daily_agg["expense_date"],
                y=daily_agg["moving_avg"],
                name="7-Day Moving Avg",
                line=dict(color='#FF7F0E', width=2, dash='dash')
            ))
            
            fig7.update_layout(
                title="Daily Spending with Trend Line",
                xaxis_title="Date",
                yaxis_title="Amount (₵)",
                hovermode="x unified",
                xaxis=dict(
                    rangeselector=dict(
                        buttons=list([
                            dict(count=7, label="1w", step="day", stepmode="backward"),
                            dict(count=1, label="1m", step="month", stepmode="backward"),
                            dict(count=3, label="3m", step="month", stepmode="backward"),
                            dict(step="all")
                        ])
                    ),
                    rangeslider=dict(visible=True),
                    type="date"
                )
            )
            
            st.plotly_chart(fig7, use_container_width=True)
        else:
            st.info("No data available for timeline analysis.")
    except Exception as e:
        st.error(f"Error creating timeline chart: {str(e)}")
    
    # Calendar heatmap
    st.subheader("📅 Spending Calendar")
    
    try:
        if not filtered.empty:
            # Prepare data for heatmap
            heatmap_data = filtered.copy()
            heatmap_data["date"] = heatmap_data["expense_date"].dt.date
            heatmap_data["year"] = heatmap_data["expense_date"].dt.year
            heatmap_data["month"] = heatmap_data["expense_date"].dt.month
            heatmap_data["day"] = heatmap_data["expense_date"].dt.day
            heatmap_data["weekday"] = heatmap_data["expense_date"].dt.weekday
            heatmap_data["week"] = heatmap_data["expense_date"].dt.isocalendar().week
            
            # Create pivot table for heatmap
            pivot_data = heatmap_data.pivot_table(
                values='total',
                index='weekday',
                columns='week',
                aggfunc='sum',
                fill_value=0
            )
            
            # Sort weekdays properly
            pivot_data = pivot_data.reindex([0, 1, 2, 3, 4, 5, 6])
            
            fig8 = px.imshow(
                pivot_data,
                labels=dict(x="Week Number", y="Day of Week", color="Total Spend"),
                title="Weekly Spending Heatmap",
                color_continuous_scale="Viridis"
            )
            
            fig8.update_xaxes(title_text="Week Number")
            fig8.update_yaxes(
                title_text="Day of Week",
                ticktext=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
                tickvals=[0, 1, 2, 3, 4, 5, 6]
            )
            
            st.plotly_chart(fig8, use_container_width=True)
        else:
            st.info("No data available for calendar heatmap.")
    except Exception as e:
        st.error(f"Error creating heatmap: {str(e)}")

with tab4:
    # Anomaly Detection
    st.subheader("🔍 Spending Anomalies")
    
    try:
        if not filtered.empty:
            # Prepare data for anomaly detection
            anomaly_data = filtered.groupby("expense_date")["total"].sum().reset_index()
            anomaly_data.set_index("expense_date", inplace=True)
            anomaly_data = anomaly_data.resample("D").sum().fillna(0)
            
            # Calculate z-scores
            mean = anomaly_data["total"].mean()
            std = anomaly_data["total"].std() if anomaly_data["total"].std() > 0 else 1
            anomaly_data["z_score"] = (anomaly_data["total"] - mean) / std
            
            # Detect anomalies
            threshold = anomaly_sensitivity / 5  # Scale sensitivity to appropriate threshold
            anomaly_data["is_anomaly"] = abs(anomaly_data["z_score"]) > threshold
            
            # Visualize anomalies
            fig9 = go.Figure()
            
            # Normal points
            normal_points = anomaly_data[~anomaly_data["is_anomaly"]]
            if not normal_points.empty:
                fig9.add_trace(go.Scatter(
                    x=normal_points.index,
                    y=normal_points["total"],
                    mode='markers',
                    name='Normal',
                    marker=dict(color='blue', size=6, opacity=0.6)
                ))
            
            # Anomaly points
            anomaly_points = anomaly_data[anomaly_data["is_anomaly"]]
            if not anomaly_points.empty:
                fig9.add_trace(go.Scatter(
                    x=anomaly_points.index,
                    y=anomaly_points["total"],
                    mode='markers',
                    name='Anomaly',
                    marker=dict(color='red', size=10, symbol='diamond')
                ))
            
            fig9.update_layout(
                title="Detected Spending Anomalies",
                xaxis_title="Date",
                yaxis_title="Amount (₵)",
                showlegend=True
            )
            
            st.plotly_chart(fig9, use_container_width=True)
            
            # Show anomaly details
            if not anomaly_points.empty:
                st.subheader("📋 Anomaly Details")
                
                anomaly_details = anomaly_points.reset_index()
                anomaly_details = anomaly_details[["expense_date", "total", "z_score"]]
                anomaly_details["z_score"] = anomaly_details["z_score"].round(2)
                anomaly_details.columns = ["Date", "Amount (₵)", "Z-Score"]
                
                # Highlight severity
                def highlight_severity(score):
                    abs_score = abs(score)
                    if abs_score > 3:
                        return "🚨 High"
                    elif abs_score > 2:
                        return "⚠️ Medium"
                    else:
                        return "ℹ️ Low"
                
                anomaly_details["Severity"] = anomaly_details["Z-Score"].apply(highlight_severity)
                
                st.dataframe(
                    anomaly_details.sort_values("Z-Score", key=abs, ascending=False),
                    use_container_width=True
                )
                
                # Anomaly insights
                st.subheader("💡 Anomaly Insights")
                
                # Identify potential causes
                for idx, row in anomaly_points.iterrows():
                    day_data = filtered[filtered["expense_date"].dt.date == idx.date()]
                    if not day_data.empty:
                        with st.expander(f"Anomaly on {idx.date()}: ₵{row['total']:.2f}"):
                            # Show top categories
                            category_cols = ["transport", "food", "data", "other"]
                            existing_cats = [col for col in category_cols if col in day_data.columns]
                            if existing_cats:
                                top_categories = day_data[existing_cats].sum().sort_values(ascending=False).head(2)
                                if not top_categories.empty:
                                    top_categories_str = ", ".join([f"{cat}: ₵{amt:.2f}" for cat, amt in top_categories.items()])
                                    st.markdown(f"**Top Categories:** {top_categories_str}")
                            
                            # Show descriptions if available
                            if "description" in day_data.columns and not day_data["description"].isna().all():
                                st.markdown("**Transaction Descriptions:**")
                                for desc in day_data["description"].dropna().unique()[:3]:
                                    st.markdown(f"- {desc}")
            else:
                st.success("✅ No significant anomalies detected in your spending patterns!")
        else:
            st.info("No data available for anomaly detection.")
    except Exception as e:
        st.error(f"Error in anomaly detection: {str(e)}")

with tab5:
    # Data Export
    st.subheader("📤 Export Data")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📄 Raw Data Export")
        
        # CSV Export
        try:
            csv_data = filtered.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv_data,
                file_name=f"spending_data_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        except Exception as e:
            st.error(f"Error generating CSV: {str(e)}")
        
        # Excel Export with multiple sheets
        try:
            # Prepare data for Excel export
            excel_sheets = {
                "Transactions": filtered,
                "Daily_Summary": filtered.groupby("expense_date")["total"].sum().reset_index()
            }
            
            # Add category summary if available
            category_cols = ["transport", "food", "data", "other"]
            existing_cats = [col for col in category_cols if col in filtered.columns]
            if existing_cats:
                cat_totals = filtered[existing_cats].sum().reset_index()
                cat_totals.columns = ["Category", "Amount"]
                excel_sheets["Category_Summary"] = cat_totals
            
            # Add weekly analysis if available
            if not weekly_expenses.empty:
                excel_sheets["Weekly_Analysis"] = weekly_expenses
            
            excel_data = to_excel_bytes(excel_sheets)
            
            st.download_button(
                label="📊 Download Excel Report",
                data=excel_data,
                file_name=f"spending_report_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        except Exception as e:
            st.error(f"Error generating Excel: {str(e)}")
    
    with col2:
        st.markdown("### 📊 Summary Statistics")
        
        try:
            summary_stats = pd.DataFrame({
                "Metric": [
                    "Total Spending",
                    "Average Daily Spend",
                    "Number of Transactions",
                    "Days with Data",
                    "Highest Daily Spend",
                    "Weekly Budget Utilization"
                ],
                "Value": [
                    f"₵{total_spend:,.2f}",
                    f"₵{avg_daily_spend:,.2f}",
                    f"{transactions_count}",
                    f"{total_days}",
                    f"₵{max_daily_spend:,.2f}",
                    f"{burn_rate:.1f}%"
                ]
            })
            
            st.dataframe(summary_stats, use_container_width=True, hide_index=True)
        except Exception as e:
            st.error(f"Error generating summary statistics: {str(e)}")
    
    # PDF Export (if available)
    st.markdown("---")
    st.markdown("### 📋 Generate Report")
    
    if st.button("📄 Generate PDF Summary Report"):
        try:
            # Prepare data for PDF
            weekly_summary = {
                "Period": f"{start} to {end}",
                "Total Spend": f"₵{total_spend:,.2f}",
                "Avg Daily": f"₵{avg_daily_spend:,.2f}",
                "Budget Utilization": f"{burn_rate:.1f}%"
            }
            
            # Call your existing PDF export function
            pdf_file = export_pdf(weekly_summary, filtered)
            st.success("✅ PDF report generated successfully!")
            
            # Offer download
            with open(pdf_file, "rb") as f:
                pdf_data = f.read()
            
            st.download_button(
                label="📥 Download PDF Report",
                data=pdf_data,
                file_name=f"spending_summary_{datetime.now().strftime('%Y%m%d')}.pdf",
                mime="application/pdf"
            )
        except Exception as e:
            st.error(f"Error generating PDF: {str(e)}")

# ---------------------
# Bottom Information
# ---------------------
st.markdown("---")
footer_col1, footer_col2, footer_col3 = st.columns(3)
with footer_col1:
    st.caption(f"📅 Data from {start} to {end}")
with footer_col2:
    st.caption(f"📊 {transactions_count} transactions analyzed")
with footer_col3:
    st.caption("💰 Spending Analytics v2.0")

# Add auto-refresh option
if st.sidebar.checkbox("🔄 Auto-refresh data (every 5 min)", value=False):
    st.rerun()