//////////////////////////////////////////////////////////////
// WEATHER ANALYTICS MADAGASCAR
// DBDIAGRAM.IO VERSION
//////////////////////////////////////////////////////////////

Table climate_types {
  id int [pk, increment]
  nom_climat varchar
  description text
}

Table regions {
  id int [pk, increment]
  nom_region varchar
  chef_lieu varchar
  latitude decimal
  longitude decimal
  altitude_moyenne decimal

  climate_type_id int [ref: > climate_types.id]
}

Table districts {
  id int [pk, increment]
  nom_district varchar

  region_id int [ref: > regions.id]

  latitude decimal
  longitude decimal
}

Table timezones {
  id int [pk, increment]
  timezone_name varchar
  utc_offset varchar
  description text
}

Table api_sources {
  id int [pk, increment]
  nom_source varchar
  base_url text
  description text
  api_type varchar
  is_active boolean
}

Table units {
  id int [pk, increment]
  nom_unite varchar
  symbole varchar
  type_variable varchar
}

Table variables {
  id int [pk, increment]

  code varchar
  nom_variable varchar

  unite_id int [ref: > units.id]

  type_variable varchar
  description text
}

Table weather_locations {
  id int [pk, increment]

  nom_station varchar

  region_id int [ref: > regions.id]
  district_id int [ref: > districts.id]

  latitude decimal
  longitude decimal

  altitude decimal

  timezone_id int [ref: > timezones.id]
}

Table weather_raw {
  id bigint [pk, increment]

  location_id int [ref: > weather_locations.id]
  source_api_id int [ref: > api_sources.id]

  date_heure datetime

  raw_data json

  created_at timestamp
}

Table weather_clean {
  id bigint [pk, increment]

  raw_id bigint [ref: > weather_raw.id]

  location_id int [ref: > weather_locations.id]

  date_heure datetime

  temperature_2m decimal
  relative_humidity_2m decimal

  precipitation decimal
  rain decimal

  wind_speed_10m decimal
  wind_direction_10m decimal

  surface_pressure decimal

  apparent_temperature decimal

  uv_index decimal

  is_day boolean

  created_at timestamp
}

Table weather_hourly {
  id bigint [pk, increment]

  location_id int [ref: > weather_locations.id]

  date_heure datetime

  temperature_2m decimal
  relative_humidity_2m decimal

  precipitation decimal
  rain decimal

  wind_speed_10m decimal
  wind_direction_10m decimal

  surface_pressure decimal

  uv_index decimal

  apparent_temperature decimal

  created_at timestamp
}

Table weather_daily {
  id bigint [pk, increment]

  location_id int [ref: > weather_locations.id]

  date date

  temperature_2m_max decimal
  temperature_2m_min decimal

  precipitation_sum decimal
  rain_sum decimal

  wind_speed_10m_max decimal
  wind_gusts_10m_max decimal

  sunshine_duration decimal

  uv_index_max decimal

  is_day boolean

  created_at timestamp
}

Table weather_report {
  id bigint [pk, increment]

  location_id int [ref: > weather_locations.id]

  date date

  summary_text text

  temperature_avg decimal
  temperature_min decimal
  temperature_max decimal

  precipitation_sum decimal

  humidity_avg decimal

  wind_speed_avg decimal

  feels_like_avg decimal

  created_at timestamp
}

Table data_quality {
  id bigint [pk, increment]

  raw_id bigint [ref: > weather_raw.id]

  status varchar

  message text

  checked_at timestamp
}

Table alerts {
  id bigint [pk, increment]

  location_id int [ref: > weather_locations.id]

  date_heure datetime

  type_alerte varchar

  niveau varchar

  message text

  created_at timestamp
}

//////////////////////////////////////////////////////////////
// MVP VERSION
//////////////////////////////////////////////////////////////

// MVP TABLES:
//
// regions
// weather_locations
// weather_raw
// weather_clean
// weather_daily
// weather_report
// api_sources
//
// MVP API VARIABLES:
//
// temperature_2m
// relative_humidity_2m
// precipitation
// wind_speed_10m
// surface_pressure
//
// MVP STATIC FILES:
//
// regions_madagascar.csv
// weather_locations.csv
// api_sources.json
// schema.sql
// config.yaml
//
//////////////////////////////////////////////////////////////