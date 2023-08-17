import json
from pathlib import Path
import requests
from django.core.cache import cache
from django.conf import settings
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.contrib.gis.db import models
from django_filters import rest_framework as filters
from main.models import AppCategory, Monument, Picture, Snapshot, Contest
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import APIException
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from oauth.models import OAuth2Token
from oauth.views import oauth
from .serializers import (
    MonumentAppDetailSerialier,
    MonumentAppDetailNoContestSerialier,
    MonumentAppListSerializer,
    MonumentAppListNoContestSerializer,
    UploadImagesSerializer,
    ContestSerializer,
)
from django.utils import timezone
from uuid import uuid4
from urllib.parse import urlparse, parse_qs
from .helpers import get_upload_categories


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 100
    page_size_query_param = "page_size"
    max_page_size = 1000


class MonumentFilter(filters.FilterSet):
    only_without_pictures = filters.BooleanFilter(label="only_without_pictures", method="filter_only_without_pictures")
    in_contest = filters.BooleanFilter(label="in_contest", method="filter_in_contest")
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
            return queryset.filter(pictures_count=0)
        else:
            return queryset

    def filter_in_contest(self, queryset, name, value):
        active_contests = Contest.get_active()
        if active_contests:
            if value:
                return queryset.filter(in_contest=True)
            else:
                return queryset.filter(in_contest=False)
        else:
            if value:
                return queryset.none()
            return queryset

    class Meta:
        model = Monument
        fields = ["municipality", "pictures_count"]


class MonumentAppViewSet(viewsets.ReadOnlyModelViewSet):
    """ """

    queryset = Monument.objects.all().select_related("municipality")
    serializer_class = MonumentAppListSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [
        filters.DjangoFilterBackend,
        OrderingFilter,
        SearchFilter,
    ]
    ordering_fields = ["label", "pictures_count"]
    search_fields = ["label", "municipality__name", "q_number"]
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
        active_contests = Contest.get_active()
        if active_contests:
            if self.action == "retrieve":
                return MonumentAppDetailSerialier
            return MonumentAppListSerializer

        else:
            if self.action == "retrieve":
                return MonumentAppDetailNoContestSerialier
            return MonumentAppListNoContestSerializer

    @action(detail=True, methods=["get"], url_path="upload-categories")
    def upload_categories(self, request, pk=None):
        monument = self.get_object()
        return Response(get_upload_categories(monument.q_number))


def dictfetchall(cursor):
    """
    Return all rows from a cursor as a dict.
    Assume the column names are unique.
    """
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def meters_to_degrees(meters):
    return float(meters / 1000) * (1.0 / 111.0)


def clusters_to_feature_collection(clusters):
    features = []
    for cluster in clusters:
        properties = {"ids": cluster["ids"]}
        if "properties" in cluster and cluster["properties"]:
            properties.update(json.loads(cluster["properties"]))

        features.append(
            {
                "type": "Feature",
                "geometry": json.loads(cluster["position"]),
                "properties": properties,
            }
        )
    return {"type": "FeatureCollection", "features": features}


def get_eps_for_resolution(res):
    if res > 3000:
        x = 4500
    if res > 1000:
        x = 4000
    elif res > 500:
        x = 4000
    else:
        x = 50
    out = meters_to_degrees(float(x))
    return 0


def qs_to_featurecollection(qs):
    out = {"type": "FeatureCollection", "features": []}
    for row in qs:
        if row["position"]:
            geom = json.loads(row["position"])
        else:
            print(row)
            continue
            geom = None

        out["features"].append(
            {
                "type": "Feature",
                "geometry": geom,
                "properties": {
                    "ids": row["ids"],
                    # "name": row["name"]
                },
            }
        )
    return out


class CategoriesDomainApi(APIView):
    def get(self, request):
        """ """
        app_category_with_categories = AppCategory.objects.filter(categories__isnull=False).distinct()
        data = []
        for app_category in app_category_with_categories:
            data.append(
                {
                    "name": app_category.name,
                    "categories": [category.pk for category in app_category.categories.all()],
                }
            )
        return Response(data)


# NOTE: AT THE MOMENT CLUSTERING IS DISABLED
# TODO: simplify query


class ClusterMonumentsApi(APIView):
    # todo: cache
    def get(self, request):
        """ """
        from django.db import connection

        bbox = request.query_params.get("bbox", None)
        bbox = bbox.split(",")
        if len(bbox) != 4:
            raise APIException("bbox must be a comma separated list of 4 numbers")

        bbox_condition = f"WHERE position && ST_MakeEnvelope({bbox[0]}, {bbox[1]}, {bbox[2]}, {bbox[3]}, 4326)"

        resolution = request.query_params.get("resolution", None)
        # print(resolution)
        if not resolution:
            raise APIException("resolution is required")

        municipality = request.query_params.get("municipality", None)
        only_without_pictures = request.query_params.get("only_without_pictures", None)
        in_contest = request.query_params.get("in_contest", None)
        category = request.query_params.get("category", None)


        active_contests = Contest.get_active()



        if float(resolution) > 1000:
            # grouping by region
            # looking for cache first
            cache_key = None
            last_snapshot = Snapshot.objects.filter(complete=True).order_by("-created").first()
            if last_snapshot:
                cache_key = f"cluster_region_{last_snapshot.pk}_" + str(request.query_params)
                # look for cache
                cached = cache.get(cache_key)
                if cached:
                    return Response(cached)

            qs = (
                Monument.objects.filter(position__isnull=False)
                .select_related("region")
                .values("region__name", "region__pk")
            )

            if municipality:
                qs = qs.filter(municipality_id=municipality)
            if only_without_pictures:
                qs = qs.filter(pictures_count=0)
            if in_contest:
                if active_contests:
                    qs = qs.filter(in_contest=True)
                else:
                    qs = qs.none()
            if category:
                app_category = AppCategory.objects.get(name__iexact=category)
                if not app_category:
                    raise APIException("Invalid category")
                categories_pks = app_category.categories.values_list("pk", flat=True)
                qs = qs.filter(categories__pk__in=categories_pks)

            qs = qs.annotate(
                ids=models.Count("id"),
                position=models.functions.AsGeoJSON(models.functions.Transform("region__centroid", 3857)),
            ).values("ids", "position", "region__name")
            out = Response(qs_to_featurecollection(qs))
            # caching
            if cache_key:
                cache.set(cache_key, out.data, 60 * 60 * 24 * 30)
            return out

        if float(resolution) > 300:
            # grouping by province
            cache_key = None
            last_snapshot = Snapshot.objects.filter(complete=True).order_by("-created").first()
            if last_snapshot:
                cache_key = f"cluster_province_{last_snapshot.pk}_" + str(request.query_params)
                # look for cache
                cached = cache.get(cache_key)
                if cached:
                    return Response(cached)

            qs = (
                Monument.objects.filter(position__isnull=False)
                .select_related("province")
                .values("province__name", "province__pk")
            )

            if municipality:
                qs = qs.filter(municipality_id=municipality)
            if only_without_pictures:
                qs = qs.filter(pictures_count=0)
            if in_contest:
                if active_contests:
                    qs = qs.filter(in_contest=True)
                else:
                    qs = qs.none()
            if category:
                app_category = AppCategory.objects.get(name__iexact=category)
                if not app_category:
                    raise APIException("Invalid category")
                categories_pks = app_category.categories.values_list("pk", flat=True)
                qs = qs.filter(categories__pk__in=categories_pks)

            qs = qs.annotate(
                ids=models.Count("id"),
                position=models.functions.AsGeoJSON(models.functions.Transform("province__centroid", 3857)),
            ).values("ids", "position", "province__name")
            out = Response(qs_to_featurecollection(qs))
            # caching
            if cache_key:
                cache.set(cache_key, out.data, 60 * 60 * 24 * 30)
            return out

        # "fake" clustering
        eps = get_eps_for_resolution(float(resolution))

        filter_condition = ""
        if municipality:
            filter_condition += f" AND main_monument.municipality_id = {municipality}"
        if only_without_pictures:
            filter_condition += f" AND (pictures_count = 0 OR pictures_count IS NULL)"
        if in_contest:
            if active_contests:
                filter_condition += f" AND in_contest = True"
            else:
                filter_condition += f" AND False"
            
        if category:
            app_category = AppCategory.objects.get(name__iexact=category)
            if not app_category:
                raise APIException("Invalid category")
            categories_pks = app_category.categories.values_list("pk", flat=True)
            filter_condition += (
                f" AND main_monument_categories.category_id IN ({','.join([str(pk) for pk in categories_pks])})"
            )

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
                SELECT main_monument.id as id, ST_ClusterDBSCAN(position, eps := {eps}, minpoints := 4) over () AS cidx, position,
                jsonb_build_object(
                    'id', main_monument.id,
                    'categories',  array_agg(main_monument_categories.category_id),
                    'label', label, 
                    'in_contest', in_contest, 
                    'position', position,
                    'pictures_count', pictures_count,
                    'pictures_wlm_count', pictures_wlm_count) as properties 
                FROM main_monument JOIN main_monument_categories ON main_monument.id = main_monument_categories.monument_id
                {bbox_condition}
                {filter_condition}
                GROUP BY main_monument.id
            ) sq) sq2
            GROUP BY cid, properties
            """
        )
        rows = dictfetchall(cursor)
        out = clusters_to_feature_collection(rows)
        return Response(out)


class UploadImageView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        ser = UploadImagesSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        platform = ser.validated_data.get("platform", "desktop")

        user = request.user
        oauth_token = OAuth2Token.objects.get(user=user)
        username = user.username[4:]

        year = str(timezone.now().year)

        all_results = []
        did_fail = False

        for uploaded_image in ser.validated_data["images"]:
            title = uploaded_image["title"]
            image = uploaded_image["image"]
            description = uploaded_image["description"]
            date = uploaded_image["date"]
            date_text = date.strftime("%Y-%m-%d")
            monument_id = uploaded_image["monument_id"]
            monument = Monument.objects.get(pk=monument_id)
            ext = Path(image.name).suffix
            title = f"File:{title}{ext}"
            # TODO CHECK EXISTENCE
            # GRAB CSRF TOKEN
            csrf_res = oauth.mediawiki.get(
                settings.URL_ACTION_API,
                params={"action": "query", "meta": "tokens", "format": "json", "type": "csrf"},
                token=oauth_token.to_token(),
            )
            csrf_res.raise_for_status()
            csrf_token = csrf_res.json()["query"]["tokens"]["csrftoken"]
            # COMPUTE CATEGORIES
            wlm_categories = []
            non_wlm_categories = []

            try:
                categories = get_upload_categories(monument.q_number) or {}
            except Exception as e:
                categories = {}

            # uploadurl_wlm = urls.get("uploadurl", "")
            # uploadurl_nonwlm = urls.get("nonwlmuploadurl", "")
            # if uploadurl_wlm and "categories=" in uploadurl_wlm:
            #     parts = urlparse(uploadurl_wlm)
            #     queryparams = parse_qs(parts.query)
            #     wlm_categories = [f"[[Category:{cat}]]" for cat in queryparams["categories"][0].split("|")]
            # if uploadurl_nonwlm and "categories=" in uploadurl_nonwlm:
            #     parts = urlparse(uploadurl_wlm)
            #     queryparams = parse_qs(parts.query)
            #     non_wlm_categories = [f"[[Category:{cat}]]" for cat in queryparams["categories"][0].split("|")]
            wlm_categories = [f"[[Category:{cat}]]" for cat in categories.get("wlm_categories", [])]
            non_wlm_categories = [f"[[Category:{cat}]]" for cat in categories.get("non_wlm_categories", [])]

            # GENERATE TEXT
            text = "== {{int:filedesc}} ==\n"
            text += "{{Information\n"
            text += (
                "|description={{it|1=%s}}{{Monumento italiano|%s|anno=%s}}{{Load via app WLM.it|year=%s|source=%s}}\n"
                % (
                    description,
                    str(monument.wlm_n),
                    str(date.year),
                    year,
                    platform,
                )
            )
            text += "|date=%s\n" % (date_text,)
            text += "|source={{own}}\n"
            text += "|author=[[User:%s|%s]]\n" % (
                username,
                username,
            )
            text += "}}\n"
            text += "\n"
            text += "== {{int:license-header}} ==\n"
            text += "{{self|cc-by-sa-4.0}}\n"

            if monument.in_contest:
                text += "{{Wiki Loves Monuments %s|it}}" % (year,)
                if wlm_categories:
                    text += "\n"
                text += "\n".join(wlm_categories)
            else:
                text += "\n".join(non_wlm_categories)

            # MAKE UPLOAD REQUEST
            upload_res = oauth.mediawiki.post(
                settings.URL_ACTION_API,
                data={
                    "action": "upload",
                    "filename": title,
                    "text": text,
                    "ignorewarnings": True,
                    "format": "json",
                    "token": csrf_token,
                },
                files={"file": image},
                headers={"Authorization": f"Bearer {oauth_token.access_token}"},
                token=oauth_token.to_token(),
            )
            if upload_res.ok:
                upload_res_data = upload_res.json()
                if "error" in upload_res_data:
                    did_fail = True
                else:
                    Picture.objects.create(
                        monument=monument,
                        image_id=str(
                            uuid4()
                        ),  # la upload response non ritorna l'ID pagina, mettiamo un id casuale per il vincolo di unicità del DB, a meno di problemi
                        image_url=upload_res_data["upload"]["imageinfo"]["url"],
                        image_date=timezone.now(),
                        image_title=title,
                        image_type="wlm",
                        data={
                            "title": title,
                            "Artist": f'<a href="{settings.WIKIMEDIA_BASE_URL}/wiki/User:{username}" title="User:{username}">{username}</a>',
                            "ImageDescription": description,
                            "License": "cc-by-sa-4.0",
                            "source": "user-upload",
                        },
                    )
                all_results.append(upload_res_data)
            else:
                did_fail = True
                all_results.append({"error": upload_res.status_code, "message": upload_res.text})
        monument.pictures_wlm_count = Picture.objects.filter(monument=monument, image_type="wlm").count()
        monument.pictures_count = Picture.objects.filter(monument=monument).count()

        monument.save()
        if did_fail:
            return Response(status=418, data=all_results)
        else:
            return Response(status=200, data=all_results)


class PersonalContributionsView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        response = requests.post(
            settings.URL_ACTION_API,
            data={
                "action": "query",
                "format": "json",
                "prop": "imageinfo",
                "generator": "allimages",
                "gaiuser": request.user.username[4:],
                "gaisort": "timestamp",
                "gailimit": "15",
                "iiprop": "timestamp|user|url",
            },
        )
        response.raise_for_status()
        data = response.json()
        print(data)
        images = list(data["query"]["pages"].values())
        return Response(images)


class CurrentContestsView(APIView):
    def get(self, request, *args, **kwargs):
        now = timezone.now()
        active_contests = Contest.get_active()
        ser = ContestSerializer(active_contests, many=True)
        return Response(ser.data)
