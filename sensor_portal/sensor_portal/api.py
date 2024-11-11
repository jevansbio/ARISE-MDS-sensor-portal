from data_models.api import router as data_models_router
from rest_framework import routers
from user_management.api import router as user_management_router

router = routers.DefaultRouter()
router.registry.extend(data_models_router.registry)
router.registry.extend(user_management_router.registry)
urlpatterns = router.urls
