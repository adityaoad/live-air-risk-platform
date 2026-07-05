WITH cities AS (
    SELECT
        city_id,
        city_name,
        state_region,
        country
    FROM {{ ref('stg_cities') }}
),

active_alerts AS (
    SELECT
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
        ingested_at,
        CASE
            WHEN severity = 'Extreme' THEN 5
            WHEN severity = 'Severe' THEN 4
            WHEN severity = 'Moderate' THEN 3
            WHEN severity = 'Minor' THEN 2
            WHEN severity = 'Unknown' THEN 1
            ELSE 0
        END AS severity_rank
    FROM raw.noaa_weather_alerts
    WHERE
        (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
        AND (status IS NULL OR status = 'Actual')
),

alert_counts AS (
    SELECT
        city_id,
        COUNT(*) AS active_alert_count,
        MAX(severity_rank) AS max_severity_rank
    FROM active_alerts
    GROUP BY city_id
),

latest_alert AS (
    SELECT
        city_id,
        event AS latest_alert_event,
        headline AS latest_alert_headline,
        severity AS latest_alert_severity,
        urgency AS latest_alert_urgency,
        certainty AS latest_alert_certainty,
        expires_at AS latest_alert_expires_at,
        ROW_NUMBER() OVER (
            PARTITION BY city_id
            ORDER BY effective_at DESC NULLS LAST, ingested_at DESC
        ) AS rn
    FROM active_alerts
)

SELECT
    c.city_id,
    c.city_name,
    c.state_region,
    c.country,

    COALESCE(ac.active_alert_count, 0) AS active_alert_count,

    CASE
        WHEN ac.max_severity_rank = 5 THEN 'Extreme'
        WHEN ac.max_severity_rank = 4 THEN 'Severe'
        WHEN ac.max_severity_rank = 3 THEN 'Moderate'
        WHEN ac.max_severity_rank = 2 THEN 'Minor'
        WHEN ac.max_severity_rank = 1 THEN 'Unknown'
        ELSE 'None'
    END AS highest_alert_severity,

    la.latest_alert_event,
    la.latest_alert_headline,
    la.latest_alert_severity,
    la.latest_alert_urgency,
    la.latest_alert_certainty,
    la.latest_alert_expires_at,

    CASE
        WHEN COALESCE(ac.active_alert_count, 0) > 0 THEN TRUE
        ELSE FALSE
    END AS has_active_alert,

    CURRENT_TIMESTAMP AS modeled_at

FROM cities c
LEFT JOIN alert_counts ac
    ON c.city_id = ac.city_id
LEFT JOIN latest_alert la
    ON c.city_id = la.city_id
    AND la.rn = 1
