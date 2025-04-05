from bridgekeeper import perms
from django_filters import FilterSet, ModelChoiceFilter
from data_models.models import DataFile
from .models import Observation

class ObservationFilterSet(FilterSet):
    data_files = ModelChoiceFilter(
        field_name='data_files',
        to_field_name='id',
        queryset=DataFile.objects.all()
    )

    class Meta:
        model = Observation
        fields = ['data_files'] 