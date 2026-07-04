SELECT
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
    surface_pressure,
    source,
    ingested_at
FROM raw.open_meteo_weather_hourly
WHERE observation_time IS NOT NULL
