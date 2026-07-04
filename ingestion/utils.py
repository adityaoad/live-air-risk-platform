import os
from datetime import datetime
from typing import Any, Dict, List

from dotenv import load_dotenv


def load_database_url() -> str:
    load_dotenv(".env")

    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise ValueError("DATABASE_URL missing from environment")

    return database_url


def get_active_cities(conn) -> List[Dict[str, Any]]:
    query = """
        SELECT city_id, city_name, state_region, country, latitude, longitude, timezone
        FROM analytics.cities
        WHERE is_active = TRUE
        ORDER BY city_name;
    """

    with conn.cursor() as cur:
        cur.execute(query)
        rows = cur.fetchall()

    return [
        {
            "city_id": row[0],
            "city_name": row[1],
            "state_region": row[2],
            "country": row[3],
            "latitude": float(row[4]),
            "longitude": float(row[5]),
            "timezone": row[6],
        }
        for row in rows
    ]


def parse_time(value: str):
    if not value:
        return None

    return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
