# streamlit_glucose_dashboard.py

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# Configure page for full width
st.set_page_config(page_title="Blood Glucose Dashboard", layout="wide")

st.title("Blood Glucose Dashboard")

# File uploader for Excel files
uploaded_file = st.file_uploader("Upload your glucose data (.xls or .xlsx)", type=["xls", "xlsx"])
if uploaded_file:
    @st.cache_data
    def load_data(file):
        return pd.read_excel(file)

    # Load and prepare data
    df = load_data(uploaded_file)
    # Auto-detect datetime and glucose columns
    datetime_col = df.columns[0]
    glucose_col = df.columns[1]
    # Multiply glucose by 10
    df[glucose_col] = df[glucose_col] * 10

    # Convert, sort, and normalize
    df[datetime_col] = pd.to_datetime(df[datetime_col])
    df = df.sort_values(by=datetime_col).reset_index(drop=True)
    df['date_only'] = df[datetime_col].dt.normalize()
    unique_dates = df['date_only'].drop_duplicates().tolist()

    # Tabs: Single Day first, then Full Data
    tab_day, tab_full = st.tabs(["Single Day", "Full Data"])

    # SINGLE DAY TAB
    with tab_day:
        # Initialize session state for index with last date
        if 'day_idx' not in st.session_state:
            st.session_state.day_idx = len(unique_dates) - 1

        # Date selector above navigation
        selected_date = unique_dates[st.session_state.day_idx]
        input_date = st.date_input(
            "Select day",
            value=selected_date.date(),
            min_value=unique_dates[0].date(),
            max_value=unique_dates[-1].date(),
            key='single_day_input'
        )
        if input_date != selected_date.date():
            try:
                st.session_state.day_idx = unique_dates.index(pd.Timestamp(input_date))
            except ValueError:
                pass

        # Prev/Next buttons in two equal columns
        prev_col, next_col = st.columns([1,1])
        with prev_col:
            if st.button("< Before") and st.session_state.day_idx > 0:
                st.session_state.day_idx -= 1
        with next_col:
            if st.button("Next >") and st.session_state.day_idx < len(unique_dates) - 1:
                st.session_state.day_idx += 1

        # Update selected_date after input and buttons
        selected_date = unique_dates[st.session_state.day_idx]
                # Header with current date
        st.header(f"Daily Reports: {selected_date.date()}")

        # Slider to set Time-in-Range thresholds (mg/dL)
        tir_lower, tir_upper = st.slider(
            "Time-in-Range Thresholds (mg/dL)",
            min_value=20,
            max_value=140,
            value=(70, 100),
            key="tir_thresholds"
        )
                # Define thresholds (accounting for data multiplied by 10)
        # Since df[glucose] was scaled by 10, thresholds should also scale
        LOW = tir_lower
        HIGH = tir_upper

        # Data filtering for Daily Overall
        day_df = df[df['date_only'] == selected_date]
        prev_date = selected_date - pd.Timedelta(days=1)
        prev_df = df[df['date_only'] == prev_date]

        # Daily Overall stats card
        
        avg = day_df[glucose_col].mean()
        # time in range calculations
        mask_in = day_df[glucose_col].between(LOW, HIGH)
        pct_in = mask_in.mean() * 100 if not day_df.empty else 0
        dur_in_hours = pct_in / 100 * 24
        dur_in_mins = int((dur_in_hours - int(dur_in_hours)) * 60)
        dur_in_str = f"{int(dur_in_hours)}h{dur_in_mins}m"
        pct_tar = (day_df[glucose_col] > HIGH).mean() * 100 if not day_df.empty else 0
        dur_tar_hours = pct_tar / 100 * 24
        dur_tar_mins = int((dur_tar_hours - int(dur_tar_hours)) * 60)
        dur_tar_str = f"{int(dur_tar_hours)}h{dur_tar_mins}m"
        pct_tbr = (day_df[glucose_col] < LOW).mean() * 100 if not day_df.empty else 0
        dur_tbr_hours = pct_tbr / 100 * 24
        dur_tbr_mins = int((dur_tbr_hours - int(dur_tbr_hours)) * 60)
        dur_tbr_str = f"{int(dur_tbr_hours)}h{dur_tbr_mins}m"

        # layout similar to native app: two columns
        col1, col2, col3 = st.columns(3)
        st.write(
            """
            <style>
            [data-testid="stMetricDelta"] svg {
                display: none;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )
        # Time in Range metric
        col1.metric(
            "Time in Range", 
            f"{pct_in:.1f}%", 
            dur_in_str,
            delta_color="off"
        )
        # TAR/TBR metrics
        col2.metric(
            "TAR", 
            f"{pct_tar:.1f}%", 
            dur_tar_str,
            delta_color="off"
        )
        col3.metric(
            "TBR", 
            f"{pct_tbr:.1f}%", 
            dur_tbr_str,
            delta_color="off"
        )

        # Compute metrics
        avg = day_df[glucose_col].mean()
        mn = day_df[glucose_col].min()
        mx = day_df[glucose_col].max()
        prev_avg = prev_df[glucose_col].mean() if not prev_df.empty else None
        prev_min = prev_df[glucose_col].min() if not prev_df.empty else None
        prev_max = prev_df[glucose_col].max() if not prev_df.empty else None

        st.markdown("---")

        # Display metrics
        st.write(
            """
            <style>
            [data-testid="stMetricDelta"] svg {
                display:;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )
        m1, m2, m3 = st.columns(3)
        m1.metric("Avg Glucose", f"{avg:.1f}", delta=f"{avg - prev_avg:.2f}" if prev_avg is not None else None)
        m2.metric("Min Glucose", f"{mn}", delta=f"{mn - prev_min:.2f}" if prev_min is not None else None)
        m3.metric("Max Glucose", f"{mx}", delta=f"{mx - prev_max:.2f}" if prev_max is not None else None)

        st.markdown("---")


        # Determine y-axis max for single day
        max_val_day = max(100, day_df[glucose_col].max()) if not day_df.empty else 100

        st.subheader(f"Daily Trend: {selected_date.date()}")


        # Checkbox options: average overlay and range area
        col_opt1, col_opt2 = st.columns(2)
        show_avg = col_opt1.checkbox("Overlay 7-day average day")
        show_range = col_opt2.checkbox("Show Time-in-Range area")

        # Plotly figure for single day
        fig_day = go.Figure()
        # Add Time-in-Range area and borders if enabled
        if show_range:
            fig_day.add_shape(
                type="rect",
                xref="paper", x0=0, x1=1,
                yref="y", y0=LOW, y1=HIGH,
                line=dict(color="red", width=1, dash="dash"),
                fillcolor="rgba(255,0,0,0.1)",
                layer="below"
            )
        # Glucose trace
        fig_day.add_trace(go.Scatter(
            x=day_df[datetime_col],
            y=day_df[glucose_col],
            mode='lines',
            line=dict(color='teal'),
            fill='tozeroy',
            fillcolor='rgba(0,128,128,0.2)'
        ))
        if show_avg:
            last_week = df[(df['date_only'] > selected_date - pd.Timedelta(days=7)) & (df['date_only'] <= selected_date)]
            last_week['time_only'] = last_week[datetime_col].dt.time
            avg_series = last_week.groupby('time_only')[glucose_col].mean().reset_index()
            avg_series['datetime'] = avg_series['time_only'].apply(lambda t: pd.Timestamp.combine(selected_date, t))
            fig_day.add_trace(go.Scatter(
                x=avg_series['datetime'],
                y=avg_series[glucose_col],
                mode='lines',
                line=dict(color='orange'),
                opacity=0.7
            ))
        # Vertical delimiter
        fig_day.add_vline(
            x=selected_date,
            line_width=1,
            line_color='lightgray',
            opacity=0.5,
            layer='below'
        )
        fig_day.update_layout(
            autosize=True,
            margin=dict(l=0, r=0, t=30, b=0),
            showlegend=False,
            dragmode='pan',
            xaxis=dict(
                title='Time', type='date',
                range=[selected_date, selected_date + pd.Timedelta(days=1)],
                rangeslider=dict(visible=True)
            ),
            yaxis=dict(range=[20, max_val_day]),
            hovermode='x unified'
        )
        st.plotly_chart(
            fig_day,
            use_container_width=True,
            config={'responsive': True, 'scrollZoom': False}
        )

    # FULL DATA TAB
    with tab_full:
        st.header("Full Timeline")
        min_date = df['date_only'].min().date()
        max_date = df['date_only'].max().date()
        start_date = st.date_input("Start date", min_value=min_date, max_value=max_date, value=min_date, key='full_start')
        end_date = st.date_input("End date", min_value=min_date, max_value=max_date, value=max_date, key='full_end')
        df_full = df[(df[datetime_col] >= pd.Timestamp(start_date)) & (df[datetime_col] <= pd.Timestamp(end_date))]
        dates_full = df_full['date_only'].drop_duplicates()
        max_val_full = max(100, df_full[glucose_col].max()) if not df_full.empty else 100
        fig_full = go.Figure()
        fig_full.add_trace(go.Scatter(
            x=df_full[datetime_col],
            y=df_full[glucose_col],
            mode='lines',
            line=dict(color='#007bff'),
            fill='tozeroy',
            fillcolor='rgba(0,123,255,0.2)'
        ))
        for d in dates_full:
            fig_full.add_vline(x=d, line_width=1, line_color='lightgray', opacity=0.5, layer='below')
        fig_full.update_layout(
            autosize=True,
            margin=dict(l=0, r=0, t=30, b=0),
            showlegend=False,
            dragmode='pan',
            xaxis=dict(title='Time', type='date', rangeslider=dict(visible=True)),
            yaxis=dict(range=[2, max_val_full]),
            hovermode='x unified'
        )
        st.plotly_chart(
            fig_full,
            use_container_width=True,
            config={'responsive': True, 'scrollZoom': False}
        )
else:
    st.info("Please upload an .xls or .xlsx file to get started.")
