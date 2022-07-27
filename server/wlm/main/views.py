from rest_framework import viewsets
from main.models import (Region, Province, Municipality, Monument, MonumentAuthorization, Picture, Snapshot)
from main.serializers import (RegionSerializer, ProvinceSerializer, MunicipalitySerializer, MonumentSerializer, MonumentAuthorizationSerializer, PictureSerializer, SnapshotSerializer)


class RegionViewSet(viewsets.ModelViewSet):
    queryset = Region.objects.all()
    serializer_class = RegionSerializer


class ProvinceViewSet(viewsets.ModelViewSet):
    queryset = Province.objects.all()
    serializer_class = ProvinceSerializer


class MunicipalityViewSet(viewsets.ModelViewSet):
    queryset = Municipality.objects.all()
    serializer_class = MunicipalitySerializer


class MonumentViewSet(viewsets.ModelViewSet):
    queryset = Monument.objects.all()
    serializer_class = MonumentSerializer


class MonumentAuthorizationViewSet(viewsets.ModelViewSet):
    queryset = MonumentAuthorization.objects.all()
    serializer_class = MonumentAuthorizationSerializer


class PictureViewSet(viewsets.ModelViewSet):
    queryset = Picture.objects.all()
    serializer_class = PictureSerializer


class SnapshotViewSet(viewsets.ModelViewSet):
    queryset = Snapshot.objects.all()
    serializer_class = SnapshotSerializer


