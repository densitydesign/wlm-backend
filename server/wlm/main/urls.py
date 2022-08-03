from rest_framework.routers import DefaultRouter
from main.views import (RegionViewSet, ProvinceViewSet, MunicipalityViewSet, MonumentViewSet, PictureViewSet)

router = DefaultRouter()
router.register('region', RegionViewSet)
router.register('province', ProvinceViewSet)
router.register('municipality', MunicipalityViewSet)
router.register('monument', MonumentViewSet)
router.register('picture', PictureViewSet)

urlpatterns = router.urls
