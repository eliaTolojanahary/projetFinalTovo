from django.db import models

# =========================================================
# MODELS EXISTANTS (Corrigés)
# =========================================================

class ClimateType(models.Model):
    id = models.BigAutoField(primary_key=True)
    nom_climat = models.CharField(max_length=100) 
    description = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = "climate_types"

    def __str__(self): # CORRECTION: ajout de 'self'
        return f"Climat : {self.nom_climat} - {self.description[:50]}..." if self.description else f"Climat : {self.nom_climat}"

class Region(models.Model):
    nom_region = models.CharField(max_length=150, unique=True)
    chef_lieu = models.CharField(max_length=150, blank=True, null=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=6)
    longitude = models.DecimalField(max_digits=10, decimal_places=6)
    altitude_moyenne = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    climate_type = models.ForeignKey(
        ClimateType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column="climate_type_id",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "regions"
        indexes = [
            models.Index(fields=['nom_region'], name='idx_regions_nom'),
        ]

    def __str__(self):
        return f"Région {self.nom_region} (Chef-lieu: {self.chef_lieu or 'Non défini'})"


# =========================================================
# NOUVEAUX MODELS BASÉS SUR LE SCHÉMA SQL
# =========================================================

class ApiSource(models.Model):
    nom_source = models.CharField(max_length=150)
    base_url = models.TextField()
    description = models.TextField(blank=True, null=True)
    api_type = models.CharField(max_length=100, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "api_sources"

    def __str__(self):
        statut = "Actif" if self.is_active else "Inactif"
        return f"API : {self.nom_source} [{statut}] - Type: {self.api_type or 'N/A'}"


class Unit(models.Model):
    nom_unite = models.CharField(max_length=100)
    symbole = models.CharField(max_length=50, blank=True, null=True)
    type_variable = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        db_table = "units"

    def __str__(self):
        return f"Unité : {self.nom_unite} ({self.symbole or 'Pas de symbole'})"


class Variable(models.Model):
    code = models.CharField(max_length=100, unique=True)
    nom_variable = models.CharField(max_length=150)
    unite = models.ForeignKey(
        Unit, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    type_variable = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "variables"

    def __str__(self):
        unite_symbole = self.unite.symbole if self.unite else 'N/A'
        return f"Variable : {self.nom_variable} [{self.code}] - En : {unite_symbole}"


class WeatherStation(models.Model):
    nom_station = models.CharField(max_length=150)
    # Remplacé par OneToOneField car 'region_id' est UNIQUE dans le SQL (1 région = 1 station)
    region = models.OneToOneField(Region, on_delete=models.CASCADE) 
    latitude = models.DecimalField(max_digits=10, decimal_places=6)
    longitude = models.DecimalField(max_digits=10, decimal_places=6)
    altitude = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    timezone = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "weather_stations"

    def __str__(self):
        return f"Station : {self.nom_station} (Région : {self.region.nom_region})"


class WeatherHourly(models.Model):
    station = models.ForeignKey(WeatherStation, on_delete=models.CASCADE)
    date_heure = models.DateTimeField()
    temperature_2m = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    relative_humidity_2m = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    apparent_temperature = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    precipitation = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    rain = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    wind_speed_10m = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    wind_direction_10m = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    surface_pressure = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    uv_index = models.DecimalField(max_digits=4, decimal_places=2, blank=True, null=True)
    is_day = models.BooleanField(blank=True, null=True)
    source_api = models.ForeignKey(ApiSource, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "weather_hourly"
        indexes = [
            models.Index(fields=['station'], name='idx_weather_hourly_station'),
            models.Index(fields=['date_heure'], name='idx_weather_hourly_datetime'),
        ]

    def __str__(self):
        temp = f"{self.temperature_2m}°C" if self.temperature_2m else "N/A"
        return f"Relevé Horaire - {self.station.nom_station} le {self.date_heure.strftime('%Y-%m-%d %H:%M')} (Temp: {temp})"


class WeatherDaily(models.Model):
    station = models.ForeignKey(WeatherStation, on_delete=models.CASCADE)
    date = models.DateField()
    temperature_2m_max = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    temperature_2m_min = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    temperature_avg = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    relative_humidity_avg = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    precipitation_sum = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    rain_sum = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    wind_speed_10m_max = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    wind_speed_avg = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    wind_gusts_10m_max = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    sunshine_duration = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    uv_index_max = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    source_api = models.ForeignKey(ApiSource, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "weather_daily"
        indexes = [
            models.Index(fields=['station'], name='idx_weather_daily_station'),
            models.Index(fields=['date'], name='idx_weather_daily_date'),
        ]

    def __str__(self):
        return f"Météo Journalière - {self.station.nom_station} le {self.date} (Moyenne: {self.temperature_avg}°C)"


class WeatherReport(models.Model):
    station = models.ForeignKey(WeatherStation, on_delete=models.CASCADE)
    date = models.DateField()
    summary_text = models.TextField(blank=True, null=True)
    temperature_avg = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    temperature_min = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    temperature_max = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    precipitation_sum = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    humidity_avg = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    wind_speed_avg = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    feels_like_avg = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    weather_score = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "weather_report"
        indexes = [
            models.Index(fields=['station'], name='idx_weather_report_station'),
            models.Index(fields=['date'], name='idx_weather_report_date'),
        ]

    def __str__(self):
        return f"Rapport ({self.date}) : {self.station.nom_station} - Score météo: {self.weather_score or 'N/A'}"


class Alert(models.Model):
    station = models.ForeignKey(WeatherStation, on_delete=models.CASCADE)
    date_heure = models.DateTimeField()
    type_alerte = models.CharField(max_length=100, blank=True, null=True)
    niveau = models.CharField(max_length=50, blank=True, null=True)
    message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "alerts"
        indexes = [
            models.Index(fields=['station'], name='idx_alerts_station'),
            models.Index(fields=['date_heure'], name='idx_alerts_datetime'),
        ]

    def __str__(self):
        return f"ALERTE {self.niveau} [{self.type_alerte}] - Station: {self.station.nom_station} le {self.date_heure.strftime('%Y-%m-%d %H:%M')}"