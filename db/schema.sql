CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS analytics;

CREATE TABLE IF NOT EXISTS analytics.cities (
    city_id SERIAL PRIMARY KEY,
    city_name TEXT NOT NULL,
    state_region TEXT,
    country TEXT NOT NULL,
    latitude NUMERIC(9,6) NOT NULL,
    longitude NUMERIC(9,6) NOT NULL,
    timezone TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(city_name, state_region, country)
);

CREATE TABLE IF NOT EXISTS raw.api_requests (
    request_id BIGSERIAL PRIMARY KEY,
    source TEXT NOT NULL,
    endpoint TEXT NOT NULL,
    city_id INTEGER REFERENCES analytics.cities(city_id),
    request_url TEXT,
    status_code INTEGER,
    response_json JSONB,
    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS raw.open_meteo_weather_hourly (
    city_id INTEGER REFERENCES analytics.cities(city_id),
    observation_time TIMESTAMP NOT NULL,
    temperature_2m NUMERIC,
    relative_humidity_2m NUMERIC,
    apparent_temperature NUMERIC,
    precipitation NUMERIC,
    rain NUMERIC,
    weather_code INTEGER,
    cloud_cover NUMERIC,
    wind_speed_10m NUMERIC,
    wind_gusts_10m NUMERIC,
    surface_pressure NUMERIC,
    source TEXT DEFAULT 'open_meteo_weather',
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (city_id, observation_time, source)
);

CREATE TABLE IF NOT EXISTS raw.open_meteo_air_quality_hourly (
    city_id INTEGER REFERENCES analytics.cities(city_id),
    observation_time TIMESTAMP NOT NULL,
    us_aqi NUMERIC,
    pm10 NUMERIC,
    pm2_5 NUMERIC,
    carbon_monoxide NUMERIC,
    nitrogen_dioxide NUMERIC,
    sulphur_dioxide NUMERIC,
    ozone NUMERIC,
    uv_index NUMERIC,
    source TEXT DEFAULT 'open_meteo_air_quality',
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (city_id, observation_time, source)
);
