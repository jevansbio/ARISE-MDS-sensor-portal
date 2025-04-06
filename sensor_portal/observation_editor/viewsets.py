from rest_framework import pagination, status, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from utils.viewsets import (AddOwnerViewSetMixIn, CheckAttachmentViewSetMixIn,
                            OptionalPaginationViewSetMixIn)

from .GBIF_functions import GBIF_species_search
from .models import Observation, Taxon
from .serializers import EvenShorterTaxonSerialier, ObservationSerializer
from .filtersets import ObservationFilterSet


class ObservationViewSet(CheckAttachmentViewSetMixIn, AddOwnerViewSetMixIn, OptionalPaginationViewSetMixIn):
    search_fields = ["taxon__species_name", "taxon__species_common_name"]
    ordering_fields = ["obs_dt", "created_on"]
    filterset_class = ObservationFilterSet
    queryset = Observation.objects.all().distinct()
    serializer_class = ObservationSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        if (target_taxon_level := self.request.GET.get("target_taxon_level")) is not None:
            qs = qs.get_taxonomic_level(target_taxon_level).filter(
                parent_taxon_pk__isnull=False)

        return qs

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

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # Handle nested taxon data
        if 'taxon' in request.data and isinstance(request.data['taxon'], dict):
            taxon_data = request.data['taxon']
            if 'id' in taxon_data:
                request.data['taxon'] = taxon_data['id']
            elif 'species_name' in taxon_data:
                # Create or get taxon by species name
                taxon, created = Taxon.objects.get_or_create(
                    species_name=taxon_data['species_name'],
                    defaults={'species_common_name': taxon_data.get('species_common_name', '')}
                )
                request.data['taxon'] = taxon.id
        
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        # Fetch the complete observation with taxon details
        updated_instance = self.get_object()
        response_serializer = self.get_serializer(updated_instance)
        return Response(response_serializer.data)


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
            gbif_record_n = pagination.PageNumberPagination.page_size - n_database_records
            existing_species = [x.get("species_name") for x in serializer_data]
            gbif_results, scores = GBIF_species_search(
                self.request.GET.get("search"))
            gbif_results = [x for x in gbif_results if x.get(
                "canonicalName") not in existing_species]

            gbif_results = gbif_results[:gbif_record_n]
            new_gbif_results = []
            for gbif_result in gbif_results:
                if (vernacular_name := gbif_result.get("vernacularName")) is None:
                    vernacular_names = gbif_result.get("vernacularNames", [])
                    vernacular_name = ""
                    for x in vernacular_names:
                        if x.get("language", "") == "eng":
                            vernacular_name = x.get("vernacularName", "")
                            break

                new_gbif_result = {"id": "",
                                   "species_name": gbif_result.get("canonicalName", ""),
                                   "species_common_name": vernacular_name,
                                   "taxon_souce": 1}
                new_gbif_results.append(new_gbif_result)
            serializer_data += new_gbif_results

        return self.get_paginated_response(serializer_data)
