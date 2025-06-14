from camtrap_dp_export.querysets import get_ctdp_obs_qs
from camtrap_dp_export.serializers import ObservationSerializerCTDP
from data_models.models import DataFile
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


class ObservationViewSet(CheckAttachmentViewSetMixIn, AddOwnerViewSetMixIn, OptionalPaginationViewSetMixIn):
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

        if 'CTDP' in self.request.GET.keys():
            qs = get_ctdp_obs_qs(qs)

        return qs

    def get_serializer_class(self):
        if 'CTDP' in self.request.GET.keys():
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

    @action(detail=False, methods=['get'], url_path=r'datafile/(?P<datafile_pk>\w+)', url_name="datafile_observations")
    def datafile_observations(self, request, datafile_pk=None):

        # Filter observations based on URL query parameters
        observation_qs = Observation.objects.filter(
            data_files__pk=datafile_pk).select_related('taxon', 'owner')
        observation_qs = self.filter_queryset(observation_qs)

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


class TaxonAutocompleteViewset(viewsets.ReadOnlyModelViewSet):
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
                print(e)

        return self.get_paginated_response(serializer_data)
