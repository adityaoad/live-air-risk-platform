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
            ROWS BETWEEN 6 PRECEDING AND 1 PRECEDING
        ) AS rolling_avg_aqi_6h,

        AVG(us_aqi) OVER (
            PARTITION BY city_id
            ORDER BY observation_time
            ROWS BETWEEN 12 PRECEDING AND 1 PRECEDING
        ) AS rolling_avg_aqi_12h,

        LAG(us_aqi, 1) OVER (
            PARTITION BY city_id
            ORDER BY observation_time
        ) AS previous_aqi

    FROM {{ ref('mart_city_hourly_risk') }}
    WHERE us_aqi IS NOT NULL
),

forecasted AS (
    SELECT
        *,
        COALESCE(rolling_avg_aqi_6h, rolling_avg_aqi_12h, previous_aqi) AS forecast_aqi_baseline,
        ABS(us_aqi - COALESCE(rolling_avg_aqi_6h, rolling_avg_aqi_12h, previous_aqi)) AS forecast_absolute_error
    FROM base
)

SELECT
    *,
    CASE
        WHEN forecast_aqi_baseline IS NULL THEN NULL
        WHEN forecast_aqi_baseline <= 50 THEN 'Good'
        WHEN forecast_aqi_baseline <= 100 THEN 'Moderate'
        WHEN forecast_aqi_baseline <= 150 THEN 'Unhealthy for Sensitive Groups'
        WHEN forecast_aqi_baseline <= 200 THEN 'Unhealthy'
        WHEN forecast_aqi_baseline <= 300 THEN 'Very Unhealthy'
        ELSE 'Hazardous'
    END AS forecast_aqi_category
FROM forecasted
