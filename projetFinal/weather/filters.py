import django_filters
from .models import (
    Region,
    WeatherStation,
    WeatherHourly,
    WeatherDaily,
    WeatherReport,
    Alert
)

# =========================================================
# FILTRES DE BASE
# =========================================================

class RegionFilter(django_filters.FilterSet):
    # Recherche partielle (insensible à la casse)
    nom_region = django_filters.CharFilter(lookup_expr='icontains')
    chef_lieu = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = Region
        fields = ['nom_region', 'chef_lieu', 'climate_type']


class WeatherStationFilter(django_filters.FilterSet):
    nom_station = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = WeatherStation
        fields = ['nom_station', 'region']


# =========================================================
# FILTRES DE DONNÉES MÉTÉO (Avec plages de dates)
# =========================================================

class WeatherHourlyFilter(django_filters.FilterSet):
    # Permet de filtrer entre deux dates/heures exactes (ex: ?date_heure_after=2024-01-01T00:00:00Z)
    date_heure_after = django_filters.DateTimeFilter(field_name='date_heure', lookup_expr='gte')
    date_heure_before = django_filters.DateTimeFilter(field_name='date_heure', lookup_expr='lte')

    class Meta:
        model = WeatherHourly
        fields = ['station', 'is_day', 'source_api']


class WeatherDailyFilter(django_filters.FilterSet):
    # Permet de filtrer entre deux dates (ex: ?date_after=2024-01-01)
    date_after = django_filters.DateFilter(field_name='date', lookup_expr='gte')
    date_before = django_filters.DateFilter(field_name='date', lookup_expr='lte')

    class Meta:
        model = WeatherDaily
        fields = ['station', 'source_api']


class WeatherReportFilter(django_filters.FilterSet):
    date_after = django_filters.DateFilter(field_name='date', lookup_expr='gte')
    date_before = django_filters.DateFilter(field_name='date', lookup_expr='lte')

    class Meta:
        model = WeatherReport
        fields = ['station']


class AlertFilter(django_filters.FilterSet):
    date_after = django_filters.DateTimeFilter(field_name='date_heure', lookup_expr='gte')
    date_before = django_filters.DateTimeFilter(field_name='date_heure', lookup_expr='lte')
    type_alerte = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = Alert
        fields = ['station', 'niveau', 'type_alerte']