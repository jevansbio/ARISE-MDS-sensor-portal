from django.core.exceptions import ObjectDoesNotExist
from rest_framework import status, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .filtersets import UserFilter
from .models import User
from .serializers import UserSerializer, UserProfileSerializer


class UserViewSet(viewsets.ModelViewSet):
    http_method_names = ['get', 'post', 'head']
    filterset_class = UserFilter
    serializer_class = UserSerializer
    search_fields = ['email',
                     'username', 'first_name', 'last_name']

    queryset = User.objects.all().distinct()


class UserProfileViewSet(viewsets.ModelViewSet):
    http_method_names = ['get', 'post', 'head']
    filterset_class = UserFilter
    serializer_class = UserProfileSerializer
    search_fields = ['email',
                     'username', 'first_name', 'last_name']

    queryset = User.objects.all().distinct()
