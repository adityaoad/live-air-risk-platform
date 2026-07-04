WITH joined AS (
    SELECT
        c.city_id,
        c.city_name,
        c.state_region,
        c.country,
        c.latitude,
        c.longitude,
        c.timezone,

        a.observation_time,
        a.us_aqi,
        a.pm10,
        a.pm2_5,
        a.carbon_monoxide,
        a.nitrogen_dioxide,
        a.sulphur_dioxide,
        a.ozone,
        a.uv_index,

        w.temperature_2m,
        w.relative_humidity_2m,
        w.apparent_temperature,
        w.precipitation,
        w.rain,
        w.weather_code,
        w.cloud_cover,
        w.wind_speed_10m,
        w.wind_gusts_10m,
        w.surface_pressure,

        GREATEST(a.ingested_at, w.ingested_at) AS latest_ingested_at

    FROM {{ ref('stg_air_quality_hourly') }} a
    JOIN {{ ref('stg_cities') }} c
        ON c.city_id = a.city_id
    LEFT JOIN {{ ref('stg_weather_hourly') }} w
        ON w.city_id = a.city_id
        AND w.observation_time = a.observation_time
),

scored AS (
    SELECT
        *,

        CASE
            WHEN us_aqi IS NULL THEN NULL
            WHEN us_aqi <= 50 THEN 'Good'
            WHEN us_aqi <= 100 THEN 'Moderate'
            WHEN us_aqi <= 150 THEN 'Unhealthy for Sensitive Groups'
            WHEN us_aqi <= 200 THEN 'Unhealthy'
            WHEN us_aqi <= 300 THEN 'Very Unhealthy'
            ELSE 'Hazardous'
        END AS aqi_category,

        LEAST(
            100,
            GREATEST(
                0,
                COALESCE(us_aqi, 0) * 0.70
                + COALESCE(pm2_5, 0) * 0.20
                + CASE WHEN apparent_temperature >= 95 THEN 10 ELSE 0 END
                + CASE WHEN wind_speed_10m <= 3 AND us_aqi >= 100 THEN 5 ELSE 0 END
                + CASE WHEN uv_index >= 8 THEN 5 ELSE 0 END
            )
        ) AS environmental_risk_score

    FROM joined
)

SELECT
    *,

    CASE
        WHEN environmental_risk_score IS NULL THEN NULL
        WHEN environmental_risk_score <= 25 THEN 'Low'
        WHEN environmental_risk_score <= 50 THEN 'Moderate'
        WHEN environmental_risk_score <= 75 THEN 'High'
        ELSE 'Severe'
    END AS risk_label

FROM scored
