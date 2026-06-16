-- 1. Fonction qui envoie la notification
DROP TRIGGER IF EXISTS weather_insert_notify ON weather_hourly;
DROP FUNCTION IF EXISTS notify_new_weather();

CREATE OR REPLACE FUNCTION notify_new_weather()
RETURNS trigger AS $$
BEGIN
  PERFORM pg_notify(
    'new_weather_data',
    json_build_object(
      'station_id', NEW.station_id,
      'date_heure', NEW.date_heure
    )::text
  );
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 2. Trigger déclenché à chaque INSERT sur ta table
CREATE TRIGGER weather_insert_notify
AFTER INSERT ON weather_hourly
FOR EACH ROW EXECUTE FUNCTION notify_new_weather();

SELECT trigger_name, event_manipulation, event_object_table
FROM information_schema.triggers
WHERE trigger_name = 'weather_insert_notify';