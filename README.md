# Live Air Quality & Weather Risk Platform

An end-to-end live data platform that ingests weather and air-quality data, stores raw and cleaned data in PostgreSQL, models city-level environmental risk, and supports dashboards in Streamlit plus BI tools like Power BI, Tableau, and Looker.

## Stack

Python, PostgreSQL, dbt Core, Streamlit, GitHub Actions, scikit-learn

## Data Sources

- Open-Meteo Weather API
- Open-Meteo Air Quality API
- Optional later: OpenAQ, NOAA/NWS, NASA POWER

## MVP Scope

- Controlled city seed list
- Live weather and air-quality ingestion
- Raw and analytics database layers
- City-level risk scoring
- Streamlit dashboard
- BI-ready marts for Power BI, Tableau, and Looker
