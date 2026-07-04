import os
import json

import psycopg2
import requests
from psycopg2.extras import Json, execute_batch

from ingestion.utils import get_active_cities, load_database_url, parse_time


WEATHER_HOURLY = [
    "temperature_2m",
    "relative_humidity_2m",
    "apparent_temperature",
    "precipitation",
    "rain",
    "weather_code",
    "cloud_cover",
    "wind_speed_10m",
    "wind_gusts_10m",
    "surface_pressure",
]


def fetch_weather(city):
    base_url = os.getenv(
        "OPEN_METEO_WEATHER_URL",
        "https://api.open-meteo.com/v1/forecast",
    )

    params = {
        "latitude": city["latitude"],
        "longitude": city["longitude"],
        "hourly": ",".join(WEATHER_HOURLY),
        "forecast_days": 2,
        "timezone": "auto",
    }

    response = requests.get(base_url, params=params, timeout=30)
    response.raise_for_status()

    return response.url, response.status_code, response.json()


def log_api_request(conn, city_id, request_url, status_code, payload):
    query = """
        INSERT INTO raw.api_requests (
            source,
            endpoint,
            city_id,
            request_url,
            status_code,
            response_json
        )
        VALUES (
            'open_meteo_weather',
            'forecast',
            %s,
            %s,
            %s,
            %s
        );
    """

    with conn.cursor() as cur:
        cur.execute(query, (city_id, request_url, status_code, Json(payload)))


def get_hourly_value(hourly, key, idx, total_count):
    values = hourly.get(key, [None] * total_count)
    return values[idx] if idx < len(values) else None


def flatten_weather(city_id, payload):
    hourly = payload.get("hourly", {})
    times = hourly.get("time", [])

    rows = []

    for idx, ts in enumerate(times):
        rows.append(
            {
                "city_id": city_id,
                "observation_time": parse_time(ts),
                "temperature_2m": get_hourly_value(hourly, "temperature_2m", idx, len(times)),
                "relative_humidity_2m": get_hourly_value(hourly, "relative_humidity_2m", idx, len(times)),
                "apparent_temperature": get_hourly_value(hourly, "apparent_temperature", idx, len(times)),
                "precipitation": get_hourly_value(hourly, "precipitation", idx, len(times)),
                "rain": get_hourly_value(hourly, "rain", idx, len(times)),
                "weather_code": get_hourly_value(hourly, "weather_code", idx, len(times)),
                "cloud_cover": get_hourly_value(hourly, "cloud_cover", idx, len(times)),
                "wind_speed_10m": get_hourly_value(hourly, "wind_speed_10m", idx, len(times)),
                "wind_gusts_10m": get_hourly_value(hourly, "wind_gusts_10m", idx, len(times)),
                "surface_pressure": get_hourly_value(hourly, "surface_pressure", idx, len(times)),
            }
        )

    return rows


def upsert_weather_rows(conn, rows):
    if not rows:
        return 0

    query = """
        INSERT INTO raw.open_meteo_weather_hourly (
            city_id,
            observation_time,
            temperature_2m,
            relative_humidity_2m,
            apparent_temperature,
            precipitation,
            rain,
            weather_code,
            cloud_cover,
            wind_speed_10m,
            wind_gusts_10m,
            surface_pressure
        )
        VALUES (
            %(city_id)s,
            %(observation_time)s,
            %(temperature_2m)s,
            %(relative_humidity_2m)s,
            %(apparent_temperature)s,
            %(precipitation)s,
            %(rain)s,
            %(weather_code)s,
            %(cloud_cover)s,
            %(wind_speed_10m)s,
            %(wind_gusts_10m)s,
            %(surface_pressure)s
        )
        ON CONFLICT (city_id, observation_time, source)
        DO UPDATE SET
            temperature_2m = EXCLUDED.temperature_2m,
            relative_humidity_2m = EXCLUDED.relative_humidity_2m,
            apparent_temperature = EXCLUDED.apparent_temperature,
            precipitation = EXCLUDED.precipitation,
            rain = EXCLUDED.rain,
            weather_code = EXCLUDED.weather_code,
            cloud_cover = EXCLUDED.cloud_cover,
            wind_speed_10m = EXCLUDED.wind_speed_10m,
            wind_gusts_10m = EXCLUDED.wind_gusts_10m,
            surface_pressure = EXCLUDED.surface_pressure,
            ingested_at = CURRENT_TIMESTAMP;
    """

    with conn.cursor() as cur:
        execute_batch(cur, query, rows)

    return len(rows)


def main():
    database_url = load_database_url()

    with psycopg2.connect(database_url) as conn:
        cities = get_active_cities(conn)

        total_rows = 0

        for city in cities:
            request_url, status_code, payload = fetch_weather(city)
            log_api_request(conn, city["city_id"], request_url, status_code, payload)

            rows = flatten_weather(city["city_id"], payload)
            inserted_count = upsert_weather_rows(conn, rows)
            total_rows += inserted_count

            print(f"{city['city_name']}: upserted {inserted_count} weather rows")

        conn.commit()

    print(f"Weather ingestion completed. Total rows processed: {total_rows}")


if __name__ == "__main__":
    main()
