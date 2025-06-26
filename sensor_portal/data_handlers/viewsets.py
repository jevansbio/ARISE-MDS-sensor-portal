from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from .serializers import DataHandlerSerializer


@extend_schema(
    exclude=True
)
class DataHandlerViewSet(viewsets.ViewSet):
    """
    A ViewSet for listing and retrieving data handlers.

    List: Returns all data handlers available in the settings.
    Retrieve: Returns a specific data handler by its index (primary key).
    """
    serializer_class = DataHandlerSerializer
    permission_classes = [IsAuthenticated]

    @method_decorator(cache_page(60 * 60 * 2))
    def list(self, request: Request) -> Response:
        """
        List all data handlers.

        Args:
            request (Request): The HTTP request instance.

        Returns:
            Response: A DRF Response containing serialized data handlers.
        """
        serializer = self.serializer_class(
            instance=settings.DATA_HANDLERS.data_handler_list, many=True)
        return Response(serializer.data)

    @method_decorator(cache_page(60 * 60 * 2))
    def retrieve(self, request: Request, pk: str = None) -> Response:
        """
        Retrieve a single data handler by its index.

        Args:
            request (Request): The HTTP request instance.
            pk (str, optional): The index of the data handler in the list.

        Returns:
            Response: A DRF Response containing the serialized data handler, or 404 if not found or invalid index.
        """
        try:
            data_handler = settings.DATA_HANDLERS.data_handler_list[int(pk)]
        except (IndexError, ValueError):
            return Response(status=404)

        serializer = self.serializer_class(data_handler)
        return Response(serializer.data)
