import os

import psycopg2
from psycopg2.extras import Json, execute_batch

from ingestion.utils import get_active_cities, load_database_url, parse_time, fetch_json_with_retries


AQ_HOURLY = [
    "us_aqi",
    "pm10",
    "pm2_5",
    "carbon_monoxide",
    "nitrogen_dioxide",
    "sulphur_dioxide",
    "ozone",
    "uv_index",
]


def fetch_air_quality(city):
    base_url = os.getenv(
        "OPEN_METEO_AIR_QUALITY_URL",
        "https://air-quality-api.open-meteo.com/v1/air-quality",
    )

    params = {
        "latitude": city["latitude"],
        "longitude": city["longitude"],
        "hourly": ",".join(AQ_HOURLY),
        "forecast_days": 2,
        "timezone": "auto",
    }

    return fetch_json_with_retries(
        base_url,
        params=params,
        timeout=60,
        retries=3,
        backoff_seconds=10,
    )


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
            'open_meteo_air_quality',
            'air-quality',
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


def flatten_air_quality(city_id, payload):
    hourly = payload.get("hourly", {})
    times = hourly.get("time", [])

    rows = []

    for idx, ts in enumerate(times):
        rows.append(
            {
                "city_id": city_id,
                "observation_time": parse_time(ts),
                "us_aqi": get_hourly_value(hourly, "us_aqi", idx, len(times)),
                "pm10": get_hourly_value(hourly, "pm10", idx, len(times)),
                "pm2_5": get_hourly_value(hourly, "pm2_5", idx, len(times)),
                "carbon_monoxide": get_hourly_value(hourly, "carbon_monoxide", idx, len(times)),
                "nitrogen_dioxide": get_hourly_value(hourly, "nitrogen_dioxide", idx, len(times)),
                "sulphur_dioxide": get_hourly_value(hourly, "sulphur_dioxide", idx, len(times)),
                "ozone": get_hourly_value(hourly, "ozone", idx, len(times)),
                "uv_index": get_hourly_value(hourly, "uv_index", idx, len(times)),
            }
        )

    return rows


def upsert_air_quality_rows(conn, rows):
    if not rows:
        return 0

    query = """
        INSERT INTO raw.open_meteo_air_quality_hourly (
            city_id,
            observation_time,
            us_aqi,
            pm10,
            pm2_5,
            carbon_monoxide,
            nitrogen_dioxide,
            sulphur_dioxide,
            ozone,
            uv_index
        )
        VALUES (
            %(city_id)s,
            %(observation_time)s,
            %(us_aqi)s,
            %(pm10)s,
            %(pm2_5)s,
            %(carbon_monoxide)s,
            %(nitrogen_dioxide)s,
            %(sulphur_dioxide)s,
            %(ozone)s,
            %(uv_index)s
        )
        ON CONFLICT (city_id, observation_time, source)
        DO UPDATE SET
            us_aqi = EXCLUDED.us_aqi,
            pm10 = EXCLUDED.pm10,
            pm2_5 = EXCLUDED.pm2_5,
            carbon_monoxide = EXCLUDED.carbon_monoxide,
            nitrogen_dioxide = EXCLUDED.nitrogen_dioxide,
            sulphur_dioxide = EXCLUDED.sulphur_dioxide,
            ozone = EXCLUDED.ozone,
            uv_index = EXCLUDED.uv_index,
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
            request_url, status_code, payload = fetch_air_quality(city)
            log_api_request(conn, city["city_id"], request_url, status_code, payload)

            rows = flatten_air_quality(city["city_id"], payload)
            inserted_count = upsert_air_quality_rows(conn, rows)
            total_rows += inserted_count

            print(f"{city['city_name']}: upserted {inserted_count} air-quality rows")

        conn.commit()

    print(f"Air-quality ingestion completed. Total rows processed: {total_rows}")


if __name__ == "__main__":
    main()
