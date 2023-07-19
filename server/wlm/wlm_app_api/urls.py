from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import MonumentAppViewSet, ClusterMonumentsApi, CategoriesDomainApi

router = DefaultRouter()
router.register(r'monuments', MonumentAppViewSet, basename='monuments')

urlpatterns = router.urls

urlpatterns += [
    path('cluster-monuments/', ClusterMonumentsApi.as_view(), name='cluster_monuments'),
    path('categories-domain/', CategoriesDomainApi.as_view(), name='categories_domain'),
]