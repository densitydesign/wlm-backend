from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from main.models import (Region, Province, Municipality, Monument, MonumentAuthorization, Picture)
from main.serializers import (RegionSerializer, RegionGeoSerializer,
     ProvinceSerializer, MunicipalitySerializer, MonumentSerializer, 
     MonumentSmallSerializer, MonumentAuthorizationSerializer, PictureSerializer, 
     WLMQuerySerializer, ProvinceGeoSerializer, MunicipalityGeoSerializer)
from main.helpers import get_snap


def get_history(monuments_qs, query_params):
    ser = WLMQuerySerializer(data=query_params)
    ser.is_valid(raise_exception=True)
    
    date_from = ser.validated_data["date_from"]
    date_to = ser.validated_data["date_to"]
    step_size = ser.validated_data["step_size"]
    step_unit = ser.validated_data["step_unit"]
    
    history = get_snap(monuments_qs, date_from, date_to, step_size=step_size, step_unit=step_unit)
    return history, ser.validated_data

class RegionViewSet(viewsets.ModelViewSet):
    queryset = Region.objects.all()
    serializer_class = RegionSerializer

    @action(methods=["get"], detail=False)
    def geo(self, request):
        queryset = self.get_queryset()
        filtered_queryset = self.filter_queryset(queryset)
        ser = RegionGeoSerializer(filtered_queryset, many=True)
        return Response(ser.data)


    @action(methods=["get"], detail=True)
    def geoprovinces(self, request, pk=None):
        region = self.get_object()
        ser = ProvinceGeoSerializer(region.provinces.all(), many=True)
        return Response(ser.data)   

    @action(methods=["get"], detail=True, url_path='geoprovinces/(?P<province_pk>[^/.]+)/geomunicipalities')
    def geomunicipalities(self, request, pk=None, province_pk=None):
        region = self.get_object()
        province = region.provinces.get(pk=province_pk)
        ser = MunicipalityGeoSerializer(province.municipalities.all(), many=True)
        return Response(ser.data)   
        

    @action(methods=["get"], detail=True)
    def wlm(self, request, pk=None):
        area = self.get_object()
        monuments_qs = area.monuments.all()
        history, validated_data = get_history(monuments_qs, request.query_params)
        out = {
            "history": history,
        }
        if validated_data['monuments']:
            out['monuments'] = MonumentSmallSerializer(monuments_qs, many=True).data
    
        return Response(out)

    @action(methods=["get"], detail=True)
    def monuments(self, request, pk=None):
        area = self.get_object()
        monuments_qs = area.monuments.all()
        return Response(MonumentSmallSerializer(monuments_qs, many=True).data)


class ProvinceViewSet(viewsets.ModelViewSet):
    queryset = Province.objects.all()
    serializer_class = ProvinceSerializer

    @action(methods=["get"], detail=False)
    def geo(self, request):
        queryset = self.get_queryset()
        filtered_queryset = self.filter_queryset(queryset)
        ser = ProvinceGeoSerializer(filtered_queryset, many=True)
        return Response(ser.data)

    @action(methods=["get"], detail=True)
    def geomunicipalities(self, request, pk=None):
        province = self.get_object()
        ser = MunicipalityGeoSerializer(province.municipalities.all(), many=True)
        return Response(ser.data)   


    @action(methods=["get"], detail=True)
    def wlm(self, request, pk=None):
        area = self.get_object()
        monuments_qs = area.monuments.all()
        history, validated_data = get_history(monuments_qs, request.query_params)
        out = {
            "history": history,
        }
        if validated_data['monuments']:
            out['monuments'] = MonumentSmallSerializer(monuments_qs, many=True).data
    
        return Response(out)
        

    @action(methods=["get"], detail=True)
    def monuments(self, request, pk=None):
        area = self.get_object()
        monuments_qs = area.monuments.all()
        return Response(MonumentSmallSerializer(monuments_qs, many=True).data)


class MunicipalityViewSet(viewsets.ModelViewSet):
    queryset = Municipality.objects.all()
    serializer_class = MunicipalitySerializer

    @action(methods=["get"], detail=True)
    def wlm(self, request, pk=None):
        area = self.get_object()
        monuments_qs = area.monuments.all()
        history, validated_data = get_history(monuments_qs, request.query_params)
        out = {
            "history": history,
        }
        if validated_data['monuments']:
            out['monuments'] = MonumentSmallSerializer(monuments_qs, many=True).data
    
        return Response(out)

    @action(methods=["get"], detail=True)
    def monuments(self, request, pk=None):
        area = self.get_object()
        monuments_qs = area.monuments.all()
        return Response(MonumentSmallSerializer(monuments_qs, many=True).data)


class MonumentViewSet(viewsets.ModelViewSet):
    queryset = Monument.objects.all()
    serializer_class = MonumentSerializer


class MonumentAuthorizationViewSet(viewsets.ModelViewSet):
    queryset = MonumentAuthorization.objects.all()
    serializer_class = MonumentAuthorizationSerializer


class PictureViewSet(viewsets.ModelViewSet):
    queryset = Picture.objects.all()
    serializer_class = PictureSerializer



