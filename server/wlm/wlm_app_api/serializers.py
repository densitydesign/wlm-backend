from main.models import Monument, Picture
from rest_framework import serializers


class MonumentAppListSerialier(serializers.ModelSerializer):
    municipality_label = serializers.CharField(source="municipality.name", read_only=True)
    app_category = serializers.SerializerMethodField()  

    def get_app_category(self, obj):
        category = obj.categories.first()
        if category:
            app_cat = category.app_category
            return getattr(app_cat, "name", None)

    

    class Meta:
        model = Monument
        fields = ['id', 'label', 'municipality_label', 'municipality', 'pictures_wlm_count', 'in_contest', "app_category"]


class PictureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Picture
        fields = "__all__"



class MonumentAppDetailSerialier(serializers.ModelSerializer):
    
    pictures = serializers.SerializerMethodField()
    cover_picture = serializers.SerializerMethodField()
    app_category = serializers.SerializerMethodField()  

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
        
    
    class Meta:
        model = Monument
        fields = "__all__"







