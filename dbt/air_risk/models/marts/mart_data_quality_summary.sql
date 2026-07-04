WITH weather AS (
    SELECT
        'raw.open_meteo_weather_hourly' AS table_name,
        COUNT(*) AS row_count,
        MIN(observation_time) AS earliest_observation_time,
        MAX(observation_time) AS latest_observation_time,
        MAX(ingested_at) AS latest_ingested_at,
        COUNT(*) FILTER (WHERE observation_time IS NULL) AS missing_observation_time_count
    FROM raw.open_meteo_weather_hourly
),

air_quality AS (
    SELECT
        'raw.open_meteo_air_quality_hourly' AS table_name,
        COUNT(*) AS row_count,
        MIN(observation_time) AS earliest_observation_time,
        MAX(observation_time) AS latest_observation_time,
        MAX(ingested_at) AS latest_ingested_at,
        COUNT(*) FILTER (WHERE observation_time IS NULL) AS missing_observation_time_count
    FROM raw.open_meteo_air_quality_hourly
),

city_risk AS (
    SELECT
        'analytics.mart_city_hourly_risk' AS table_name,
        COUNT(*) AS row_count,
        MIN(observation_time) AS earliest_observation_time,
        MAX(observation_time) AS latest_observation_time,
        MAX(latest_ingested_at) AS latest_ingested_at,
        COUNT(*) FILTER (WHERE observation_time IS NULL) AS missing_observation_time_count
    FROM {{ ref('mart_city_hourly_risk') }}
)

SELECT * FROM weather
UNION ALL
SELECT * FROM air_quality
UNION ALL
SELECT * FROM city_risk
