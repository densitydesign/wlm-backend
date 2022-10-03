from asyncore import read
from rest_framework import serializers
from main.models import Region, Province, Municipality, Monument, Picture, Category
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


class PictureSerializer(serializers.ModelSerializer):

    wlm_image = serializers.SerializerMethodField()
    relevant_image = serializers.SerializerMethodField()

    def get_wlm_image(self, obj):
        return obj.image_type == "wlm"
    
    def get_relevant_image(self, obj):
        return obj.image_type == "commons"
    class Meta:
        model = Picture
        fields = ["id", "image_id", "image_url", "image_date", "image_title", "wlm_image", "relevant_image"]


class MonumentSerializer(serializers.ModelSerializer):
    pictures = PictureSerializer(many=True, read_only=True)
    wlm_id = serializers.CharField(source="wlm_n")
    wlm_auth_start_date = serializers.DateTimeField(source="start")
    wlm_auth_end_date = serializers.DateTimeField(source="end")
    wikidata_creation_date = serializers.DateTimeField(source="first_revision")
    first_wlm_image_date = serializers.DateField(source="first_image_date")
    first_commons_image_date = serializers.DateField(source="first_image_date_commons")

    municipality_label = serializers.CharField(source="municipality.name", read_only=True)
    province_label = serializers.CharField(source="province.name", read_only=True)
    region_label = serializers.CharField(source="region.name", read_only=True)

    class Meta:
        model = Monument
        fields = [
            "id",
            "pictures",
            "label",
            "q_number",
            "wlm_id",
            "wlm_auth_start_date",
            "wlm_auth_end_date",
            "position",
            "wikidata_creation_date",
            "first_wlm_image_date",
            "first_commons_image_date",
            "municipality",
            "province",
            "region",
            "categories",
            "snapshot",
            "municipality_label",
            "province_label",
            "region_label",
        ]


class MonumentSmallSerializer(serializers.ModelSerializer):
    class Meta:
        model = Monument
        fields = "__all__"
        # fields = ["id", "q_number", "label"]


class WLMQuerySerializer(serializers.Serializer):
    date_from = serializers.DateField()
    date_to = serializers.DateField()
    step_size = serializers.IntegerField(default=1)
    step_unit = serializers.CharField(default="months")
    theme = serializers.CharField(required=False)
