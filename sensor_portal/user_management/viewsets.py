from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import get_object_or_404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (OpenApiParameter, extend_schema,
                                   extend_schema_view)
from rest_framework import status, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .filtersets import UserFilter
from .models import User
from .serializers import UserProfileSerializer, UserSerializer


@extend_schema(
    exclude=True
)
class UserViewSet(viewsets.ModelViewSet):
    """
    A ViewSet for managing User instances, allowing users to list, retrieve,
    create, and search for users. This viewset is primarily used by managers.
    """
    http_method_names = ['get', 'post', 'head']
    filterset_class = UserFilter
    serializer_class = UserSerializer
    search_fields = ['email',
                     'username', 'first_name', 'last_name', 'organisation']

    def get_permissions(self):

        if self.action == "create":
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    queryset = User.objects.filter(deviceuser__isnull=True).distinct()


@extend_schema(summary="Users",
               description="User profiles. A user can only retrieve their own profile",
               tags=["Users"],
               methods=["get"],
               )
@extend_schema_view(list=extend_schema(exclude=True
                                       ),
                    retrieve=extend_schema(summary='Get user profile.',
                                           parameters=[
                                               OpenApiParameter(
                                                   "id",
                                                   OpenApiTypes.INT,
                                                   OpenApiParameter.PATH,
                                                   description="Database ID of user to get.")]),)
class UserProfileViewSet(viewsets.ModelViewSet):
    """
    A ViewSet for managing user profiles, allowing users to retrieve their own profile.
    This viewset is primarily used for viewing user profiles, and it does not allow listing of all users.
    Users can only retrieve their own profile unless they are staff members.
    """
    http_method_names = ['get', 'head']
    filterset_class = UserFilter
    serializer_class = UserProfileSerializer
    search_fields = ['email',
                     'username', 'first_name', 'last_name', 'organisation']
    permission_classes = [IsAuthenticated]
    queryset = User.objects.filter(deviceuser__isnull=True)

    def list(self, request, *args, **kwargs):
        return Response({"detail": "Method 'GET' not allowed."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def retrieve(self, request, pk=None, *args, **kwargs):
        user_obj = get_object_or_404(pk=pk, klass=self.queryset)

        if not request.user == user_obj and not request.user.is_staff:
            # Force return of the users own profile
            serialized_data = UserProfileSerializer(request.user)
            return Response(serialized_data.data, status=status.HTTP_200_OK)
            # return Response({"detail": " You do not have permission to view this item."},
            #                 status=status.HTTP_403_FORBIDDEN)

        return super().retrieve(request, *args, **kwargs)
