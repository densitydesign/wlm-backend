from main.models import Monument, Picture
from rest_framework import serializers
from rest_framework_gis.serializers import GeometryField, GeoFeatureModelSerializer, GeometrySerializerMethodField
from django.db import models
import json

class MonumentAppListSerialier(serializers.ModelSerializer):
    municipality_label = serializers.CharField(source="municipality.name", read_only=True)
    app_category = serializers.SerializerMethodField()  
    distance = serializers.FloatField(read_only=True, required=False, source="distance.km")

    def get_app_category(self, obj):
        category = obj.categories.first()
        if category:
            app_cat = category.app_category
            return getattr(app_cat, "name", None)

    

    class Meta:
        model = Monument
        fields = ['id', 'label', 'municipality_label', 'municipality', 'pictures_wlm_count', 'in_contest', "app_category", "distance"]


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

    def get_pictures(self, obj):
        pictures = obj.pictures.filter(image_type="wlm")
        return PictureSerializer(pictures, many=True).data
    
    def get_cover_picture(self, obj):
        picture = obj.pictures.first()
        if picture:
            return PictureSerializer(picture).data

    def get_app_category(self, obj):
        category = obj.categories.first()
        if category:
            app_cat = category.app_category
            return getattr(app_cat, "name", None)

    def get_counts_comune_by_app_category(self, obj):
        category = obj.categories.first()
        if category:
            app_cat = category.app_category
            app_category = getattr(app_cat, "name", None)
            if app_category == 'Comune':
                monuments_by_category = Monument.objects.filter(municipality=obj.municipality).values(
                    'categories__app_category__name').annotate(
                    count=models.Count('categories__app_category__name')).order_by('categories__app_category__name')
                return monuments_by_category
            else:
                return None
        else:
            return None
            
        
    
    class Meta:
        model = Monument
        fields = "__all__"


class ClusterSerializer(serializers.Serializer):
    position = serializers.SerializerMethodField()

    #count = serializers.IntegerField()
    #ids = serializers.ListField(child=serializers.IntegerField())
    ids = serializers.IntegerField()
    cid = serializers.IntegerField()

    def get_position(self, obj):
        return json.loads(obj["position"])


class ClusterGeoSerializer(serializers.Serializer):
    position = GeometryField()
    properties = serializers.DictField(required=False)

    #count = serializers.IntegerField()
    ids = serializers.ListField(child=serializers.IntegerField())
    cid = serializers.IntegerField()

