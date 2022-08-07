from django.core.cache import cache
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from main.models import (Region, Province, Municipality, Monument, Picture)
from main.serializers import (RegionSerializer, RegionGeoSerializer,
     ProvinceSerializer, MunicipalitySerializer, MonumentSerializer, 
     MonumentSmallSerializer,  PictureSerializer, 
     WLMQuerySerializer, ProvinceGeoSerializer, MunicipalityGeoSerializer)
from main.helpers import get_snap, format_history
from drf_spectacular.utils import extend_schema


def get_history(monuments_qs, query_params, group=None):
    ser = WLMQuerySerializer(data=query_params)
    ser.is_valid(raise_exception=True)
    
    date_from = ser.validated_data["date_from"]
    date_to = ser.validated_data["date_to"]
    step_size = ser.validated_data["step_size"]
    step_unit = ser.validated_data["step_unit"]
    
    history = get_snap(monuments_qs, date_from, date_to, step_size=step_size, step_unit=step_unit, group=group)
    print(history)
    return history, ser.validated_data

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
    @action(methods=["get"], detail=True)
    def wlm(self, request, pk=None):
        area = self.get_object()
        monuments_qs = area.monuments.all()
        history, validated_data = get_history(monuments_qs, request.query_params, group=['region', 'region__name'])
        return Response(history)

    @extend_schema(parameters=[WLMQuerySerializer])
    @action(methods=["get"], detail=True, url_path='wlm-areas')
    def wlm_areas(self, request, pk=None):
        area = self.get_object()
        monuments_qs = area.monuments.all()
        history, validated_data = get_history(monuments_qs, request.query_params, group=['province', 'province__name'])
        return Response(history)

    @action(methods=["get"], detail=True)
    def monuments(self, request, pk=None):
        area = self.get_object()
        monuments_qs = area.monuments.all()
        return Response(MonumentSmallSerializer(monuments_qs, many=True).data)


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
    @action(methods=["get"], detail=True, url_path='wlm-areas')
    def wlm_areas(self, request, pk=None):
        area = self.get_object()
        monuments_qs = area.monuments.all()
        history, validated_data = get_history(monuments_qs, request.query_params, group=['municipality', 'municipality__name'])
        return Response(history)
    

    @action(methods=["get"], detail=True)
    def monuments(self, request, pk=None):
        area = self.get_object()
        monuments_qs = area.monuments.all()
        return Response(MonumentSmallSerializer(monuments_qs, many=True).data)


class MunicipalityViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Municipality.objects.all()
    serializer_class = MunicipalitySerializer

    @extend_schema(parameters=[WLMQuerySerializer])
    @action(methods=["get"], detail=True)
    def wlm(self, request, pk=None):
        area = self.get_object()
        monuments_qs = area.monuments.all()
        history, validated_data = get_history(monuments_qs, request.query_params, group=['municipality', 'municipality__name'])
        return Response(history)

    @action(methods=["get"], detail=True)
    def monuments(self, request, pk=None):
        area = self.get_object()
        monuments_qs = area.monuments.all()
        return Response(MonumentSmallSerializer(monuments_qs, many=True).data)


class MonumentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Monument.objects.all()
    serializer_class = MonumentSerializer


class PictureViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Picture.objects.all()
    serializer_class = PictureSerializer



