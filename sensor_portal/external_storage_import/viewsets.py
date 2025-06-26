from drf_spectacular.utils import extend_schema
from external_storage_import.serializers import DataStorageInputSerializer
from utils.viewsets import AddOwnerViewSetMixIn

from .filtersets import DataStorageFilter
from .models import DataStorageInput


@extend_schema(exclude=True)
class DataStorageInputViewSet(AddOwnerViewSetMixIn):
    """
    A ViewSet for managing DataStorageInput instances, allowing users to
    list, retrieve, and search for external storage inputs.
    """
    serializer_class = DataStorageInputSerializer
    queryset = DataStorageInput.objects.all().distinct()
    search_fields = ['name']
    filterset_class = DataStorageFilter
