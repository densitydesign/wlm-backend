from django.core.cache import cache
from django.http import HttpResponseRedirect
from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.response import Response
from main.models import (Region, Province, Municipality, Monument, Picture, Category, Snapshot)
from main.serializers import (RegionSerializer, RegionGeoSerializer,
     ProvinceSerializer, MunicipalitySerializer, MonumentSerializer, 
     MonumentSmallSerializer,  PictureSerializer, 
     CategorySerializer,ProvinceGeoSerializer, MunicipalityGeoSerializer,
     WLMQuerySerializer,)
from main.helpers import get_snap, format_history
from drf_spectacular.utils import extend_schema
from rest_framework.pagination import PageNumberPagination
from django_filters import rest_framework as filters
from django.db import models
from django.utils.decorators import method_decorator
from django.views.decorators.http import condition
from django.views.decorators.cache import cache_control, cache_page
from django.conf import settings
from rest_framework.exceptions import NotFound



def get_last_import(request, **kwargs):
    """
    Last-modified logic computation
    """
    if not getattr(settings, 'HTTP_CONDITIONAL_CACHE', False):
        return None
    
    agg = Snapshot.objects.aggregate(last_import=models.Max("created"))
    return agg["last_import"]
    

def get_history(monuments_qs, query_params, group=None, mode='wlm'):
    ser = WLMQuerySerializer(data=query_params)
    ser.is_valid(raise_exception=True)
    
    date_from = ser.validated_data["date_from"]
    date_to = ser.validated_data["date_to"]
    step_size = ser.validated_data["step_size"]
    step_unit = ser.validated_data["step_unit"]

    theme = ser.validated_data.get("theme", None)
    if theme:
        monuments_qs = monuments_qs.filter(categories__pk=theme)
    
    history = get_snap(monuments_qs, date_from, date_to, step_size=step_size, step_unit=step_unit, group=group, mode=mode)
    return history, ser.validated_data


@method_decorator(condition(last_modified_func=get_last_import), name="dispatch")
@method_decorator(cache_control(max_age=0, public=True), name="dispatch")
@method_decorator(cache_page(None, cache="views"), name="dispatch")
class DomainView(APIView):
    def get(self, request):
        categories = Category.objects.all()
        cat_serializer = CategorySerializer(categories, many=True)
        try:
            last_snapshot = Snapshot.objects.filter(complete=True).latest('created')
        except Snapshot.DoesNotExist:
            last_snapshot = None
            
        if last_snapshot is not None:
            last_date = last_snapshot.created.date()
        else:
            last_date = None

        full_xlsx_url = None
        if last_snapshot is not None and last_snapshot.xlsx_export:
            full_xlsx_url = last_snapshot.xlsx_export.url
        
        full_csv_url = None
        if last_snapshot is not None and last_snapshot.csv_export:
            full_csv_url = last_snapshot.csv_export.url
        
        return Response({"themes" : cat_serializer.data, "last_snapshot": last_date, "full_xlsx_url": full_xlsx_url, "full_csv_url": full_csv_url})



@method_decorator(condition(last_modified_func=get_last_import), name="dispatch")
@method_decorator(cache_control(max_age=0, public=True), name="dispatch")
@method_decorator(cache_page(None, cache="views"), name="dispatch")
class RegionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Region.objects.all()
    serializer_class = RegionSerializer

    @extend_schema(responses={200: RegionGeoSerializer})
    @action(methods=["get"], detail=False)
    def geo(self, request):
        """
        GeoJSON representation of the regions
        """
        cached = cache.get("region_geo")
        if cached:
            return Response(cached)
        queryset = self.get_queryset()
        ser = RegionGeoSerializer(queryset, many=True)
        return Response(ser.data)


    @extend_schema(responses={200: ProvinceGeoSerializer(many=True)})
    @action(methods=["get"], detail=True)
    def areas(self, request, pk=None):
        region = self.get_object()
        cached = cache.get(f"region_geo/{region.code}")
        if cached:
            return Response(cached)
        ser = ProvinceGeoSerializer(region.provinces.all(), many=True)
        return Response(ser.data)   

    @extend_schema(parameters=[WLMQuerySerializer])
    @action(methods=["get"], detail=False, url_path="wlm-aggregate")
    def wlm_aggregate(self, request, pk=None):
        monuments_qs = Monument.objects.all()
        history, validated_data = get_history(monuments_qs, request.query_params, group=['national', 'national_name'])
        return Response(history)

    @extend_schema(parameters=[WLMQuerySerializer])
    @action(methods=["get"], detail=False, url_path="commons-aggregate")
    def commons_aggregate(self, request, pk=None):
        monuments_qs = Monument.objects.all()
        history, validated_data = get_history(monuments_qs, request.query_params, group=['national', 'national_name'], mode='commons')
        return Response(history)


    @extend_schema(parameters=[WLMQuerySerializer])
    @action(methods=["get"], detail=False, url_path="wlm-regions")
    def wlm_regions(self, request, pk=None):
        monuments_qs = Monument.objects.all()
        history, validated_data = get_history(monuments_qs, request.query_params, group=['region', 'region__name'])
        return Response(history)

    @extend_schema(parameters=[WLMQuerySerializer])
    @action(methods=["get"], detail=False, url_path="commons-regions")
    def commons_regions(self, request, pk=None):
        monuments_qs = Monument.objects.all()
        history, validated_data = get_history(monuments_qs, request.query_params, group=['region', 'region__name'], mode='commons')
        return Response(history)
        
    @extend_schema(parameters=[WLMQuerySerializer])
    @action(methods=["get"], detail=True)
    def wlm(self, request, pk=None):
        area = self.get_object()
        monuments_qs = area.monuments.all()
        history, validated_data = get_history(monuments_qs, request.query_params, group=['region', 'region__name'])
        return Response(history)

    @extend_schema(parameters=[WLMQuerySerializer])
    @action(methods=["get"], detail=True)
    def commons(self, request, pk=None):
        area = self.get_object()
        monuments_qs = area.monuments.all()
        history, validated_data = get_history(monuments_qs, request.query_params, group=['region', 'region__name'], mode='commons')
        return Response(history)

    @extend_schema(parameters=[WLMQuerySerializer])
    @action(methods=["get"], detail=True, url_path='wlm-areas')
    def wlm_areas(self, request, pk=None):
        area = self.get_object()
        monuments_qs = area.monuments.all()
        history, validated_data = get_history(monuments_qs, request.query_params, group=['province', 'province__name'])
        return Response(history)

    @extend_schema(parameters=[WLMQuerySerializer])
    @action(methods=["get"], detail=True, url_path='commons-areas')
    def commons_areas(self, request, pk=None):
        area = self.get_object()
        monuments_qs = area.monuments.all()
        history, validated_data = get_history(monuments_qs, request.query_params, group=['province', 'province__name'], mode='commons')
        return Response(history)

    # @action(methods=["get"], detail=True)
    # def monuments(self, request, pk=None):
    #     area = self.get_object()
    #     monuments_qs = area.monuments.all()
    #     return Response(MonumentSmallSerializer(monuments_qs, many=True).data)


@method_decorator(condition(last_modified_func=get_last_import), name="dispatch")
@method_decorator(cache_control(max_age=0, public=True), name="dispatch")
@method_decorator(cache_page(None, cache="views"), name="dispatch")
class ProvinceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Province.objects.all()
    serializer_class = ProvinceSerializer

    @extend_schema(responses={200: ProvinceGeoSerializer})
    @action(methods=["get"], detail=False)
    def geo(self, request):
        cached = cache.get(f"province_geo")
        if cached:
            return Response(cached)
        queryset = self.get_queryset()
        ser = ProvinceGeoSerializer(queryset, many=True)
        return Response(ser.data)

    @extend_schema(responses={200: MunicipalityGeoSerializer(many=True)})
    @action(methods=["get"], detail=True)
    def areas(self, request, pk=None):
        province = self.get_object()
        cached = cache.get(f"province_geo/{province.code}")
        if cached:
            return Response(cached)
        ser = MunicipalityGeoSerializer(province.municipalities.all(), many=True)
        return Response(ser.data)   


    @extend_schema(parameters=[WLMQuerySerializer])
    @action(methods=["get"], detail=True)
    def wlm(self, request, pk=None):
        area = self.get_object()
        monuments_qs = area.monuments.all()
        history, validated_data = get_history(monuments_qs, request.query_params, group=['province', 'province__name'])
        return Response(history)

    @extend_schema(parameters=[WLMQuerySerializer])
    @action(methods=["get"], detail=True)
    def commons(self, request, pk=None):
        area = self.get_object()
        monuments_qs = area.monuments.all()
        history, validated_data = get_history(monuments_qs, request.query_params, group=['province', 'province__name'], mode='commons')
        return Response(history)

    @extend_schema(parameters=[WLMQuerySerializer])
    @action(methods=["get"], detail=True, url_path='wlm-areas')
    def wlm_areas(self, request, pk=None):
        area = self.get_object()
        monuments_qs = area.monuments.all()
        history, validated_data = get_history(monuments_qs, request.query_params, group=['municipality', 'municipality__name'])
        return Response(history)

    @extend_schema(parameters=[WLMQuerySerializer])
    @action(methods=["get"], detail=True, url_path='commons-areas')
    def commons_areas(self, request, pk=None):
        area = self.get_object()
        monuments_qs = area.monuments.all()
        history, validated_data = get_history(monuments_qs, request.query_params, group=['municipality', 'municipality__name'], mode='commons')
        return Response(history)
    

    # @action(methods=["get"], detail=True)
    # def monuments(self, request, pk=None):
    #     area = self.get_object()
    #     monuments_qs = area.monuments.all()
    #     return Response(MonumentSmallSerializer(monuments_qs, many=True).data)


@method_decorator(condition(last_modified_func=get_last_import), name="dispatch")
@method_decorator(cache_control(max_age=0, public=True), name="dispatch")
@method_decorator(cache_page(None, cache="views"), name="dispatch")
class MunicipalityViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Municipality.objects.all()
    serializer_class = MunicipalitySerializer
    pagination_class = PageNumberPagination
    page_size = 100

    @extend_schema(parameters=[WLMQuerySerializer])
    @action(methods=["get"], detail=True)
    def wlm(self, request, pk=None):
        area = self.get_object()
        monuments_qs = area.monuments.all()
        history, validated_data = get_history(monuments_qs, request.query_params, group=['municipality', 'municipality__name'])
        return Response(history)

    @extend_schema(parameters=[WLMQuerySerializer])
    @action(methods=["get"], detail=True)
    def commons(self, request, pk=None):
        area = self.get_object()
        monuments_qs = area.monuments.all()
        history, validated_data = get_history(monuments_qs, request.query_params, group=['municipality', 'municipality__name'], mode='commons')
        return Response(history)


    # @action(methods=["get"], detail=True)
    # def monuments(self, request, pk=None):
    #     area = self.get_object()
    #     monuments_qs = area.monuments.all()
    #     return Response(MonumentSmallSerializer(monuments_qs, many=True).data)


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 100
    page_size_query_param = 'page_size'
    max_page_size = 1000


class Y(filters.ModelChoiceFilter):
    def filter(self, qs, value):
        raise
        if value:
            return qs.filter(**{self.field_name: value})
        return qs

class MonumentFilter(filters.FilterSet):
    #photographed = filters.BooleanFilter(method='filter_photographed')
    #on_wiki = filters.BooleanFilter(method='filter_on_wiki')
    #in_contest = filters.BooleanFilter(method='filter_in_contest')
    theme = filters.CharFilter(method='filter_theme')
    region = filters.CharFilter(method='filter_region')
    province = filters.CharFilter(method='filter_province')
    municipality = filters.CharFilter(method='filter_municipality')

    def filter_region(self, qs, name, value):
        if(value=='0'):
            return qs.filter(region__isnull=True)
        return qs.filter(region__code=value)

    def filter_province(self, qs, name, value):
        if(value=='0'):
            return qs.filter(province__isnull=True)
        return qs.filter(province__code=value)

    def filter_municipality(self, qs, name, value):
        if(value=='0'):
            return qs.filter(municipality__isnull=True)
        return qs.filter(municipality__code=value)
    
    def filter_theme(self, queryset, name, value):
        return queryset.filter(categories__pk=value)

    ordering = filters.OrderingFilter(
        # tuple-mapping retains order
        fields=(
            ('wlm_n', 'wlm_id'),
            ('q_number', 'q_number'),
            ('label', 'label'),
            ('start', 'wlm_auth_start_date'),
            ('end', 'wlm_auth_end_date'),
            ('first_image_date', 'first_wlm_image_date'),
            ('first_image_date_commons', 'first_commons_image_date'),
            ('municipality_label', 'municipality__name'),
            ('province_label', 'province__name'),
            ('region_label', 'region__name'),
        ),
    )

  
    
    class Meta:
        model = Monument
        fields = ['region', 'province', 'municipality', 'theme']
        

@method_decorator(condition(last_modified_func=get_last_import), name="dispatch")
@method_decorator(cache_control(max_age=0, public=True), name="dispatch")
@method_decorator(cache_page(None, cache="views"), name="dispatch")
class MonumentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Monument.objects.all().select_related('region', 'province', 'municipality')
    serializer_class = MonumentSerializer
    pagination_class = StandardResultsSetPagination
    filterset_class = MonumentFilter

    @action(methods=["get"], detail=False, url_path="by-q/(?P<q>[^/.]+)")
    def byq(self, request, q=None):
        try:
            mon = Monument.objects.get(q_number=q)
        except:
            raise NotFound()
        return Response(MonumentSerializer(mon).data)


    @action(methods=["get"], detail=False)
    def csv(self, request):
        try:
            last_snapshot = Snapshot.objects.filter(complete=True).latest('created')
        except Snapshot.DoesNotExist:
            last_snapshot = None
        
        if last_snapshot is None or last_snapshot.csv_export is None:
            return Response(status=404)

        url = request.build_absolute_uri(last_snapshot.csv_export.url)
        return HttpResponseRedirect(url)

    @action(methods=["get"], detail=False)
    def xlsx(self, request):
        try:
            last_snapshot = Snapshot.objects.filter(complete=True).latest('created')
        except Snapshot.DoesNotExist:
            last_snapshot = None
        
        if last_snapshot is None or last_snapshot.xlsx_export is None:
            return Response(status=404)

        url = request.build_absolute_uri(last_snapshot.xlsx_export.url)
        return HttpResponseRedirect(url)
    

@method_decorator(condition(last_modified_func=get_last_import), name="dispatch")
@method_decorator(cache_control(max_age=0, public=True), name="dispatch")
@method_decorator(cache_page(None, cache="views"), name="dispatch")
class PictureViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Picture.objects.all()
    serializer_class = PictureSerializer
    pagination_class = StandardResultsSetPagination



