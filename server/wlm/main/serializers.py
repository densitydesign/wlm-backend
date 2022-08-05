from rest_framework import serializers
from main.models import (Region, Province, Municipality, Monument,  Picture)
from rest_framework_gis.serializers import GeometryField, GeoFeatureModelSerializer


class RegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        exclude = ["poly"]


class RegionGeoSerializer(GeoFeatureModelSerializer):

    poly = GeometryField()

    class Meta:
        model = Region
        fields = ["name", "code", "centroid"]
        geo_field = "poly"
        id_field = False
        

class ProvinceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Province
        exclude = ["poly"]

class ProvinceGeoSerializer(GeoFeatureModelSerializer):

    poly = GeometryField()

    class Meta:
        model = Province
        fields = ["name", "code", "centroid"]
        geo_field = "poly"
        id_field = False


class MunicipalitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Municipality
        exclude = ["poly"]


class MunicipalityGeoSerializer(GeoFeatureModelSerializer):

    poly = GeometryField()

    class Meta:
        model = Municipality
        fields = ["name", "code", "centroid"]
        geo_field = "poly"
        id_field = False


class MonumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Monument
        fields = "__all__"

class MonumentSmallSerializer(serializers.ModelSerializer):
    class Meta:
        model = Monument
        fields = ["id", "q_number", "label"]


class PictureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Picture
        fields = "__all__"


class WLMQuerySerializer(serializers.Serializer):
    date_from = serializers.DateField()
    date_to = serializers.DateField()
    step_size = serializers.IntegerField(default=1)
    step_unit = serializers.CharField(default='months')
    monuments = serializers.BooleanField(default=False)
