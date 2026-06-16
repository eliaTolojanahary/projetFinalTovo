from django.db import migrations


SQL_CREATE = """
DROP TRIGGER IF EXISTS weather_insert_notify ON weather_hourly;

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

CREATE TRIGGER weather_insert_notify
AFTER INSERT ON weather_hourly
FOR EACH ROW EXECUTE FUNCTION notify_new_weather();
"""

SQL_DROP = """
DROP TRIGGER IF EXISTS weather_insert_notify ON weather_hourly;
DROP FUNCTION IF EXISTS notify_new_weather();
"""


class Migration(migrations.Migration):
    dependencies = [
        ('weather', '0003_alter_climatetype_id'),
    ]

    operations = [
        migrations.RunSQL(SQL_CREATE, reverse_sql=SQL_DROP),
    ]
