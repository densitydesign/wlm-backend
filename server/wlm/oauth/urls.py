from django.urls import path
from oauth.views import login, authorize, MeView, RedeemView, WMProfileView

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
urlpatterns = [
    path('oauth-login/', login, name='oauth_login'),
    path('oauth-wm-callback/', authorize, name='oauth_authorize'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('me/', MeView.as_view(), name='me'),
    path('redeem/', RedeemView.as_view(), name='redeem'),
    path('wm-profile/', WMProfileView.as_view(), name='wm-profile'),
]


