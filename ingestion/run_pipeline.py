from ingestion.open_meteo_weather_ingest import main as ingest_weather
from ingestion.open_meteo_air_quality_ingest import main as ingest_air_quality


def main():
    print("Starting weather ingestion...")
    ingest_weather()

    print("Starting air-quality ingestion...")
    ingest_air_quality()

    print("Pipeline completed successfully.")


if __name__ == "__main__":
    main()
