from django.shortcuts import render
from django.http import HttpResponse
from authlib.integrations.django_client import OAuth
from django.urls import reverse
import requests
import logging
import sys
from authlib.integrations.django_client import OAuth, DjangoOAuth2App
from authlib.integrations.requests_client import OAuth2Session
from django.contrib.auth import get_user_model
from oauth.models import OAuth2Token
from oauth.serializers import UserSerializer, TokenSerializer, RedeemInputSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema
from  authlib.integrations.requests_client import OAuth2Auth

import jwt

SECRET = "ze4QUGtDgDE7qTeo6tajY1MR1gMMp3YPu1A1dBf/5Mc="
from datetime import datetime, timedelta, timezone


def forge_access_jwt(username, ttl=300):
    payload = {"username": username, "exp": datetime.now(tz=timezone.utc) + timedelta(seconds=ttl)}
    return jwt.encode(payload, SECRET, algorithm="HS256")


class InvalidDownloadToken(Exception):
    pass


def check_download_jwt(token):
    try:
        payload = jwt.decode(token, SECRET, algorithms=["HS256"])
    except (jwt.exceptions.InvalidTokenError, jwt.exceptions.ExpiredSignatureError) as err:
        raise InvalidDownloadToken()
    return payload["username"]


# log = logging.getLogger('authlib')
# log.addHandler(logging.StreamHandler(sys.stdout))
# log.setLevel(logging.DEBUG)

User = get_user_model()


class WLMSession(OAuth2Session):
    def request(self, method, url: str, withhold_token=False, auth=None, **kwargs):
        out = super().request(method, url, withhold_token, auth, **kwargs)
        # print(out.text)
        return out


class WLMDjangoOAuth2App(DjangoOAuth2App):
    client_cls = WLMSession


class WLMOauth(OAuth):
    oauth2_client_cls = WLMDjangoOAuth2App


def update_token(name, token, refresh_token=None, access_token=None):
    if refresh_token:
        item = OAuth2Token.objects.get(name=name, refresh_token=refresh_token)
    elif access_token:
        item = OAuth2Token.objects.get(name=name, access_token=access_token)
    else:
        return

    # update old token
    item.access_token = token["access_token"]
    item.refresh_token = token.get("refresh_token")
    item.expires_at = token["expires_at"]
    item.save()


# oauth = OAuth(update_token=update_token)

oauth = WLMOauth(update_token=update_token)


params = {
    "client_id": "b200933a5469c41337c85627939bc485",
    "client_secret": "d21f5227f416da4619da9268798e60964731cdbd",
    "access_token_url": "http://localhost:8080/rest.php/oauth2/access_token",
    "access_token_params": {
        "grant_type": "authorization_code",
    },
    "authorize_url": "http://localhost:8080/rest.php/oauth2/authorize",
    "authorize_params": {},
    "refresh_token_url": None,
    "client_kwargs": {
        "code_challenge_method": "S256",
    },
    "api_base_url": "http://localhost:8080/rest.php/oauth2/resource/",
}

"""
    http://localhost:8000/api/oauth-login/
"""

oauth.register(name="mediawiki", **params)


def login(request):
    # build a full authorize callback uri
    redirect_uri = request.build_absolute_uri(reverse("oauth_authorize"))
    return oauth.mediawiki.authorize_redirect(request, redirect_uri)

    # print(o)


def authorize(request):
    token = oauth.mediawiki.authorize_access_token(request)
    resp = oauth.mediawiki.get("profile", token=token)
    profile = resp.json()
    username = "mw--" + profile["username"]

    user = User.objects.filter(username=username).first()
    if not user:
        user = User.objects.create_user(username=username)

    OAuth2Token.objects.update_or_create(
        user=user,
        name="mediawiki",
        defaults=dict(
            token_type=token["token_type"],
            access_token=token["access_token"],
            refresh_token=token["refresh_token"],
            expires_at=token["expires_at"],
        ),
    )

    redeem_token = forge_access_jwt(username)

    return HttpResponse(redeem_token)


class RedeemView(APIView):
    serializer_class = TokenSerializer

    @extend_schema(
        parameters=[
            RedeemInputSerializer,
        ],
        responses={
            200: TokenSerializer,
            400: "Invalid token",
        },
    )
    def get(self, request):
        input_ser = RedeemInputSerializer(data=request.GET)
        input_ser.is_valid(raise_exception=True)
        token = input_ser.validated_data["redeem_token"]
        username = check_download_jwt(token)
        user = User.objects.filter(username=username).first()
        if not user:
            return HttpResponse("Invalid token", status=400)
        refresh = RefreshToken.for_user(user)

        data = {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }
        return Response(data)


class MeView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def get(self, request):
        return Response(UserSerializer(request.user).data)
    

class WMProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        token = OAuth2Token.objects.get(user=request.user, name="mediawiki")
        #resp = oauth.mediawiki.get("profile", token=token.to_token())
        auth = OAuth2Auth(token.to_token())
        profile_url = "http://localhost:8080/rest.php/oauth2/resource/profile"
        resp = requests.get(profile_url, auth=auth)
        profile = resp.json()
        return Response(profile)    


"""
ESEMPIO QUERY USER
https://commons.wikimedia.org/w/api.php?action=query&prop=imageinfo&generator=search&gsrsearch=author:Mongolo1984&iiprop=extmetadata|user&gsrnamespace=6&gsrsearch=%22Wiki%20Loves%20Monuments%20Italia%22|author:Mongolo1984
"""