import os
from pathlib import Path

import psycopg2
from dotenv import load_dotenv


def run_sql_file(conn, file_path):
    sql = Path(file_path).read_text(encoding="utf-8")

    with conn.cursor() as cur:
        cur.execute(sql)

    conn.commit()


def main():
    load_dotenv(".env")

    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise ValueError("DATABASE_URL missing from .env")

    with psycopg2.connect(database_url) as conn:
        run_sql_file(conn, "db/schema.sql")
        run_sql_file(conn, "db/seed_cities.sql")

    print("Database setup completed.")


if __name__ == "__main__":
    main()
