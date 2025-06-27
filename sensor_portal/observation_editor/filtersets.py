import django_filters.rest_framework
from utils.filtersets import ExtraDataFilterMixIn, GenericFilterMixIn

from .models import Observation


class ObservationFilter(GenericFilterMixIn, ExtraDataFilterMixIn):
    """
    FilterSet for filtering observations based on various fields.

    """
    field_help_dict = {"taxon__id": "Numeric database ID of the taxon.",
                       "owner__id": "Numeric database ID of user who created this observation.",
                       "data_files__deployment__id": "Numeric database ID of deployment to which\
                           the datafiles of this observation are attached.",
                       "data_files__id": "Numeric database ID of datafile of this observation.",
                       "validation_of__id": "Numeric database ID of the observation of which this observation is a validation of."}

    class Meta:
        model = Observation

        fields = {
            'data_files__id': ['exact'],
            'data_files__deployment__id': ['exact'],
            'taxon__id': ['exact', 'in'],
            'obs_dt': ['exact', 'lte', 'gte'],
            'confidence': ['exact', 'lte', 'gte'],
            'source': ['exact'],
            'sex': ['exact'],
            'lifestage': ['exact'],
            'behavior': ['exact'],
            'validation_requested': ['exact'],
            'validation_of__id': ['exact'],
            'taxon__species_name': ['exact', 'contains'],
            'taxon__species_common_name': ['exact', 'contains'],
            'taxon__taxon_code': ['exact', 'contains'],
            'owner__id': ['exact'],
        }
