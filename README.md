# Live Air Quality & Weather Risk Platform

An end-to-end live data platform that ingests weather and air-quality data, stores raw and modeled data in PostgreSQL, calculates city-level environmental risk, and serves a dashboard in Streamlit.

## Current MVP Status

Working:
- Python 3.12 virtual environment
- Neon PostgreSQL database
- Raw weather and air-quality tables
- City seed table with 13 cities
- Open-Meteo weather ingestion
- Open-Meteo air-quality ingestion
- API request logging
- Retry handling for API timeout failures
- dbt staging models
- dbt risk marts
- BI-ready marts for Power BI, Tableau, and Looker
- Data quality summary mart
- Streamlit dashboard
- GitHub Actions scheduled ingestion every 3 hours

Not done yet:
- Streamlit cloud deployment
- Power BI/Tableau/Looker dashboard connection
- Anomaly detection
- Forecasting
- OpenAQ or NOAA enrichment
- Final screenshots and project polish

## Stack

Python 3.12, PostgreSQL/Neon, dbt Core, dbt-postgres, Streamlit, Plotly, pandas, psycopg2, GitHub Actions, Open-Meteo Weather API, Open-Meteo Air Quality API.

## Architecture

Open-Meteo APIs are ingested with Python scripts into raw PostgreSQL tables. dbt transforms the raw data into staging views, risk marts, BI-ready marts, and data quality summary tables. Streamlit reads from the analytics marts to display city-level environmental risk, AQI trends, pollutant trends, weather context, and data freshness.

## Database Tables

Raw schema:
- raw.api_requests
- raw.open_meteo_weather_hourly
- raw.open_meteo_air_quality_hourly

Analytics schema:
- analytics.cities
- analytics.stg_cities
- analytics.stg_weather_hourly
- analytics.stg_air_quality_hourly
- analytics.mart_city_hourly_risk
- analytics.mart_latest_city_risk
- analytics.mart_bi_city_risk_summary
- analytics.mart_bi_hourly_city_trends
- analytics.mart_data_quality_summary

## Local Setup

Create and activate a virtual environment:

    python3.12 -m venv .venv
    source .venv/bin/activate

Install dependencies:

    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt

Create a .env file:

    cp .env.example .env

Add your Neon connection string:

    DATABASE_URL=your_neon_postgres_connection_string

## Run Database Setup

    python db/setup_db.py

## Run Ingestion Locally

    python -m ingestion.run_pipeline

## Run dbt

    cd dbt/air_risk
    dbt debug --profiles-dir .
    dbt run --profiles-dir .
    dbt test --profiles-dir .
    cd ../..

## Run Streamlit Dashboard

    streamlit run app/streamlit_app.py

## Scheduling

GitHub Actions runs the ingestion and dbt pipeline every 3 hours.

Required GitHub repository secret:

    DATABASE_URL

## Dashboard Notes

The Streamlit dashboard displays timestamps in Mountain Time with an MT suffix. Database timestamps are stored as raw timestamps from ingestion/modeling, while dashboard display is formatted for readability.

## Risk Score Disclaimer

The environmental risk score is an analytical indicator. It is not official health, medical, or emergency guidance.

## BI Dashboard Plan

Power BI, Tableau, or Looker can connect directly to the BI-ready marts:
- analytics.mart_bi_city_risk_summary
- analytics.mart_bi_hourly_city_trends

These tables are designed for city ranking, AQI trend analysis, pollutant comparison, weather context, and risk segmentation.
