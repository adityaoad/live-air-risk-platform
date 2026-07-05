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

DISPLAY_LABELS = {
    "city_name": "City",
    "state_region": "State/Region",
    "country": "Country",
    "observation_time": "Observation Time",
    "us_aqi": "US AQI",
    "aqi_category": "AQI Category",
    "environmental_risk_score": "Environmental Risk Score",
    "risk_label": "Risk Level",
    "pm2_5": "PM2.5",
    "pm10": "PM10",
    "ozone": "Ozone",
    "apparent_temperature_c": "Apparent Temperature (°C)",
    "apparent_temperature_f": "Apparent Temperature (°F)",
    "wind_speed_10m": "Wind Speed at 10m",
    "uv_index": "UV Index",
    "latest_ingested_at": "Latest Ingested At",
    "rolling_avg_aqi_24h": "24-Hour Rolling Avg AQI",
    "rolling_std_aqi_24h": "24-Hour Rolling Std AQI",
    "aqi_z_score": "AQI Z-Score",
    "is_aqi_anomaly": "AQI Anomaly",
    "forecast_aqi_baseline": "Forecast AQI Baseline",
    "forecast_absolute_error": "Forecast Absolute Error",
    "forecast_aqi_category": "Forecast AQI Category",
    "table_name": "Table",
    "row_count": "Row Count",
    "earliest_observation_time": "Earliest Observation Time",
    "latest_observation_time": "Latest Observation Time",
    "missing_observation_time_count": "Missing Observation Time Count",
    "active_alert_count": "Active Alert Count",
    "highest_alert_severity": "Highest Alert Severity",
    "latest_alert_event": "Latest Alert Event",
    "latest_alert_headline": "Latest Alert Headline",
    "latest_alert_urgency": "Latest Alert Urgency",
    "latest_alert_certainty": "Latest Alert Certainty",
    "latest_alert_expires_at": "Latest Alert Expires At",
    "has_active_alert": "Has Active Alert",
}


def format_display_df(df):
    return df.rename(columns=DISPLAY_LABELS)


def clean_table_name(value):
    if pd.isna(value):
        return value

    return str(value).replace("_", " ").replace(".", " / ").title()


def clean_plotly_legend(fig):
    for trace in fig.data:
        if hasattr(trace, "name") and trace.name in DISPLAY_LABELS:
            trace.name = DISPLAY_LABELS[trace.name]
            trace.legendgroup = DISPLAY_LABELS[trace.legendgroup] if trace.legendgroup in DISPLAY_LABELS else trace.legendgroup

        if hasattr(trace, "hovertemplate") and trace.hovertemplate:
            for raw_name, display_name in DISPLAY_LABELS.items():
                trace.hovertemplate = trace.hovertemplate.replace(raw_name, display_name)

    return fig


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


@st.cache_data(ttl=300)
def load_weather_alerts():
    query = """
        SELECT
            city_name,
            state_region,
            country,
            active_alert_count,
            highest_alert_severity,
            latest_alert_event,
            latest_alert_headline,
            latest_alert_urgency,
            latest_alert_certainty,
            latest_alert_expires_at,
            has_active_alert
        FROM analytics.mart_city_weather_alerts
        ORDER BY
            active_alert_count DESC,
            CASE highest_alert_severity
                WHEN 'Extreme' THEN 5
                WHEN 'Severe' THEN 4
                WHEN 'Moderate' THEN 3
                WHEN 'Minor' THEN 2
                WHEN 'Unknown' THEN 1
                ELSE 0
            END DESC,
            city_name;
    """

    with get_connection() as conn:
        return pd.read_sql(query, conn)


st.set_page_config(
    page_title="Live Air Quality & Weather Risk Platform",
    layout="wide",
)

st.title("Live Air Quality & Weather Risk Platform")
st.caption("Live city-level environmental risk monitoring using weather, air-quality, and NOAA/NWS alert data.")

latest_df = load_latest_risk()
hourly_df = load_hourly_risk()
forecast_df = load_forecast()
anomaly_df = load_anomalies()
dq_df = load_data_quality()
alerts_df = load_weather_alerts()

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

if not alerts_df.empty:
    alerts_df["latest_alert_expires_at"] = pd.to_datetime(alerts_df["latest_alert_expires_at"])

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

tab_overview, tab_city, tab_anomalies, tab_forecast, tab_quality, tab_definitions = st.tabs(["Overview", "City Explorer", "Anomalies", "Forecast", "Data Quality", "Definitions"])

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
    st.dataframe(
        format_display_df(ranking_df),
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
        labels=DISPLAY_LABELS,
        title="Latest Environmental Risk Score by City",
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

    st.subheader("NOAA/NWS Weather Alerts")

    if alerts_df.empty:
        st.info("No NOAA/NWS weather alert data available yet.")
    else:
        active_alerts = int(alerts_df["active_alert_count"].sum())
        cities_with_alerts = int(alerts_df["has_active_alert"].sum())

        col_alert_1, col_alert_2 = st.columns(2)
        col_alert_1.metric("Active Weather Alerts", active_alerts)
        col_alert_2.metric("Cities With Active Alerts", cities_with_alerts)

        active_alerts_df = alerts_df[alerts_df["has_active_alert"] == True].copy()

        if active_alerts_df.empty:
            st.success("No active NOAA/NWS weather alerts for tracked US cities.")
        else:
            active_alerts_df["latest_alert_expires_at"] = to_mountain_time(
                active_alerts_df["latest_alert_expires_at"]
            )

            st.dataframe(
                format_display_df(
                    active_alerts_df[
                        [
                            "city_name",
                            "state_region",
                            "active_alert_count",
                            "highest_alert_severity",
                            "latest_alert_event",
                            "latest_alert_headline",
                            "latest_alert_expires_at",
                        ]
                    ]
                ),
                use_container_width=True,
                hide_index=True,
            )

with tab_city:
    st.subheader("City Explorer")

    city = st.selectbox(
        "Select city",
        sorted(hourly_df["city_name"].dropna().unique()),
    )

    city_df = hourly_df[hourly_df["city_name"] == city].copy()

    st.subheader("Weather Alert Context")

    if alerts_df.empty:
        st.info("No NOAA/NWS weather alert data available yet.")
    else:
        city_alert_df = alerts_df[alerts_df["city_name"] == city].copy()

        if city_alert_df.empty:
            st.info("No NOAA/NWS alert record found for this city.")
        else:
            city_alert = city_alert_df.iloc[0]

            col_city_alert_1, col_city_alert_2 = st.columns(2)
            col_city_alert_1.metric("Active Alerts", int(city_alert["active_alert_count"]))
            col_city_alert_2.metric("Highest Severity", city_alert["highest_alert_severity"])

            if bool(city_alert["has_active_alert"]):
                expires_value = city_alert["latest_alert_expires_at"]

                if pd.notna(expires_value):
                    expires_display = (
                        pd.to_datetime(expires_value, utc=True)
                        .tz_convert("America/Denver")
                        .strftime("%Y-%m-%d %H:%M MT")
                    )
                else:
                    expires_display = "Not provided"

                st.warning(
                    f"{city_alert['latest_alert_event']}: "
                    f"{city_alert['latest_alert_headline']} "
                    f"(expires {expires_display})"
                )
            else:
                st.success("No active NOAA/NWS weather alerts for this city.")

    fig_aqi = px.line(
        city_df,
        x="observation_time",
        y="us_aqi",
        labels=DISPLAY_LABELS,
        title=f"{city} US AQI Trend",
        markers=True,
    )

    fig_aqi = clean_plotly_legend(fig_aqi)
    st.plotly_chart(fig_aqi, use_container_width=True)

    fig_pollutants = px.line(
        city_df,
        x="observation_time",
        y=["pm2_5", "pm10", "ozone"],
        labels=DISPLAY_LABELS,
        title=f"{city} Pollutant Trends",
    )

    fig_pollutants = clean_plotly_legend(fig_pollutants)
    st.plotly_chart(fig_pollutants, use_container_width=True)

    fig_weather = px.line(
        city_df,
        x="observation_time",
        y=["apparent_temperature_f", "wind_speed_10m", "uv_index"],
        labels=DISPLAY_LABELS,
        title=f"{city} Weather Context: Apparent Temperature, Wind, and UV",
    )

    fig_weather = clean_plotly_legend(fig_weather)
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
            format_display_df(
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
                ]
            ),
            use_container_width=True,
            hide_index=True,
        )

        fig_anomalies = px.scatter(
            anomaly_df,
            x="observation_time",
            y="us_aqi",
            color="is_aqi_anomaly",
            hover_data=["city_name", "aqi_z_score", "environmental_risk_score"],
            labels=DISPLAY_LABELS,
            title="AQI Anomaly Detection",
        )

        fig_anomalies = clean_plotly_legend(fig_anomalies)
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
            labels=DISPLAY_LABELS,
            title=f"{forecast_city} AQI: Actual vs Baseline Forecast",
            markers=True,
        )

        fig_forecast = clean_plotly_legend(fig_forecast)
        st.plotly_chart(fig_forecast, use_container_width=True)

        forecast_display_df = forecast_city_df.sort_values("observation_time", ascending=False).copy()
        forecast_display_df["observation_time"] = to_mountain_time(forecast_display_df["observation_time"])

        st.dataframe(
            format_display_df(
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
                ]
            ),
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

    if "table_name" in dq_display_df.columns:
        dq_display_df["table_name"] = dq_display_df["table_name"].apply(clean_table_name)

    st.dataframe(
        format_display_df(dq_display_df),
        use_container_width=True,
        hide_index=True,
    )

    if not dq_df.empty:
        dq_chart_df = dq_df.copy()
        dq_chart_df["table_name"] = dq_chart_df["table_name"].apply(clean_table_name)

        fig_rows = px.bar(
            dq_chart_df,
            x="table_name",
            y="row_count",
            labels=DISPLAY_LABELS,
            title="Row Counts by Table",
        )

        st.plotly_chart(fig_rows, use_container_width=True)


with tab_definitions:
    st.subheader("Definitions")

    st.markdown(
        """
        This page explains the main environmental, weather, alert, and data-quality terms used across the dashboard.
        """
    )

    definitions = [
        {
            "Term": "US AQI",
            "Definition": "The United States Air Quality Index. Higher values indicate worse air quality and greater potential health concern.",
        },
        {
            "Term": "AQI Category",
            "Definition": "A descriptive air-quality band derived from AQI values, such as Good, Moderate, or Unhealthy.",
        },
        {
            "Term": "PM2.5",
            "Definition": "Fine particulate matter with diameter of 2.5 micrometers or smaller. It is one of the most important pollution indicators because it can penetrate deep into the lungs.",
        },
        {
            "Term": "PM10",
            "Definition": "Particulate matter with diameter of 10 micrometers or smaller. It includes dust, pollen, smoke, and other coarse particles.",
        },
        {
            "Term": "Ozone",
            "Definition": "Ground-level ozone concentration. High ozone can affect breathing and is often worse during sunny, hot conditions.",
        },
        {
            "Term": "Apparent Temperature",
            "Definition": "The temperature humans feel after accounting for weather factors such as humidity and wind. The dashboard displays this in Fahrenheit.",
        },
        {
            "Term": "Wind Speed at 10m",
            "Definition": "Wind speed measured or modeled at 10 meters above ground level, a standard height used in weather reporting.",
        },
        {
            "Term": "UV Index",
            "Definition": "A measure of ultraviolet radiation exposure risk from the sun. Higher values indicate stronger UV exposure.",
        },
        {
            "Term": "Environmental Risk Score",
            "Definition": "A 0-100 analytical score combining AQI and weather-related modifiers. It is designed for comparison across cities and time.",
        },
        {
            "Term": "Risk Level",
            "Definition": "A readable category derived from the Environmental Risk Score, such as Low, Moderate, High, or Severe.",
        },
        {
            "Term": "AQI Anomaly",
            "Definition": "A flag showing whether AQI is unusually high compared with recent rolling patterns for that city.",
        },
        {
            "Term": "AQI Z-Score",
            "Definition": "A standardized measure showing how far the current AQI is from the recent rolling average.",
        },
        {
            "Term": "24-Hour Rolling Avg AQI",
            "Definition": "The average AQI over the recent 24-hour window, used as a baseline for trend and anomaly detection.",
        },
        {
            "Term": "Forecast AQI Baseline",
            "Definition": "A simple short-term baseline estimate for AQI. It is not a deep forecasting model.",
        },
        {
            "Term": "Forecast Absolute Error",
            "Definition": "The absolute difference between the actual AQI and the forecast baseline.",
        },
        {
            "Term": "NOAA/NWS Weather Alert",
            "Definition": "An active weather alert issued through the National Oceanic and Atmospheric Administration / National Weather Service API.",
        },
        {
            "Term": "Alert Severity",
            "Definition": "The seriousness level of an active NOAA/NWS alert, such as Minor, Moderate, Severe, or Extreme.",
        },
        {
            "Term": "Alert Urgency",
            "Definition": "How quickly action may be needed for the alert, based on NOAA/NWS alert metadata.",
        },
        {
            "Term": "Alert Certainty",
            "Definition": "The confidence level that the alert event will occur, based on NOAA/NWS alert metadata.",
        },
        {
            "Term": "Data Freshness",
            "Definition": "A measure of how recently the data was ingested or updated in the warehouse.",
        },
    ]

    st.dataframe(
        pd.DataFrame(definitions),
        use_container_width=True,
        hide_index=True,
    )

st.caption(
    "Risk score is an analytical indicator, not official health or medical guidance."
)
