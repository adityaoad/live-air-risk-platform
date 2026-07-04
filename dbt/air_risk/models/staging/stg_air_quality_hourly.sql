SELECT
    city_id,
    observation_time,
    us_aqi,
    pm10,
    pm2_5,
    carbon_monoxide,
    nitrogen_dioxide,
    sulphur_dioxide,
    ozone,
    uv_index,
    source,
    ingested_at
FROM raw.open_meteo_air_quality_hourly
WHERE observation_time IS NOT NULL
