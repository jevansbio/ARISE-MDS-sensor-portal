import logging

from camtrap_dp_export.querysets import get_ctdp_obs_qs
from camtrap_dp_export.serializers import ObservationSerializerCTDP
from data_models.models import DataFile
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (OpenApiParameter, extend_schema,
                                   extend_schema_view)
from rest_framework import pagination, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from utils.viewsets import (AddOwnerViewSetMixIn, CheckAttachmentViewSetMixIn,
                            OptionalPaginationViewSetMixIn)

from .filtersets import ObservationFilter
from .GBIF_functions import GBIF_species_search
from .models import Observation, Taxon
from .serializers import EvenShorterTaxonSerialier, ObservationSerializer
from .serializers_fake import DummyObservationSerializer

logger = logging.getLogger(__name__)

obs_extra_parameters = [OpenApiParameter("target_taxon_level",
                                         OpenApiTypes.INT,
                                         OpenApiParameter.QUERY,
                                         description='Set maximum taxonomic level to return .\
                                         For example, setting to 2 will return observerations at the genus level and below.'),
                        OpenApiParameter("ctdp",
                                         OpenApiTypes.BOOL,
                                         OpenApiParameter.QUERY,
                                         description='Set True to return in camtrap DP format')]


@extend_schema(summary="Observations",
               description="Observations are annotations of datafiles, made by human or AI.",
               tags=["Observations"],
               methods=["get", "post", "put", "patch", "delete"],
               responses=DummyObservationSerializer,
               request=DummyObservationSerializer,
               )
@extend_schema_view(
    list=extend_schema(summary='List observations',
                       parameters=obs_extra_parameters,
                       ),
    retrieve=extend_schema(summary='Get a single observation',
                           parameters=[
                               OpenApiParameter(
                                   "id",
                                   OpenApiTypes.INT,
                                   OpenApiParameter.PATH,
                                   description="Database ID of observation to get.")]),
    partial_update=extend_schema(summary='Partially update an observation',
                                 parameters=[
                                     OpenApiParameter(
                                         "id",
                                         OpenApiTypes.INT,
                                         OpenApiParameter.PATH,
                                         description="Database ID of observation to update.")]),
    update=extend_schema(summary='Update an observation',
                         parameters=[
                             OpenApiParameter(
                                 "id",
                                 OpenApiTypes.INT,
                                 OpenApiParameter.PATH,
                                 description="Database ID of observation to update.")]),
    create=extend_schema(summary='Create an observation'),
    destroy=extend_schema(summary='Delete an observation',
                          parameters=[
                              OpenApiParameter(
                                  "id",
                                  OpenApiTypes.INT,
                                  OpenApiParameter.PATH,
                                  description="Database ID of observation to delete.")]),
    datafile_observations=extend_schema(summary="Observations from datafile",
                                        description="Get observations from a specific datafile.",
                                        filters=True,
                                        parameters=obs_extra_parameters + [
                                            OpenApiParameter(
                                                "datafile_id",
                                                OpenApiTypes.INT,
                                                OpenApiParameter.PATH,
                                                description="Database ID of datafile from which to get observations.")]),
    deployment_observations=extend_schema(summary="Observations from deployment",
                                          filters=True,
                                          description="Get observations from a specific deployment.",
                                          parameters=obs_extra_parameters + [
                                              OpenApiParameter(
                                                  "deployment_id",
                                                  OpenApiTypes.INT,
                                                  OpenApiParameter.PATH,
                                                  description="Database ID of deployment from which to get observations.")]),
)
class ObservationViewSet(CheckAttachmentViewSetMixIn, AddOwnerViewSetMixIn, OptionalPaginationViewSetMixIn):
    """

    A ViewSet for listing, creating, updating, and deleting observations. 

    """
    search_fields = ["taxon__species_name", "taxon__species_common_name"]
    ordering_fields = ["obs_dt", "created_on"]
    queryset = Observation.objects.all().prefetch_related("taxon")
    serializer_class = ObservationSerializer
    filter_backend = viewsets.ModelViewSet.filter_backends
    filterset_class = ObservationFilter

    def get_queryset(self):
        qs = Observation.objects.all().prefetch_related("taxon")
        if (target_taxon_level := self.request.GET.get("target_taxon_level")) is not None:
            qs = qs.get_taxonomic_level(target_taxon_level).filter(
                parent_taxon_pk__isnull=False)

        if 'ctdp' in self.request.GET.keys():
            qs = get_ctdp_obs_qs(qs)

        return qs

    def get_serializer_class(self):
        if 'ctdp' in self.request.GET.keys():
            return ObservationSerializerCTDP
        else:
            return ObservationSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update(
            {"target_taxon_level": self.request.GET.get("target_taxon_level")})
        return context

    def check_attachment(self, serializer):
        data_files_objects = serializer.validated_data.get('data_files')
        if data_files_objects is not None:
            for data_file_object in data_files_objects:
                if not self.request.user.has_perm('data_models.annotate_datafile', data_file_object):
                    raise PermissionDenied(
                        f"You don't have permission to add an observation to {data_file_object.file_name}")

    @action(detail=False, methods=['get'], url_path=r'datafile/(?P<datafile_id>\w+)', url_name="datafile_observations")
    def datafile_observations(self, request, datafile_id=None):

        # Filter observations based on URL query parameters
        observation_qs = Observation.objects.filter(
            data_files__pk=datafile_id).select_related('taxon', 'owner')
        observation_qs = self.filter_queryset(observation_qs)

        if 'ctdp' in self.request.GET.keys():
            observation_qs = get_ctdp_obs_qs(observation_qs)

        # Paginate the queryset
        page = self.paginate_queryset(observation_qs)
        if page is not None:
            observation_serializer = self.get_serializer(
                page, many=True, context={'request': request})

            return self.get_paginated_response(observation_serializer.data)

        # If no pagination, serialize all data

        observation_serializer = self.get_serializer(
            page, many=True, context={'request': request})
        return Response(observation_serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path=r'deployment/(?P<deployment_id>\w+)', url_name="deployment_observations")
    def deployment_observations(self, request, deployment_id=None):

        # Filter observations based on URL query parameters
        observation_qs = Observation.objects.filter(
            data_files__deployment=deployment_id).select_related('taxon', 'owner')
        observation_qs = self.filter_queryset(observation_qs)

        if 'ctdp' in self.request.GET.keys():
            observation_qs = get_ctdp_obs_qs(observation_qs)

        # Paginate the queryset
        page = self.paginate_queryset(observation_qs)
        if page is not None:
            observation_serializer = self.get_serializer(
                page, many=True, context={'request': request})
            return self.get_paginated_response(observation_serializer.data)

        # If no pagination, serialize all data
        observation_serializer = self.get_serializer(
            observation_qs, many=True, context={'request': request})
        return Response(observation_serializer.data, status=status.HTTP_200_OK)


@extend_schema(
    exclude=True
)
class TaxonAutocompleteViewset(viewsets.ReadOnlyModelViewSet):
    """
    A ViewSet for providing autocomplete functionality for taxon names.
    This ViewSet allows users to search for taxon names and common names,
    returning a limited number of results for efficient searching.
    It integrates with the GBIF species search API to supplement local taxon data.
    """
    http_method_names = ['get']
    search_fields = ["species_name", "species_common_name"]
    queryset = Taxon.objects.all().distinct()
    serializer_class = EvenShorterTaxonSerialier
    pagination.PageNumberPagination.page_size = 5

    def list(self, request, pk=None):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        serializer = self.serializer_class(page, many=True)
        serializer_data = serializer.data
        if (n_database_records := len(serializer_data)) < pagination.PageNumberPagination.page_size:
            try:
                gbif_record_n = pagination.PageNumberPagination.page_size - n_database_records
                existing_species = [x.get("species_name")
                                    for x in serializer_data]
                gbif_results, scores = GBIF_species_search(
                    self.request.GET.get("search"))
                gbif_results = [x for x in gbif_results if (canon_name := x.get(
                    "canonicalName")) and canon_name not in existing_species and canon_name != ""]
                if len(gbif_results) > 0:
                    gbif_results = gbif_results[:gbif_record_n]
                    new_gbif_results = []
                    for gbif_result in gbif_results:
                        if (vernacular_name := gbif_result.get("vernacularName")) is None:
                            vernacular_names = gbif_result.get(
                                "vernacularNames", [])
                            vernacular_name = ""
                            for x in vernacular_names:
                                if x.get("language", "") == "eng":
                                    vernacular_name = x.get(
                                        "vernacularName", "")
                                    break

                        new_gbif_result = {"id": "",
                                           "species_name": gbif_result.get("canonicalName", ""),
                                           "species_common_name": vernacular_name,
                                           "taxon_souce": 1}
                        new_gbif_results.append(new_gbif_result)
                    serializer_data += new_gbif_results
            except Exception as e:
                logger.error(e)

        return self.get_paginated_response(serializer_data)
