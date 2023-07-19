from rest_framework import viewsets
from rest_framework.views import APIView
from django.contrib.gis.geos import Point
from rest_framework.exceptions import APIException
from django.db import models
from .serializers import MonumentAppListSerialier, MonumentAppDetailSerialier, ClusterSerializer
from main.models import Monument, Picture, AppCategory, Category
from rest_framework.pagination import PageNumberPagination
from django_filters import rest_framework as filters
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.gis.db.models.functions import Distance


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 100
    page_size_query_param = "page_size"
    max_page_size = 1000


class MonumentFilter(filters.FilterSet):
    only_without_pictures = filters.BooleanFilter(label="only_without_pictures", method="filter_only_without_pictures")
    category = filters.CharFilter(method="filter_category")

    def filter_category(self, queryset, name, value):
        if value:
            app_category = AppCategory.objects.get(name=value)
            if not app_category:
                return queryset.none()
            categories_pks = app_category.categories.values_list("pk", flat=True)
            return queryset.filter(categories__pk__in=categories_pks)
        return queryset

    def filter_only_without_pictures(self, queryset, name, value):
        if value:
            return queryset.filter(pictures_wlm_count=0)
        else:
            return queryset

    class Meta:
        model = Monument
        fields = ["municipality", "pictures_wlm_count", "in_contest"]


class MonumentAppViewSet(viewsets.ReadOnlyModelViewSet):
    """ """

    queryset = Monument.objects.all().select_related("municipality")
    serializer_class = MonumentAppListSerialier
    pagination_class = StandardResultsSetPagination
    filter_backends = [
        filters.DjangoFilterBackend,
        OrderingFilter,
        SearchFilter,
    ]
    ordering_fields = ["label", "pictures_wlm_count"]
    search_fields = ["label", "municipality__name"]
    filterset_class = MonumentFilter

    def get_queryset(self):
        qs = super().get_queryset()

        user_lat = self.request.query_params.get("user_lat", None)
        user_lon = self.request.query_params.get("user_lon", None)
        if user_lat and user_lon:
            point = Point(float(user_lon), float(user_lat), srid=4326)
            qs = qs.annotate(distance=Distance("position", point))

        if self.request.query_params.get("ordering", None) in ["distance"]:
            if not user_lat or not user_lon:
                raise APIException("user_lat and user_lon are required when ordering by distance")
            qs = qs.order_by("distance")

        return qs

    def get_serializer_class(self):
        if self.action == "retrieve":
            return MonumentAppDetailSerialier
        return super().get_serializer_class()


def dictfetchall(cursor):
    """
    Return all rows from a cursor as a dict.
    Assume the column names are unique.
    """
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]

def meters_to_degrees(meters):
    return float(meters  / 1000)  * (1.0 / 111.0)


def clusters_to_feature_collection(clusters):
    features = []
    for cluster in clusters:
        properties = {
            "ids": cluster["ids"]
        }
        if "properties" in cluster and cluster["properties"]:
            properties.update(cluster["properties"])

        features.append(
            {
                "type": "Feature",
                "geometry": cluster["position"],
                "properties": properties,
            }
        )
    return {"type": "FeatureCollection", "features": features}


def get_eps_for_resolution(res):
    # if res > 4000:
    #     x = 5000
    # elif res > 3000:
    #     x = 6000
    # elif res > 2000:
    #     x = 4000
    # elif res > 1000:
    #     x  = 2500
    # else:
    #     x = 1500
    if res > 1000:
        x = 2400
    elif res > 500:
        x = 1200
    else:
        x = 40
    out = meters_to_degrees(float(x))
    return out


class ClusterMonumentsApi(APIView):
    def get(self, request):
        """
                
        """
        from django.db import connection
        
        bbox = request.query_params.get("bbox", None)
        bbox = bbox.split(",")
        if len(bbox) != 4:
            raise APIException("bbox must be a comma separated list of 4 numbers")

        bbox_condition = f"WHERE position && ST_MakeEnvelope({bbox[0]}, {bbox[1]}, {bbox[2]}, {bbox[3]}, 4326)"

        resolution = request.query_params.get("resolution", None)
        if not resolution:
            raise APIException("resolution is required")
        
        print(resolution)
        eps = get_eps_for_resolution(float(resolution))
        print("eps", eps)

    

        cursor = connection.cursor()
        cursor.execute(
            f"""
            SELECT 
                cid,
                properties,
                ST_AsGeoJSON(
                    ST_Transform(
                        ST_Centroid(ST_Collect(position)),
                        'EPSG:4326',
                        'EPSG:3857'
                    )
                ) AS position, 
                count(id) AS ids 

            FROM (
                SELECT 
                    id, position,
                    CASE WHEN cidx IS NOT NULL THEN cidx ELSE id END AS cid, 
                    CASE WHEN cidx IS NOT NULL THEN null ELSE properties END AS properties

                
            FROM (
                SELECT id, ST_ClusterDBSCAN(position, eps := {eps}, minpoints := 4) over () AS cidx, position,
                jsonb_build_object('label', label) as properties 
                FROM main_monument
                {bbox_condition}
            ) sq) sq2
            GROUP BY cid, properties
            """
        )
        rows = dictfetchall(cursor)
        print(rows[-1])
        ser = ClusterSerializer(rows, many=True)
        out = clusters_to_feature_collection(ser.data)
        return Response(out)

        
