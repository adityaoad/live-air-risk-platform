import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import psycopg2
import requests
from psycopg2.extras import Json, execute_batch

from ingestion.utils import get_active_cities, load_database_url


NOAA_ALERTS_URL = "https://api.weather.gov/alerts/active"


def parse_noaa_time(value: Optional[str]):
    if not value:
        return None

    return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)


def is_us_city(city: Dict[str, Any]) -> bool:
    return city.get("country") == "United States"


def fetch_alerts_for_city(city: Dict[str, Any]) -> Dict[str, Any]:
    user_agent = os.getenv(
        "NOAA_USER_AGENT",
        "live-air-risk-platform/1.0 contact@example.com",
    )

    headers = {
        "User-Agent": user_agent,
        "Accept": "application/geo+json",
    }

    params = {
        "point": f"{city['latitude']},{city['longitude']}",
    }

    response = requests.get(
        NOAA_ALERTS_URL,
        headers=headers,
        params=params,
        timeout=60,
    )

    response.raise_for_status()
    return response.json()


def transform_alerts(city: Dict[str, Any], response_json: Dict[str, Any]) -> List[Dict[str, Any]]:
    features = response_json.get("features", [])
    rows = []

    for feature in features:
        properties = feature.get("properties", {})

        alert_id = properties.get("id")
        if not alert_id:
            continue

        rows.append(
            {
                "alert_id": alert_id,
                "city_id": city["city_id"],
                "event": properties.get("event"),
                "headline": properties.get("headline"),
                "severity": properties.get("severity"),
                "urgency": properties.get("urgency"),
                "certainty": properties.get("certainty"),
                "status": properties.get("status"),
                "effective_at": parse_noaa_time(properties.get("effective")),
                "expires_at": parse_noaa_time(properties.get("expires")),
                "area_desc": properties.get("areaDesc"),
                "instruction": properties.get("instruction"),
                "response_json": response_json,
            }
        )

    return rows


def upsert_alerts(conn, rows: List[Dict[str, Any]]) -> None:
    if not rows:
        return

    query = """
        INSERT INTO raw.noaa_weather_alerts (
            alert_id,
            city_id,
            event,
            headline,
            severity,
            urgency,
            certainty,
            status,
            effective_at,
            expires_at,
            area_desc,
            instruction,
            response_json
        )
        VALUES (
            %(alert_id)s,
            %(city_id)s,
            %(event)s,
            %(headline)s,
            %(severity)s,
            %(urgency)s,
            %(certainty)s,
            %(status)s,
            %(effective_at)s,
            %(expires_at)s,
            %(area_desc)s,
            %(instruction)s,
            %(response_json)s
        )
        ON CONFLICT (alert_id)
        DO UPDATE SET
            city_id = EXCLUDED.city_id,
            event = EXCLUDED.event,
            headline = EXCLUDED.headline,
            severity = EXCLUDED.severity,
            urgency = EXCLUDED.urgency,
            certainty = EXCLUDED.certainty,
            status = EXCLUDED.status,
            effective_at = EXCLUDED.effective_at,
            expires_at = EXCLUDED.expires_at,
            area_desc = EXCLUDED.area_desc,
            instruction = EXCLUDED.instruction,
            response_json = EXCLUDED.response_json,
            ingested_at = CURRENT_TIMESTAMP;
    """

    rows_for_insert = [
        {
            **row,
            "response_json": Json(row["response_json"]),
        }
        for row in rows
    ]

    with conn.cursor() as cur:
        execute_batch(cur, query, rows_for_insert)

    conn.commit()


def main() -> None:
    database_url = load_database_url()

    with psycopg2.connect(database_url) as conn:
        cities = get_active_cities(conn)
        us_cities = [city for city in cities if is_us_city(city)]

        print(f"Found {len(us_cities)} US cities for NOAA alert ingestion.")

        total_alerts = 0

        for city in us_cities:
            city_label = f"{city['city_name']}, {city['state_region']}"

            try:
                print(f"Fetching NOAA alerts for {city_label}...")

                response_json = fetch_alerts_for_city(city)
                rows = transform_alerts(city, response_json)
                upsert_alerts(conn, rows)

                print(f"{city_label}: upserted {len(rows)} active alerts.")
                total_alerts += len(rows)

            except requests.exceptions.RequestException as error:
                print(f"NOAA request failed for {city_label}: {error}")

            except Exception as error:
                print(f"Unexpected error for {city_label}: {error}")

        print(f"NOAA alert ingestion completed. Total active alerts upserted: {total_alerts}")


if __name__ == "__main__":
    main()
