from rest_framework import viewsets
from .serializers import MonumentAppListSerialier, MonumentAppDetailSerialier
from main.models import Monument, Picture, AppCategory, Category
from rest_framework.pagination import PageNumberPagination
from django_filters import rest_framework as filters
from rest_framework.filters import SearchFilter, OrderingFilter


# class MonumentFilter(filters.FilterSet):
#     #photographed = filters.BooleanFilter(method='filter_photographed')
#     #on_wiki = filters.BooleanFilter(method='filter_on_wiki')
#     #in_contest = filters.BooleanFilter(method='filter_in_contest')
#     theme = filters.CharFilter(method='filter_theme')
#     region = filters.CharFilter(method='filter_region')
#     province = filters.CharFilter(method='filter_province')
#     municipality = filters.CharFilter(method='filter_municipality')
#     current_commons_state = CharInFilter(field_name='current_commons_state', lookup_expr='in', widget=filters_widgets.CSVWidget)
#     current_wlm_state = CharInFilter(field_name='current_wlm_state', lookup_expr='in', widget=filters_widgets.CSVWidget)

#     def filter_region(self, qs, name, value):
#         if(value=='0'):
#             return qs.filter(region__isnull=True)
#         return qs.filter(region__code=value)

#     def filter_province(self, qs, name, value):
#         if(value=='0'):
#             return qs.filter(province__isnull=True)
#         return qs.filter(province__code=value)

#     def filter_municipality(self, qs, name, value):
#         if(value=='0'):
#             return qs.filter(municipality__isnull=True)
#         return qs.filter(municipality__code=value)
    
#     def filter_theme(self, queryset, name, value):
#         return queryset.filter(categories__pk=value)

#     ordering = filters.OrderingFilter(
#         # tuple-mapping retains order
#         fields=(
#             ('wlm_n', 'wlm_id'),
#             ('q_number', 'q_number'),
#             ('label', 'label'),
#             ('start', 'wlm_auth_start_date'),
#             ('end', 'wlm_auth_end_date'),
#             ('approved_by', 'approved_by'),
#             ('first_image_date', 'first_wlm_image_date'),
#             ('first_image_date_commons', 'first_commons_image_date'),
#             ('most_recent_wlm_image_date', 'most_recent_wlm_image_date'),
#             ('most_recent_commons_image_date', 'most_recent_commons_image_date'),
#             ('municipality_label', 'municipality__name'),
#             ('province_label', 'province__name'),
#             ('region_label', 'region__name'),
#             ('pictures_wlm_count', 'pictures_wlm_count'),
#             ('pictures_commons_count', 'pictures_commons_count'),
#             ('pictures_count', 'pictures_count'),
#             ('first_revision', 'first_revision'),
#         ),
#     )

  
#     class Meta:
#         model = Monument
#         fields = ['region', 'province', 'municipality', 'theme', 'current_wlm_state', 'current_commons_state', 'to_review']



class StandardResultsSetPagination(PageNumberPagination):
    page_size = 100
    page_size_query_param = 'page_size'
    max_page_size = 1000


class MonumentFilter(filters.FilterSet):

    only_without_pictures = filters.BooleanFilter(label="only_without_pictures", method='filter_only_with_pictures')
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
    #filterset_fields = 
    search_fields = ['label', 'municipality__name']
    filterset_class = MonumentFilter

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return MonumentAppDetailSerialier
        return super().get_serializer_class()
    


# Create your views here.
