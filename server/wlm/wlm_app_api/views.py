import json
from pathlib import Path
import requests
from django.core.cache import cache
from django.conf import settings
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point, Polygon
from django.contrib.gis.db import models
from django.contrib.postgres.aggregates import ArrayAgg
from django_filters import rest_framework as filters
from main.models import AppCategory, Monument, Picture, Snapshot, Contest, Category
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
    MonumentAppListSerializer,
    UploadImagesSerializer,
    ContestSerializer,
)
from django.utils import timezone
from uuid import uuid4
from .helpers import get_upload_categories


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 100
    page_size_query_param = "page_size"
    max_page_size = 1000


class MonumentFilter(filters.FilterSet):
    only_without_pictures = filters.BooleanFilter(label="only_without_pictures", method="filter_only_without_pictures")
    category = filters.CharFilter(method="filter_category")

    def filter_category(self, queryset, name, value):
        """
        Match only the first
        """
        if value:
            app_category = AppCategory.objects.get(name=value)
            if not app_category:
                return queryset.none()

            first_app_category = (
                Monument.categories.through.objects.filter(
                    monument_id=models.OuterRef("pk"),
                )
                .order_by("category__app_category__priority")
                .values("category_id")[:1]
            )

            categories = Category.objects.filter(app_category=app_category).values_list("pk", flat=True)

            return queryset.annotate(first_app_category=models.Subquery(first_app_category)).filter(
                first_app_category__in=categories
            )

        return queryset

    def filter_only_without_pictures(self, queryset, name, value):
        if value:
            return queryset.filter(pictures_count=0)
        else:
            return queryset

    class Meta:
        model = Monument
        fields = ["municipality", "pictures_count", "in_contest"]


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
    search_fields = ["label", "municipality__name", "q_number", "wlm_n"]
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

        return qs.distinct()

    def get_serializer_class(self):
        if self.action == "retrieve":
            return MonumentAppDetailSerialier
        return MonumentAppListSerializer
            

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


def qs_to_featurecollection(qs, name=""):
    out = {"type": "FeatureCollection", "features": [], "name": name}
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
                    "cluster": row["cluster"],
                },
            }
        )
    return out


def qs_to_featurecollection_flat(qs):
    out = {"type": "FeatureCollection", "features": []}

    categories = Category.objects.all().select_related("app_category")
    categories_by_id = {category.pk: category for category in categories}



    
    for row in qs:
        
        if row["pos"]:

            
            geom = json.loads(row["pos"])
            data = {x: row[x] for x in row if x != "pos"}
            
            data_add = {}
            remove_keys = []
            for d in data:
                if d.endswith("_"):
                    data_add[d[:-1]] = data[d]
                    remove_keys.append(d)

            for k in remove_keys:
                del data[k]
            data.update(data_add)
            if "position" in data:
                data["position"] = json.loads(data["position"])

            if data["categories"]:
                if not data["categories_priorities"]:
                    data["app_category"]  = None
                else:
                    priorities = [x for x in data["categories_priorities"]] 
                    for i, x in enumerate(priorities):
                        if x is None:
                            priorities[i] = 999
                    
                    min_priority = min(priorities)
                    if min_priority == 999:
                        data["app_category"] = "Altri monumenti"
                    else:
                        min_priority_index = data["categories_priorities"].index(min_priority)
                        category_id = data["categories"][min_priority_index]
                        data["app_category"] = categories_by_id[category_id].app_category.name
                
        else:
            print(row)
            continue
            geom = None

        out["features"].append({"type": "Feature", "geometry": geom, "properties": data})
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

        resolution = request.query_params.get("resolution", None)
        # print(resolution)
        if not resolution:
            raise APIException("resolution is required")

        municipality = request.query_params.get("municipality", None)
        only_without_pictures = request.query_params.get("only_without_pictures", None)
        in_contest = request.query_params.get("in_contest", None)
        category = request.query_params.get("category", None)
        
        qs = Monument.objects.filter(position__isnull=False)

        if municipality:
            qs = qs.filter(municipality_id=municipality)
        if only_without_pictures:
            qs = qs.filter(pictures_count=0)
        if in_contest:
            qs = qs.filter(in_contest=True)

        if category:
            app_category = AppCategory.objects.get(name__iexact=category)
            if not app_category:
                raise APIException("Invalid category")

            first_app_category = (
                Monument.categories.through.objects.filter(
                    monument_id=models.OuterRef("pk"),
                )
                .order_by("category__app_category__priority")
                .values("category_id")[:1]
            )

            categories = Category.objects.filter(app_category=app_category).values_list("pk", flat=True)
            qs = qs.annotate(first_app_category=models.Subquery(first_app_category)).filter(
                first_app_category__in=categories
            )

        if float(resolution) > 1000:
            # grouping by region
            # looking for cache first
            cache_key = None
            last_snapshot = Snapshot.objects.filter(complete=True).order_by("-created").first()
            if last_snapshot:
                cache_key = f"cluster_region_{last_snapshot.pk}_" + str(request.query_params)
                #look for cache
                cached = cache.get(cache_key)
                if cached:
                    return Response(cached)

            qs = qs.select_related("region").values("region__name", "region__pk")

            qs = qs.annotate(
                ids=models.Count("id"),
                cluster=models.F("region__name"),
                position=models.functions.AsGeoJSON(models.functions.Transform("region__centroid", 3857)),
            ).values("ids", "position", "cluster")

            out = Response(qs_to_featurecollection(qs, "region"))
            

            #caching
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

            qs = qs.select_related("province").values("province__name", "province__pk")

            qs = qs.annotate(
                ids=models.Count("id"),
                cluster=models.F("province__name"),
                position=models.functions.AsGeoJSON(models.functions.Transform("province__centroid", 3857)),
            ).values("ids", "position", "cluster")

            out = Response(qs_to_featurecollection(qs, "province"))
            #caching
            if cache_key:
                cache.set(cache_key, out.data, 60 * 60 * 24 * 30)
            return out

        bbox = Polygon.from_bbox(bbox)
        
        qs = qs.filter(
            position__within=bbox,
        )

        qs = qs.annotate(
            ids=models.Value(1, output_field=models.IntegerField()),
            pos=models.functions.AsGeoJSON(models.functions.Transform("position", 3857)),
            categories_=ArrayAgg("categories__pk", order_by='categories__pk'),
            categories_priorities=ArrayAgg("categories__app_category__priority", order_by='categories__pk'),
            position_=models.functions.AsGeoJSON('position'),
        ).values(
            "ids",
            "pos",
            "label",
            "categories_",
            "id",
            "in_contest",
            "pictures_count",
            "pictures_wlm_count",
            "position_",
            "categories_priorities",
            
        )

        out = Response(qs_to_featurecollection_flat(qs))
        return out


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

        active_contests = Contest.get_active()


        try:
            csrf_res = oauth.mediawiki.get(
                settings.URL_ACTION_API,
                params={"action": "query", "meta": "tokens", "format": "json", "type": "csrf"},
                token=oauth_token.to_token(),
            )
            csrf_res.raise_for_status()
            csrf_token = csrf_res.json()["query"]["tokens"]["csrftoken"]
        except Exception as e:
            raise APIException("Errore di autenticazione: riprova ad effettuare il login")

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
            
            if monument.in_contest and active_contests:
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
            else:
                text += (
                    "|description={{it|1=%s}}{{Load via app WLM.it|year=%s|source=%s}}\n"
                    % (
                        description,
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

            if monument.in_contest and active_contests:
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
        images = list(data["query"]["pages"].values())
        return Response(images)


class CurrentContestsView(APIView):
    def get(self, request, *args, **kwargs):
        active_contests = Contest.get_active()
        ser = ContestSerializer(active_contests, many=True)
        return Response(ser.data)
