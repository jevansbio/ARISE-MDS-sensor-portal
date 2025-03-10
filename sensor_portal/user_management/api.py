
from rest_framework import routers
from user_management.viewsets import UserViewSet, UserProfileViewSet

router = routers.DefaultRouter()
router.register(r"user", UserViewSet, basename='user')
router.register(r"userprofile", UserProfileViewSet, basename='userprofile')
