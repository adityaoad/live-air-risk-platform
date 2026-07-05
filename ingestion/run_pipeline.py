from ingestion.open_meteo_weather_ingest import main as ingest_weather
from ingestion.open_meteo_air_quality_ingest import main as ingest_air_quality
from ingestion.noaa_alerts_ingest import main as ingest_noaa_alerts


def main():
    print("Starting weather ingestion...")
    ingest_weather()

    print("Starting air-quality ingestion...")
    ingest_air_quality()

    print("Starting NOAA weather alerts ingestion...")
    ingest_noaa_alerts()

    print("Pipeline completed successfully.")


if __name__ == "__main__":
    main()
