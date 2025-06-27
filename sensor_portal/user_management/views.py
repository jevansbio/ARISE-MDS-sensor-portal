from drf_spectacular.utils import extend_schema
from rest_framework_simplejwt.views import (TokenObtainPairView,
                                            TokenRefreshView)

from .serializers import MyTokenObtainPairSerializer


@extend_schema(exclude=True)
class MyTokenObtainPairView(TokenObtainPairView):
    """
    Custom TokenObtainPairView that uses a custom serializer for obtaining JWT tokens.
    """
    serializer_class = MyTokenObtainPairSerializer


@extend_schema(exclude=True)
class MyTokenRefreshView(TokenRefreshView):
    """
    Custom TokenRefreshView that uses the default serializer for refreshing JWT tokens.
    Placeholder for future customizations if needed. Could exten to use captcha as with MyTokenObtainPairView.
    """
    pass
