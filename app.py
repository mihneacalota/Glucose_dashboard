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

    df = load_data(uploaded_file)
    # st.write("### Data Preview", df.head())

    # Auto-detect datetime and glucose columns
    datetime_col = df.columns[0]
    glucose_col = df.columns[1]

    # Convert and prepare
    df[datetime_col] = pd.to_datetime(df[datetime_col])
    df = df.sort_values(by=datetime_col).reset_index(drop=True)
    df['date_only'] = df[datetime_col].dt.normalize()
    unique_dates = df['date_only'].drop_duplicates().tolist()

    # Tabs for full vs single-day view
    tab_full, tab_day = st.tabs(["Full Data", "Single Day"])

    # FULL DATA TAB
    with tab_full:
        st.header("Full Timeline")
        min_date = df['date_only'].min().date()
        max_date = df['date_only'].max().date()
        start_date = st.date_input(
            "Start date", min_value=min_date, max_value=max_date, value=min_date, key='full_start'
        )
        end_date = st.date_input(
            "End date", min_value=min_date, max_value=max_date, value=max_date, key='full_end'
        )
        df_full = df[
            (df[datetime_col] >= pd.Timestamp(start_date)) & 
            (df[datetime_col] <= pd.Timestamp(end_date))
        ]
        dates_full = df_full['date_only'].drop_duplicates()

        # Determine y-axis max (min 10)
        max_val_full = max(10, df_full[glucose_col].max()) if not df_full.empty else 10

        # Plotly figure
        fig_full = go.Figure()
        fig_full.add_trace(
            go.Scatter(
                x=df_full[datetime_col],
                y=df_full[glucose_col],
                mode='lines',
                # no legend name to hide legend
                line=dict(color='#007bff'),
                fill='tozeroy',
                fillcolor='rgba(0,123,255,0.2)'
            )
        )
        # Daily splits
        for d in dates_full:
            fig_full.add_vline(
                x=d,
                line_width=1,
                line_color='lightgray',
                opacity=0.5,
                layer='below'
            )
        # Layout: edge-to-edge, responsive, no y-axis title, hide legend
        fig_full.update_layout(
            autosize=True,
            margin=dict(l=0, r=0, t=30, b=0),
            showlegend=False,
            dragmode='pan',
            xaxis=dict(
                title='Time',
                type='date',
                rangeslider=dict(visible=True)
            ),
            yaxis=dict(
                range=[2, max_val_full]
            ),
            hovermode='x unified'
        )
        st.plotly_chart(
            fig_full, use_container_width=True, config={'responsive': True, 'scrollZoom': False}
        )

    # SINGLE DAY TAB
    with tab_day:
        st.header("Single Day View")
        # Initialize session state for index if missing
        if 'day_idx' not in st.session_state:
            st.session_state.day_idx = 0
        # Date input for selecting single day
        min_date = unique_dates[0].date()
        max_date = unique_dates[-1].date()
        # Current selected_date from session_state
        selected_date = unique_dates[st.session_state.day_idx]
        # Date input field
        input_date = st.date_input(
            "Select day",
            value=selected_date.date(),
            min_value=min_date,
            max_value=max_date,
            key='single_day_input'
        )
        # Update day_idx based on input_date
        if input_date != selected_date.date():
            # find closest matching date_only
            try:
                st.session_state.day_idx = unique_dates.index(pd.Timestamp(input_date))
            except ValueError:
                # if not exact match, ignore
                pass
        # Prev/Next buttons
        prev_col, next_col = st.columns([1, 1])
        if prev_col.button("Previous Day") and st.session_state.day_idx > 0:
            st.session_state.day_idx -= 1
        if next_col.button("Next Day") and st.session_state.day_idx < len(unique_dates) - 1:
            st.session_state.day_idx += 1
        # finalize selected_date
        selected_date = unique_dates[st.session_state.day_idx]

        # Overlay average-day option (last 7 days)
        show_avg = st.checkbox("Overlay 7-day average day")


        # Data filtering
        day_df = df[df['date_only'] == selected_date]
        prev_date = selected_date - pd.Timedelta(days=1)
        prev_df = df[df['date_only'] == prev_date]

        # Compute metrics
        avg = day_df[glucose_col].mean()
        mn = day_df[glucose_col].min()
        mx = day_df[glucose_col].max()
        prev_avg = prev_df[glucose_col].mean() if not prev_df.empty else None
        prev_min = prev_df[glucose_col].min() if not prev_df.empty else None
        prev_max = prev_df[glucose_col].max() if not prev_df.empty else None

        # Display selected date in normal format
        st.subheader(f"Selected date: {selected_date.strftime('%d-%m-%Y')}")


        # Display metrics
        m1, m2, m3 = st.columns(3)
        m1.metric(
            "Avg Glucose",
            f"{avg:.1f}",
            delta=f"{avg - prev_avg:.2f}" if prev_avg is not None else None
        )
        m2.metric(
            "Min Glucose",
            f"{mn}",
            delta=f"{mn - prev_min:.2f}" if prev_min is not None else None
        )
        m3.metric(
            "Max Glucose",
            f"{mx}",
            delta=f"{mx - prev_max:.2f}" if prev_max is not None else None
        )

        # Determine y-axis max for single day
        max_val_day = max(10, day_df[glucose_col].max()) if not day_df.empty else 10

        # Plotly figure for single day
        fig_day = go.Figure()
        fig_day.add_trace(
            go.Scatter(
                x=day_df[datetime_col],
                y=day_df[glucose_col],
                mode='lines',
                name='Glucose',
                line=dict(color='teal'),
                fill='tozeroy',
                fillcolor='rgba(0,128,128,0.2)'
            )
        )
        if show_avg:
            last_week = df[
                (df['date_only'] > selected_date - pd.Timedelta(days=7)) & 
                (df['date_only'] <= selected_date)
            ]
            last_week['time_only'] = last_week[datetime_col].dt.time
            avg_series = last_week.groupby('time_only')[glucose_col].mean().reset_index()
            avg_series['datetime'] = avg_series['time_only'].apply(
                lambda t: pd.Timestamp.combine(selected_date, t)
            )
            fig_day.add_trace(
                go.Scatter(
                    x=avg_series['datetime'],
                    y=avg_series[glucose_col],
                    mode='lines',
                    name='7-day average',
                    line=dict(color='orange'),
                    opacity=0.7
                )
            )
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
                title='Time',
                type='date',
                range=[selected_date, selected_date + pd.Timedelta(days=1)],
                rangeslider=dict(visible=True)
            ),
            yaxis=dict(
                range=[2, max_val_day]
            ),
            hovermode='x unified'
        )
        st.plotly_chart(
            fig_day, use_container_width=True, config={'responsive': True, 'scrollZoom': False}
        )
else:
    st.info("Please upload an .xls or .xlsx file to get started.")
