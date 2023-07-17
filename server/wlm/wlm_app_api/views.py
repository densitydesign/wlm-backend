from rest_framework import viewsets
from django.contrib.gis.geos import Point
from rest_framework.exceptions import APIException
from django.db import models
from .serializers import MonumentAppListSerialier, MonumentAppDetailSerialier
from main.models import Monument, Picture, AppCategory, Category
from rest_framework.pagination import PageNumberPagination
from django_filters import rest_framework as filters
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.gis.db.models.functions import Distance

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 100
    page_size_query_param = 'page_size'
    max_page_size = 1000

class MonumentFilter(filters.FilterSet):

    only_without_pictures = filters.BooleanFilter(label="only_without_pictures", method='filter_only_without_pictures')
    category = filters.CharFilter(method='filter_category')

    def filter_category(self, queryset, name, value):
        if value:
            app_category = AppCategory.objects.get(name=value)
            if not app_category:
                return queryset.none()
            categories_pks = app_category.categories.values_list('pk', flat=True)
            return queryset.filter(categories__pk__in=categories_pks)
        return queryset
    
    def filter_only_without_pictures(self, queryset, name, value):
        if(value):
            return queryset.filter(pictures_wlm_count=0)
        else:
            return queryset
        
    class Meta:
        model = Monument
        fields = ['municipality', 'pictures_wlm_count', "in_contest"]



class MonumentAppViewSet(viewsets.ReadOnlyModelViewSet):
    """
    
    """
    queryset = Monument.objects.all().select_related("municipality")
    serializer_class = MonumentAppListSerialier
    pagination_class = StandardResultsSetPagination
    filter_backends = [
        filters.DjangoFilterBackend,
        OrderingFilter,
        SearchFilter,
    ]
    ordering_fields = ['label', 'pictures_wlm_count']
    search_fields = ['label', 'municipality__name']
    filterset_class = MonumentFilter

    def get_queryset(self):
        qs = super().get_queryset()

        user_lat = self.request.query_params.get('user_lat', None)
        user_lon = self.request.query_params.get('user_lon', None)
        if user_lat and user_lon:
            point = Point(float(user_lon), float(user_lat), srid=4326)
            qs = qs.annotate(
                distance=Distance(
                    'position',
                    point
                )   
            )

        if self.request.query_params.get('ordering', None) in ['distance']:
            if not user_lat or not user_lon:
                raise APIException("user_lat and user_lon are required when ordering by distance")
            qs = qs.order_by('distance')
            
            

        return qs
    

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return MonumentAppDetailSerialier
        return super().get_serializer_class()
        



# Create your views here.
