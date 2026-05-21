from rest_framework import viewsets
from rest_framework.filters import OrderingFilter, SearchFilter
from django_filters.rest_framework import DjangoFilterBackend

from .models import (
    ClimateType,
    Region,
    ApiSource,
    Unit,
    Variable,
    WeatherStation,
    WeatherHourly,
    WeatherDaily,
    WeatherReport,
    Alert
)
from .serializers import (
    ClimateTypeSerializer,
    RegionSerializer,
    ApiSourceSerializer,
    UnitSerializer,
    VariableSerializer,
    WeatherStationSerializer,
    WeatherHourlySerializer,
    WeatherDailySerializer,
    WeatherReportSerializer,
    AlertSerializer
)
from .filters import (
    RegionFilter,
    WeatherStationFilter,
    WeatherHourlyFilter,
    WeatherDailyFilter,
    WeatherReportFilter,
    AlertFilter
)

# =========================================================
# VIEWS / VIEWSETS DE CONFIGURATION ET CONFIGURATION MÉTÉO
# =========================================================

class ClimateTypeViewSet(viewsets.ModelViewSet):
    queryset = ClimateType.objects.all()
    serializer_class = ClimateTypeSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    search_fields = ['nom_climat', 'description']
    ordering_fields = ['nom_climat']
    ordering = ['nom_climat']


class RegionViewSet(viewsets.ModelViewSet):
    queryset = Region.objects.all().select_related('climate_type')
    serializer_class = RegionSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_class = RegionFilter
    search_fields = ['nom_region', 'chef_lieu']
    ordering_fields = ['nom_region', 'created_at']
    ordering = ['nom_region']


class ApiSourceViewSet(viewsets.ModelViewSet):
    queryset = ApiSource.objects.all()
    serializer_class = ApiSourceSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_fields = ['is_active', 'api_type']
    search_fields = ['nom_source', 'description']
    ordering_fields = ['nom_source', 'created_at']
    ordering = ['nom_source']


class UnitViewSet(viewsets.ModelViewSet):
    queryset = Unit.objects.all()
    serializer_class = UnitSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_fields = ['type_variable']
    search_fields = ['nom_unite', 'symbole']
    ordering_fields = ['nom_unite']


class VariableViewSet(viewsets.ModelViewSet):
    queryset = Variable.objects.all().select_related('unite')
    serializer_class = VariableSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_fields = ['type_variable', 'unite']
    search_fields = ['code', 'nom_variable', 'description']
    ordering_fields = ['code', 'nom_variable']
    ordering = ['code']


class WeatherStationViewSet(viewsets.ModelViewSet):
    queryset = WeatherStation.objects.all().select_related('region')
    serializer_class = WeatherStationSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_class = WeatherStationFilter
    search_fields = ['nom_station']
    ordering_fields = ['nom_station', 'altitude', 'created_at']
    ordering = ['nom_station']


# =========================================================
# VIEWS / VIEWSETS DES DONNÉES MÉTÉO ET ALERTES
# =========================================================

class WeatherHourlyViewSet(viewsets.ModelViewSet):
    # Utilisation de select_related pour optimiser les requêtes SQL (évite le problème N+1)
    queryset = WeatherHourly.objects.all().select_related('station', 'source_api')
    serializer_class = WeatherHourlySerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = WeatherHourlyFilter
    ordering_fields = ['date_heure', 'temperature_2m']
    ordering = ['-date_heure'] # Du plus récent au plus ancien par défaut


class WeatherDailyViewSet(viewsets.ModelViewSet):
    queryset = WeatherDaily.objects.all().select_related('station', 'source_api')
    serializer_class = WeatherDailySerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = WeatherDailyFilter
    ordering_fields = ['date', 'temperature_avg', 'precipitation_sum']
    ordering = ['-date']


class WeatherReportViewSet(viewsets.ModelViewSet):
    queryset = WeatherReport.objects.all().select_related('station')
    serializer_class = WeatherReportSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = WeatherReportFilter
    ordering_fields = ['date', 'weather_score']
    ordering = ['-date']


class AlertViewSet(viewsets.ModelViewSet):
    queryset = Alert.objects.all().select_related('station')
    serializer_class = AlertSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_class = AlertFilter
    search_fields = ['message']
    ordering_fields = ['date_heure', 'niveau']
    ordering = ['-date_heure']