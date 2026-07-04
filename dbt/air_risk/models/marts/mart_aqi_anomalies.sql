WITH base AS (
    SELECT
        city_id,
        city_name,
        state_region,
        country,
        observation_time,
        us_aqi,
        pm2_5,
        pm10,
        ozone,
        environmental_risk_score,
        risk_label,

        AVG(us_aqi) OVER (
            PARTITION BY city_id
            ORDER BY observation_time
            ROWS BETWEEN 24 PRECEDING AND 1 PRECEDING
        ) AS rolling_avg_aqi_24h,

        STDDEV(us_aqi) OVER (
            PARTITION BY city_id
            ORDER BY observation_time
            ROWS BETWEEN 24 PRECEDING AND 1 PRECEDING
        ) AS rolling_std_aqi_24h

    FROM {{ ref('mart_city_hourly_risk') }}
    WHERE us_aqi IS NOT NULL
),

scored AS (
    SELECT
        *,
        CASE
            WHEN rolling_std_aqi_24h IS NULL OR rolling_std_aqi_24h = 0 THEN NULL
            ELSE (us_aqi - rolling_avg_aqi_24h) / rolling_std_aqi_24h
        END AS aqi_z_score
    FROM base
)

SELECT
    *,
    CASE
        WHEN aqi_z_score >= 2.5 THEN TRUE
        ELSE FALSE
    END AS is_aqi_anomaly
FROM scored
