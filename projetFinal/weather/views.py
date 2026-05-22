from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import OrderingFilter, SearchFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from datetime import timedelta
from django.views.generic import TemplateView

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
    RegionWithStationSerializer,
    ApiSourceSerializer,
    UnitSerializer,
    VariableSerializer,
    WeatherStationSerializer,
    WeatherStationSummarySerializer,
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

    @action(detail=False, methods=['get'], url_path='with-station')
    def with_station(self, request):
        queryset = self.get_queryset().select_related('climate_type')
        serializer = RegionWithStationSerializer(queryset, many=True)
        return Response(serializer.data)


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

    @action(detail=True, methods=['get'], url_path='current')
    def current(self, request, pk=None):
        station = self.get_object()
        latest = (
            WeatherHourly.objects
            .filter(station=station)
            .select_related('station', 'source_api')
            .order_by('-date_heure')
            .first()
        )
        if latest is None:
            # return empty object (200) so frontend can handle absence without 404 network error
            return Response({})
        return Response(WeatherHourlySerializer(latest).data)

    @action(detail=True, methods=['get'], url_path='hourly-history')
    def hourly_history(self, request, pk=None):
        station = self.get_object()
        hours = int(request.query_params.get('hours', 24))
        queryset = (
            WeatherHourly.objects
            .filter(station=station)
            .select_related('station', 'source_api')
            .order_by('-date_heure')
        )
        return Response(WeatherHourlySerializer(queryset[:hours], many=True).data)

    @action(detail=True, methods=['get'], url_path='daily-trend')
    def daily_trend(self, request, pk=None):
        station = self.get_object()
        days = int(request.query_params.get('days', 7))
        queryset = (
            WeatherDaily.objects
            .filter(station=station)
            .select_related('station', 'source_api')
            .order_by('-date')
        )
        return Response(WeatherDailySerializer(queryset[:days], many=True).data)

    @action(detail=True, methods=['get'], url_path='report-today')
    def report_today(self, request, pk=None):
        station = self.get_object()
        report = (
            WeatherReport.objects
            .filter(station=station)
            .select_related('station')
            .order_by('-date')
            .first()
        )
        if report is None:
            # return empty object so frontend can handle gracefully without 404
            return Response({})
        return Response(WeatherReportSerializer(report).data)

    @action(detail=True, methods=['get'], url_path='active-alerts')
    def active_alerts(self, request, pk=None):
        station = self.get_object()
        queryset = (
            Alert.objects
            .filter(station=station)
            .select_related('station')
            .order_by('-date_heure')
        )
        if not queryset.exists():
            return Response([])
        return Response(AlertSerializer(queryset, many=True).data)


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


class DashboardView(TemplateView):
    template_name = 'weather/dashboard.html'


class VisualizationHistoriqueView(TemplateView):
    template_name = 'weather/visualization_historique.html'


class VisualizationTendancesView(TemplateView):
    template_name = 'weather/visualization_tendances.html'


class ReportsListView(TemplateView):
    template_name = 'weather/reports_list.html'


class ReportDetailView(TemplateView):
    template_name = 'weather/report_detail.html'