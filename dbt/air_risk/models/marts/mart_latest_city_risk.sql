WITH ranked AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY city_id
            ORDER BY observation_time DESC
        ) AS rn
    FROM {{ ref('mart_city_hourly_risk') }}
    WHERE us_aqi IS NOT NULL
)

SELECT
    *
FROM ranked
WHERE rn = 1
