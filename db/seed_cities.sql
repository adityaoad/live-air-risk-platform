INSERT INTO analytics.cities (city_name, state_region, country, latitude, longitude, timezone) VALUES
('Denver', 'Colorado', 'United States', 39.739236, -104.990251, 'America/Denver'),
('Los Angeles', 'California', 'United States', 34.052235, -118.243683, 'America/Los_Angeles'),
('San Francisco', 'California', 'United States', 37.774929, -122.419416, 'America/Los_Angeles'),
('Seattle', 'Washington', 'United States', 47.606209, -122.332071, 'America/Los_Angeles'),
('Austin', 'Texas', 'United States', 30.267153, -97.743061, 'America/Chicago'),
('Dallas', 'Texas', 'United States', 32.776665, -96.796989, 'America/Chicago'),
('New York', 'New York', 'United States', 40.712776, -74.005974, 'America/New_York'),
('Chicago', 'Illinois', 'United States', 41.878113, -87.629799, 'America/Chicago'),
('Phoenix', 'Arizona', 'United States', 33.448376, -112.074036, 'America/Phoenix'),
('Salt Lake City', 'Utah', 'United States', 40.760780, -111.891045, 'America/Denver'),
('London', 'England', 'United Kingdom', 51.507351, -0.127758, 'Europe/London'),
('Delhi', 'Delhi', 'India', 28.704060, 77.102493, 'Asia/Kolkata'),
('Tokyo', 'Tokyo', 'Japan', 35.676192, 139.650311, 'Asia/Tokyo')
ON CONFLICT (city_name, state_region, country) DO NOTHING;
