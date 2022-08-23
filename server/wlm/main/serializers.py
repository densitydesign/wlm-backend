from asyncore import read
from rest_framework import serializers
from main.models import (Region, Province, Municipality, Monument,  Picture, Category)
from rest_framework_gis.serializers import GeometryField, GeoFeatureModelSerializer


class CategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = Category
        fields = "__all__"


class RegionSerializer(serializers.ModelSerializer):

    label = serializers.CharField(source="name", read_only=True)
    class Meta:
        model = Region
        exclude = ["poly"]


class RegionGeoSerializer(GeoFeatureModelSerializer):

    poly = GeometryField()
    label = serializers.CharField(source="name", read_only=True)

    class Meta:
        model = Region
        fields = ["name", "code", "centroid", "label"]
        geo_field = "poly"
        id_field = False
        

class ProvinceSerializer(serializers.ModelSerializer):

    label = serializers.CharField(source="name", read_only=True)
    class Meta:
        model = Province
        exclude = ["poly"]

class ProvinceGeoSerializer(GeoFeatureModelSerializer):

    poly = GeometryField()
    label = serializers.CharField(source="name", read_only=True)

    class Meta:
        model = Province
        fields = ["name", "code", "centroid", "label"]
        geo_field = "poly"
        id_field = False


class MunicipalitySerializer(serializers.ModelSerializer):

    label = serializers.CharField(source="name", read_only=True)
    class Meta:
        model = Municipality
        exclude = ["poly"]


class MunicipalityGeoSerializer(GeoFeatureModelSerializer):

    poly = GeometryField()
    label = serializers.CharField(source="name", read_only=True)

    class Meta:
        model = Municipality
        fields = ["name", "code", "centroid", "label"]
        geo_field = "poly"
        id_field = False


class MonumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Monument
        fields = "__all__"

class MonumentSmallSerializer(serializers.ModelSerializer):
    class Meta:
        model = Monument
        fields = "__all__"
        #fields = ["id", "q_number", "label"]


class PictureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Picture
        fields = "__all__"


class WLMQuerySerializer(serializers.Serializer):
    date_from = serializers.DateField()
    date_to = serializers.DateField()
    step_size = serializers.IntegerField(default=1)
    step_unit = serializers.CharField(default='months')
    theme = serializers.CharField(required=False)
