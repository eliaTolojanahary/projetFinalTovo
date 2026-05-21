from rest_framework import serializers
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

# =========================================================
# SERIALIZERS DE BASE
# =========================================================

class ClimateTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClimateType
        fields = '__all__'


class RegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = '__all__'


class ApiSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApiSource
        fields = '__all__'


class UnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Unit
        fields = '__all__'


class VariableSerializer(serializers.ModelSerializer):
    class Meta:
        model = Variable
        fields = '__all__'


class WeatherStationSerializer(serializers.ModelSerializer):
    class Meta:
        model = WeatherStation
        fields = '__all__'


# =========================================================
# SERIALIZERS DE DONNÉES MÉTÉO
# =========================================================

class WeatherHourlySerializer(serializers.ModelSerializer):
    class Meta:
        model = WeatherHourly
        fields = '__all__'


class WeatherDailySerializer(serializers.ModelSerializer):
    class Meta:
        model = WeatherDaily
        fields = '__all__'


class WeatherReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = WeatherReport
        fields = '__all__'


class AlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alert
        fields = '__all__'