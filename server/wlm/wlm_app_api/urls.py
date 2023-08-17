from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import MonumentAppViewSet, ClusterMonumentsApi, CategoriesDomainApi, UploadImageView, PersonalContributionsView, CurrentContestsView

router = DefaultRouter()
router.register(r'monuments', MonumentAppViewSet, basename='monuments')

urlpatterns = router.urls

urlpatterns += [
    path('cluster-monuments/', ClusterMonumentsApi.as_view(), name='cluster_monuments'),
    path('categories-domain/', CategoriesDomainApi.as_view(), name='categories_domain'),
    path('upload-images/', UploadImageView.as_view(), name='upload_image'),
    path('personal-contributions/', PersonalContributionsView.as_view(), name='personal_contributions'),
    path('active-contests/', CurrentContestsView.as_view(), name='current_contests'),
]