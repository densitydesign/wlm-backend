from rest_framework.routers import DefaultRouter
from .views import MonumentAppViewSet

router = DefaultRouter()
router.register(r'monuments', MonumentAppViewSet, basename='monuments')

urlpatterns = router.urls