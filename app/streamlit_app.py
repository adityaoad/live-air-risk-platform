import os

import pandas as pd
import plotly.express as px
import psycopg2
import streamlit as st
from dotenv import load_dotenv


load_dotenv(".env")


def get_database_url():
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        database_url = st.secrets.get("DATABASE_URL", None)

    if not database_url:
        raise ValueError("DATABASE_URL missing from environment or Streamlit secrets")

    return database_url


def get_connection():
    return psycopg2.connect(get_database_url())


def to_mountain_time(series):
    return (
        pd.to_datetime(series, utc=True)
        .dt.tz_convert("America/Denver")
        .dt.strftime("%Y-%m-%d %H:%M MT")
    )


@st.cache_data(ttl=300)
def load_latest_risk():
    query = """
        SELECT
            city_name,
            state_region,
            country,
            observation_time,
            us_aqi,
            pm2_5,
            pm10,
            ozone,
            apparent_temperature_c,
            apparent_temperature_f,
            wind_speed_10m,
            uv_index,
            environmental_risk_score,
            risk_label,
            aqi_category,
            latest_ingested_at
        FROM analytics.mart_latest_city_risk
        ORDER BY environmental_risk_score DESC NULLS LAST;
    """

    with get_connection() as conn:
        return pd.read_sql(query, conn)


@st.cache_data(ttl=300)
def load_hourly_risk():
    query = """
        SELECT
            city_name,
            state_region,
            country,
            observation_time,
            us_aqi,
            pm2_5,
            pm10,
            ozone,
            apparent_temperature_c,
            apparent_temperature_f,
            wind_speed_10m,
            uv_index,
            environmental_risk_score,
            risk_label,
            aqi_category
        FROM analytics.mart_city_hourly_risk
        WHERE observation_time IS NOT NULL
        ORDER BY observation_time;
    """

    with get_connection() as conn:
        return pd.read_sql(query, conn)


@st.cache_data(ttl=300)
def load_forecast():
    query = """
        SELECT
            city_name,
            state_region,
            country,
            observation_time,
            us_aqi,
            forecast_aqi_baseline,
            forecast_absolute_error,
            forecast_aqi_category,
            pm2_5,
            pm10,
            ozone,
            environmental_risk_score,
            risk_label
        FROM analytics.mart_aqi_forecast_baseline
        WHERE forecast_aqi_baseline IS NOT NULL
        ORDER BY observation_time;
    """

    with get_connection() as conn:
        return pd.read_sql(query, conn)


@st.cache_data(ttl=300)
def load_anomalies():
    query = """
        SELECT
            city_name,
            state_region,
            country,
            observation_time,
            us_aqi,
            pm2_5,
            pm10,
            ozone,
            environmental_risk_score,
            risk_label,
            rolling_avg_aqi_24h,
            rolling_std_aqi_24h,
            aqi_z_score,
            is_aqi_anomaly
        FROM analytics.mart_aqi_anomalies
        WHERE aqi_z_score IS NOT NULL
        ORDER BY observation_time DESC;
    """

    with get_connection() as conn:
        return pd.read_sql(query, conn)


@st.cache_data(ttl=300)
def load_data_quality():
    query = """
        SELECT
            table_name,
            row_count,
            earliest_observation_time,
            latest_observation_time,
            latest_ingested_at,
            missing_observation_time_count
        FROM analytics.mart_data_quality_summary
        ORDER BY table_name;
    """

    with get_connection() as conn:
        return pd.read_sql(query, conn)


st.set_page_config(
    page_title="Live Air Quality & Weather Risk Platform",
    layout="wide",
)

st.title("Live Air Quality & Weather Risk Platform")
st.caption("MVP dashboard using live Open-Meteo weather and air-quality data.")

latest_df = load_latest_risk()
hourly_df = load_hourly_risk()
forecast_df = load_forecast()
anomaly_df = load_anomalies()
dq_df = load_data_quality()

if latest_df.empty:
    st.error("No latest risk data found. Run dbt models first.")
    st.stop()

latest_df["observation_time"] = pd.to_datetime(latest_df["observation_time"])
latest_df["latest_ingested_at"] = pd.to_datetime(latest_df["latest_ingested_at"])
hourly_df["observation_time"] = pd.to_datetime(hourly_df["observation_time"])

if not forecast_df.empty:
    forecast_df["observation_time"] = pd.to_datetime(forecast_df["observation_time"])

if not anomaly_df.empty:
    anomaly_df["observation_time"] = pd.to_datetime(anomaly_df["observation_time"])

if not dq_df.empty:
    dq_df["earliest_observation_time"] = pd.to_datetime(dq_df["earliest_observation_time"])
    dq_df["latest_observation_time"] = pd.to_datetime(dq_df["latest_observation_time"])
    dq_df["latest_ingested_at"] = pd.to_datetime(dq_df["latest_ingested_at"])

col1, col2, col3, col4 = st.columns(4)

col1.metric("Cities Tracked", latest_df["city_name"].nunique())
col2.metric("Highest AQI", int(latest_df["us_aqi"].max()))
col3.metric("Highest Risk Score", round(latest_df["environmental_risk_score"].max(), 1))
latest_refresh_mt = (
    pd.to_datetime(latest_df["latest_ingested_at"].max(), utc=True)
    .tz_convert("America/Denver")
    .strftime("%Y-%m-%d %H:%M MT")
)

col4.metric("Latest Refresh", latest_refresh_mt)

tab_overview, tab_city, tab_anomalies, tab_forecast, tab_quality = st.tabs(["Overview", "City Explorer", "Anomalies", "Forecast", "Data Quality"])

with tab_overview:
    st.subheader("Latest City Risk Ranking")

    ranking_cols = [
        "city_name",
        "state_region",
        "country",
        "observation_time",
        "us_aqi",
        "aqi_category",
        "environmental_risk_score",
        "risk_label",
        "pm2_5",
        "pm10",
        "ozone",
        "apparent_temperature_c",
        "apparent_temperature_f",
        "wind_speed_10m",
        "uv_index",
    ]

    ranking_df = latest_df[ranking_cols].copy()
    ranking_df["observation_time"] = to_mountain_time(ranking_df["observation_time"])
    ranking_df = ranking_df.rename(
        columns={
            "apparent_temperature_c": "Apparent Temperature (°C)",
            "apparent_temperature_f": "Apparent Temperature (°F)",
        }
    )

    st.dataframe(
        ranking_df,
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Risk Score by City")

    risk_order = ["Low", "Moderate", "High", "Severe"]

    latest_df["risk_label"] = pd.Categorical(
        latest_df["risk_label"],
        categories=risk_order,
        ordered=True,
    )

    sort_choice = st.selectbox(
        "Sort city risk chart",
        ["Highest risk first", "Lowest risk first"],
        key="risk_chart_sort",
    )

    sort_ascending = sort_choice == "Lowest risk first"

    risk_chart_df = latest_df.sort_values(
        "environmental_risk_score",
        ascending=sort_ascending,
    ).copy()

    fig_risk = px.bar(
        risk_chart_df,
        x="city_name",
        y="environmental_risk_score",
        color="risk_label",
        color_discrete_map={
            "Low": "#2E8B57",
            "Moderate": "#F4B400",
            "High": "#F57C00",
            "Severe": "#D32F2F",
        },
        category_orders={
            "city_name": risk_chart_df["city_name"].tolist(),
            "risk_label": risk_order,
        },
        hover_data={
            "city_name": False,
            "environmental_risk_score": ":.1f",
            "risk_label": True,
            "us_aqi": ":.0f",
            "aqi_category": True,
            "pm2_5": ":.1f",
            "ozone": ":.1f",
        },
        title="Latest Environmental Risk Score",
    )

    fig_risk.add_hline(
        y=25,
        line_dash="dot",
        annotation_text="Moderate threshold",
        annotation_position="top left",
    )

    fig_risk.add_hline(
        y=50,
        line_dash="dot",
        annotation_text="High threshold",
        annotation_position="top left",
    )

    fig_risk.add_hline(
        y=75,
        line_dash="dot",
        annotation_text="Severe threshold",
        annotation_position="top left",
    )

    fig_risk.update_layout(
        legend_title_text="Risk Label",
        xaxis_title="City",
        yaxis_title="Environmental Risk Score",
        yaxis_range=[0, 100],
    )

    st.plotly_chart(fig_risk, use_container_width=True)

with tab_city:
    st.subheader("City Explorer")

    city = st.selectbox(
        "Select city",
        sorted(hourly_df["city_name"].dropna().unique()),
    )

    city_df = hourly_df[hourly_df["city_name"] == city].copy()

    fig_aqi = px.line(
        city_df,
        x="observation_time",
        y="us_aqi",
        title=f"{city} AQI Trend",
        markers=True,
    )

    st.plotly_chart(fig_aqi, use_container_width=True)

    fig_pollutants = px.line(
        city_df,
        x="observation_time",
        y=["pm2_5", "pm10", "ozone"],
        title=f"{city} Pollutant Trends",
    )

    st.plotly_chart(fig_pollutants, use_container_width=True)

    fig_weather = px.line(
        city_df,
        x="observation_time",
        y=["apparent_temperature_c",
        "apparent_temperature_f", "wind_speed_10m", "uv_index"],
        title=f"{city} Weather Context: Apparent Temperature (°C/°F), Wind, UV",
    )

    st.plotly_chart(fig_weather, use_container_width=True)


with tab_anomalies:
    st.subheader("AQI Anomalies")

    anomaly_count = int(anomaly_df["is_aqi_anomaly"].sum()) if not anomaly_df.empty else 0
    scored_count = len(anomaly_df)

    col_a, col_b = st.columns(2)
    col_a.metric("Scored Rows", scored_count)
    col_b.metric("Anomaly Rows", anomaly_count)

    anomaly_display_df = anomaly_df[anomaly_df["is_aqi_anomaly"] == True].copy()

    if anomaly_display_df.empty:
        st.info("No AQI anomalies detected with the current threshold.")
    else:
        anomaly_display_df["observation_time"] = to_mountain_time(anomaly_display_df["observation_time"])

        st.dataframe(
            anomaly_display_df[
                [
                    "city_name",
                    "state_region",
                    "country",
                    "observation_time",
                    "us_aqi",
                    "rolling_avg_aqi_24h",
                    "aqi_z_score",
                    "environmental_risk_score",
                    "risk_label",
                    "pm2_5",
                    "pm10",
                    "ozone",
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )

        fig_anomalies = px.scatter(
            anomaly_df,
            x="observation_time",
            y="us_aqi",
            color="is_aqi_anomaly",
            hover_data=["city_name", "aqi_z_score", "environmental_risk_score"],
            title="AQI Anomaly Detection",
        )

        st.plotly_chart(fig_anomalies, use_container_width=True)



with tab_forecast:
    st.subheader("AQI Forecast Baseline")

    if forecast_df.empty:
        st.info("No forecast baseline data available yet.")
    else:
        avg_error = round(forecast_df["forecast_absolute_error"].mean(), 2)
        forecasted_rows = len(forecast_df)

        col_f1, col_f2 = st.columns(2)
        col_f1.metric("Forecasted Rows", forecasted_rows)
        col_f2.metric("Avg Absolute Error", avg_error)

        forecast_city = st.selectbox(
            "Select forecast city",
            sorted(forecast_df["city_name"].dropna().unique()),
            key="forecast_city_select",
        )

        forecast_city_df = forecast_df[forecast_df["city_name"] == forecast_city].copy()

        fig_forecast = px.line(
            forecast_city_df,
            x="observation_time",
            y=["us_aqi", "forecast_aqi_baseline"],
            title=f"{forecast_city} AQI: Actual vs Baseline Forecast",
            markers=True,
        )

        st.plotly_chart(fig_forecast, use_container_width=True)

        forecast_display_df = forecast_city_df.sort_values("observation_time", ascending=False).copy()
        forecast_display_df["observation_time"] = to_mountain_time(forecast_display_df["observation_time"])

        st.dataframe(
            forecast_display_df[
                [
                    "city_name",
                    "state_region",
                    "country",
                    "observation_time",
                    "us_aqi",
                    "forecast_aqi_baseline",
                    "forecast_absolute_error",
                    "forecast_aqi_category",
                    "environmental_risk_score",
                    "risk_label",
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )


with tab_quality:
    st.subheader("Data Quality Summary")

    dq_display_df = dq_df.copy()

    for col in [
        "earliest_observation_time",
        "latest_observation_time",
        "latest_ingested_at",
    ]:
        dq_display_df[col] = to_mountain_time(dq_display_df[col])

    st.dataframe(
        dq_display_df,
        use_container_width=True,
        hide_index=True,
    )

    if not dq_df.empty:
        fig_rows = px.bar(
            dq_df,
            x="table_name",
            y="row_count",
            title="Row Counts by Table",
        )

        st.plotly_chart(fig_rows, use_container_width=True)

st.caption(
    "Risk score is an analytical indicator, not official health or medical guidance."
)
