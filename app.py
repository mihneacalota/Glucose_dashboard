# streamlit_glucose_dashboard.py

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# Configure page
st.set_page_config(page_title="Blood Glucose Dashboard", layout="wide")

st.title("Blood Glucose Dashboard")

# File uploader for Excel files
uploaded_file = st.file_uploader("Upload your glucose data (.xls or .xlsx)", type=["xls", "xlsx"])
if uploaded_file:
    @st.cache_data
    def load_data(file):
        return pd.read_excel(file)

    df = load_data(uploaded_file)
    st.write("### Data Preview", df.head())

    # Auto-detect datetime and glucose columns
    datetime_col = df.columns[0]
    glucose_col = df.columns[1]

    # Convert and sort
    df[datetime_col] = pd.to_datetime(df[datetime_col])
    df = df.sort_values(by=datetime_col).reset_index(drop=True)

    # Select time range filter
    st.header("Select Time Range")
    min_date = df[datetime_col].min().date()
    max_date = df[datetime_col].max().date()
    start_date = st.date_input("Start date", min_value=min_date, max_value=max_date, value=min_date)
    end_date = st.date_input("End date", min_value=min_date, max_value=max_date, value=max_date)
    df = df[(df[datetime_col] >= pd.Timestamp(start_date)) & (df[datetime_col] <= pd.Timestamp(end_date))]

    # Prepare day splits
    df['date_only'] = df[datetime_col].dt.normalize()
    unique_dates = df['date_only'].drop_duplicates()

    # Build Plotly figure
    fig = go.Figure()

    # Raw glucose line
    fig.add_trace(go.Scatter(
        x=df[datetime_col],
        y=df[glucose_col],
        mode='lines',
        name='Glucose',
        line=dict(color='teal')
    ))

    # Vertical day-split lines
    for d in unique_dates:
        fig.add_vline(
            x=d,
            line_width=1,
            line_color='lightgray',
            opacity=0.5,
            layer='below'
        )

    # Layout settings with fixed y-axis range
    fig.update_layout(
        xaxis_title='Time',
        yaxis_title='Glucose',
        yaxis=dict(range=[2, max(10, df[glucose_col].max())]),
        hovermode='x unified',
        margin=dict(l=40, r=20, t=30, b=40)
    )

    # Render chart
    st.subheader("Glucose Levels Over Time")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Please upload an .xls or .xlsx file to get started.")
