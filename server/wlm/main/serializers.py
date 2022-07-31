from rest_framework import serializers
from main.models import (Region, Province, Municipality, Monument, MonumentAuthorization, Picture)


class RegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        exclude = ["poly"]

class ProvinceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Province
        exclude = ["poly"]

class MunicipalitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Municipality
        exclude = ["poly"]


class MonumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Monument
        fields = "__all__"

class MonumentSmallSerializer(serializers.ModelSerializer):
    class Meta:
        model = Monument
        fields = ["id", "q_number", "label"]


class MonumentAuthorizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = MonumentAuthorization
        fields = "__all__" 


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
