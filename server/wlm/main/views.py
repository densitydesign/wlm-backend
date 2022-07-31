from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from main.models import (Region, Province, Municipality, Monument, MonumentAuthorization, Picture)
from main.serializers import (RegionSerializer, ProvinceSerializer, MunicipalitySerializer, MonumentSerializer, MonumentSmallSerializer, MonumentAuthorizationSerializer, PictureSerializer, WLMQuerySerializer)
from main.helpers import get_snap
import datetime





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
    def topo(self, request):
        return self.list(request)

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



