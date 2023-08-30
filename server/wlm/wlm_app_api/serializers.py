import requests
from pathlib import Path
from main.models import Monument, Picture, Contest, AppCategory
from rest_framework import serializers
from rest_framework_gis.serializers import GeometryField, GeoFeatureModelSerializer
from django.db import models
from .helpers import get_upload_categories
import json


class MonumentAppListSerializer(serializers.ModelSerializer):
    municipality_label = serializers.CharField(source="municipality.name", read_only=True)
    app_category = serializers.SerializerMethodField()
    distance = serializers.FloatField(read_only=True, required=False, source="distance.km")

    def get_app_category(self, obj):
        out = (
            AppCategory.objects.filter(categories__in=obj.categories.all()).order_by("priority").values("name").first()
        )
        if out:
            return out["name"]
        return None

    class Meta:
        model = Monument
        fields = [
            "id",
            "label",
            "municipality_label",
            "municipality",
            "pictures_wlm_count",
            "pictures_count",
            "in_contest",
            "app_category",
            "distance",
            "address",
            "location",
            "position",
            "q_number",
        ]


class PictureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Picture
        fields = "__all__"


class MonumentAppDetailSerialier(serializers.ModelSerializer):
    pictures = serializers.SerializerMethodField()
    cover_picture = serializers.SerializerMethodField()
    app_category = serializers.SerializerMethodField()
    counts_comune_by_app_category = serializers.SerializerMethodField()
    municipality_label = serializers.CharField(source="municipality.name", read_only=True)
    province_label = serializers.CharField(source="municipality.province.name", read_only=True)
    distance = serializers.FloatField(read_only=True, required=False)
    categories_urls = serializers.SerializerMethodField()
    app_category = serializers.SerializerMethodField()

    def get_pictures(self, obj):
        pictures = obj.pictures.all().order_by("-image_date")
        return PictureSerializer(pictures, many=True).data

    def get_cover_picture(self, obj):
        picture = obj.pictures.first()
        if picture:
            return PictureSerializer(picture).data

    def get_app_category(self, obj):
        out = (
            AppCategory.objects.filter(categories__in=obj.categories.all()).order_by("priority").values("name").first()
        )
        if out:
            return out["name"]
        return None

    def get_counts_comune_by_app_category(self, obj):
        category = obj.categories.first()
        if category:
            app_cat = category.app_category
            app_category = getattr(app_cat, "name", None)
            if app_category == "Comune":
                monuments_by_category = (
                    Monument.objects.filter(municipality=obj.municipality)
                    .values("categories__app_category__name")
                    .annotate(count=models.Count("categories__app_category__name"))
                    .order_by("categories__app_category__name")
                )
                return monuments_by_category
            else:
                return None
        else:
            return None

    def get_categories_urls(self, obj):
        return get_upload_categories(obj.q_number)

    class Meta:
        model = Monument
        fields = "__all__"


class ClusterSerializer(serializers.Serializer):
    position = serializers.SerializerMethodField()

    ids = serializers.IntegerField()
    cid = serializers.IntegerField()

    def get_position(self, obj):
        return json.loads(obj["position"])


class ClusterGeoSerializer(serializers.Serializer):
    position = GeometryField()
    properties = serializers.DictField(required=False)

    ids = serializers.ListField(child=serializers.IntegerField())
    cid = serializers.IntegerField()


class UploadImageSerializer(serializers.Serializer):
    image = serializers.ImageField()
    title = serializers.CharField()
    description = serializers.CharField(required=False)
    date = serializers.DateField()
    monument_id = serializers.CharField()

    def validate_title(self, value):
        candidates = "/\;"
        for x in candidates:
            if x in value:
                raise serializers.ValidationError("Il titolo contiene caratteri non validi: " + x)
        return value
    
    def validate(self, attrs):
        out = super().validate(attrs)
        image = out["image"]
        title = out["title"]
        ext = Path(image.name).suffix
        title = f"File:{title}{ext}"

        url = f"https://commons.wikimedia.org/wiki/{title}"
        r = requests.get(url)
        if r.status_code == 200:
            raise serializers.ValidationError("Esiste già un file con questo nome su Wikimedia Commons")

        return out


class UploadImagesSerializer(serializers.Serializer):
    images = UploadImageSerializer(many=True)
    platform = serializers.CharField(required=False, default="desktop")


class ContestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contest
        fields = "__all__"


class MonumentGeoSerializer(GeoFeatureModelSerializer):
    ids = serializers.IntegerField(read_only=True)

    # pos = GeometryField(required=False)

    class Meta:
        model = Monument
        fields = "__all__"
        geo_field = "position"
