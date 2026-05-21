"""
URL configuration for weather_dashboard project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from weather.views import (
    ClimateTypeViewSet,
    RegionViewSet,
    ApiSourceViewSet,
    UnitViewSet,
    VariableViewSet,
    WeatherStationViewSet,
    WeatherHourlyViewSet,
    WeatherDailyViewSet,
    WeatherReportViewSet,
    AlertViewSet
)
from weather.views import DashboardView
from weather.views import VisualizationHistoriqueView, VisualizationTendancesView

# Initialisation du routeur automatique de DRF
router = DefaultRouter()

# Enregistrement des routes pour chaque ViewSet
router.register(r'climate-types', ClimateTypeViewSet, basename='climatetype')
router.register(r'regions', RegionViewSet, basename='region')
router.register(r'api-sources', ApiSourceViewSet, basename='apisource')
router.register(r'units', UnitViewSet, basename='unit')
router.register(r'variables', VariableViewSet, basename='variable')
router.register(r'weather-stations', WeatherStationViewSet, basename='weatherstation')
router.register(r'weather-hourly', WeatherHourlyViewSet, basename='weatherhourly')
router.register(r'weather-daily', WeatherDailyViewSet, basename='weatherdaily')
router.register(r'weather-reports', WeatherReportViewSet, basename='weatherreport')
router.register(r'alerts', AlertViewSet, basename='alert')

# Les URLs de l'application incluent toutes les routes générées par le routeur
urlpatterns = [
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('visualization/historique/', VisualizationHistoriqueView.as_view(), name='visualization-historique'),
    path('visualization/tendances/', VisualizationTendancesView.as_view(), name='visualization-tendances'),
    path('', include(router.urls)),
]