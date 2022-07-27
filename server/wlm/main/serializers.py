from rest_framework import serializers
from main.models import (Region, Province, Municipality, Monument, MonumentAuthorization, Picture, Snapshot)


class RegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = "__all__"

class ProvinceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Province
        fields = "__all__"

class MunicipalitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Municipality
        fields = "__all__"


class MonumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Monument
        fields = "__all__"


class MonumentAuthorizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = MonumentAuthorization
        fields = "__all__" 


class PictureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Picture
        fields = "__all__"


class SnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Snapshot
        fields = "__all__"

    