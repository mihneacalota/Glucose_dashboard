# streamlit_glucose_dashboard.py

import streamlit as st
import pandas as pd
import altair as alt

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

    # Select time range
    st.header("Select Time Range")
    df[datetime_col] = pd.to_datetime(df[datetime_col])
    min_date = df[datetime_col].min().date()
    max_date = df[datetime_col].max().date()
    start_date = st.date_input("Start date", min_value=min_date, max_value=max_date, value=min_date)
    end_date = st.date_input("End date", min_value=min_date, max_value=max_date, value=max_date)

    # Filter data and sort
    df = df[(df[datetime_col] >= pd.Timestamp(start_date)) & (df[datetime_col] <= pd.Timestamp(end_date))]
    df = df.sort_values(by=datetime_col).reset_index(drop=True)

    # Compute rolling average (1-hour window)
    df = df.set_index(datetime_col)
    df['rolling_avg'] = df[glucose_col].rolling('1h').mean()
    df = df.reset_index()

    # Prepare daily split positions for vertical rules
    df['date_only'] = df[datetime_col].dt.normalize()
    unique_dates = df['date_only'].drop_duplicates().to_frame(name='midnight')

    # Base encoding with daily tick labels
    base = alt.Chart(df).encode(
        x=alt.X(f"{datetime_col}:T",
                title="Time",
                axis=alt.Axis(format="%a %d %b", tickCount='day', labelAngle=0, labelPadding=10)),
        y=alt.Y(f"{glucose_col}:Q", title="Glucose")
    )

    # Raw glucose line
    line = base.mark_line().encode(
        tooltip=[alt.Tooltip(f"{datetime_col}:T", title="Time"),
                 alt.Tooltip(f"{glucose_col}:Q", title="Glucose")]
    )

    # Rolling average line (solid green)
    avg_line = base.mark_line(color='orange').encode(
        y='rolling_avg:Q',
        tooltip=[alt.Tooltip(f"{datetime_col}:T", title="Time"),
                 alt.Tooltip("rolling_avg:Q", format=".1f", title="1h Avg")]
    )

    # Daily vertical rules
    rules = alt.Chart(unique_dates).mark_rule(color='lightgray', strokeWidth=1).encode(
        x='midnight:T'
    )

    # Layer chart components
    chart = alt.layer(rules, line, avg_line).properties(
        width='container',
        height=400
    ).interactive()

    st.subheader("Glucose Levels Over Time")
    st.altair_chart(chart, use_container_width=True)
else:
    st.info("Please upload an .xls or .xlsx file to get started.")
