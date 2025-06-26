import django_filters.rest_framework
from django.db.models import BooleanField, Case, ExpressionWrapper, F, Q, When
from observation_editor.models import Observation
from utils.filtersets import ExtraDataFilterMixIn, GenericFilterMixIn

from .models import (DataFile, DataType, Deployment, Device, DeviceModel,
                     Project)


class DataTypeFilter(GenericFilterMixIn):
    """
    FilterSet for DataType, providing filters to distinguish between file and device types.

    Filters:
        file_type (BooleanFilter): Returns only data types attached to devices.
        device_type (BooleanFilter): Returns only data types attached to files.
    """

    file_type = django_filters.BooleanFilter(
        method='is_file_type', label="file_type", help_text="Return only data types attached to devices.")
    device_type = django_filters.BooleanFilter(
        method='is_file_type', label="device_type", help_text="Return only data types attached to files.")

    def is_file_type(self, queryset, name, value):
        """
        Filter queryset based on whether DataTypes are linked to devices or files.

        Args:
            queryset (QuerySet): Queryset to filter.
            name (str): 'file_type' or 'device_type'.
            value (bool): Whether to include only device/file types.

        Returns:
            QuerySet: Filtered queryset.
        """
        if name == "file_type":
            return queryset
        return queryset.filter(device_models__isnull=not value)


class DeploymentFilter(GenericFilterMixIn, ExtraDataFilterMixIn):
    """
    FilterSet for Deployment, allowing advanced filtering by deployment, device, site, and project fields,
    as well as activity status and time ranges.

    field_help_dict provides help text for common fields.
    """

    field_help_dict = {
        "device__id": "Numeric database ID of a deployed device.",
        "owner__id": "Numeric database ID of user who created a deployment.",
        "id": "Numeric database ID of deployment.",
        "site__id": "Numeric database ID of site where the deployment is located.",
        "data_type__id": "Numeric database ID of primary data type of deployment."
    }

    class Meta:
        model = Deployment
        fields = GenericFilterMixIn.get_fields().copy()
        fields.update({
            'deployment_device_ID': ['exact', 'icontains', 'in'],
            'is_active': ['exact'],
            'deployment_start': ['exact', 'lte', 'gte'],
            'deployment_end': ['exact', 'lte', 'gte'],
            'site': ['exact', 'in'],
            'site__name': ['exact', 'icontains', 'in'],
            'site__short_name': ['exact', 'icontains', 'in'],
            'device__id': ['exact', 'in'],
            'device__device_ID': ['exact', 'icontains', 'in'],
            'device__name': ['exact', 'icontains', 'in'],
            'project__id': ['exact'],
            'project__project_ID': ['exact'],
            'device_type': ['exact', 'in'],
            'device_type__name': ['exact', 'icontains', 'in'],
        })


class ProjectFilter(GenericFilterMixIn):
    """
    FilterSet for Project, allowing filtering by project details and deployment activity.

    Filters:
        is_active (BooleanFilter): Filter projects by whether they have active deployments.

    Meta:
        model: Project
        fields: project_ID, name, organisation (all support exact, icontains, in)
    """

    is_active = django_filters.BooleanFilter(
        field_name="deployments__is_active", help_text="Filters projects by whether they have active deployments.")

    class Meta:
        model = Project
        fields = GenericFilterMixIn.get_fields().copy()
        fields.update({
            'project_ID': ['exact', 'icontains', 'in'],
            'name': ['exact', 'icontains', 'in'],
            'organisation': ['exact', 'icontains', 'in'],
        })


class DeviceFilter(GenericFilterMixIn, ExtraDataFilterMixIn):
    """
    FilterSet for Device, enabling filtering by device type, deployment activity, and related fields.

    Filters:
        is_active (BooleanFilter): Filters devices by the active status of their deployments.
        device_type (ModelChoiceFilter): Filters by device type.

    field_help_dict provides help text for key fields.
    """

    is_active = django_filters.BooleanFilter(
        field_name="deployments__is_active", help_text="Filters devices by whether they have active deployments.")

    device_type = django_filters.ModelChoiceFilter(
        field_name='type',
        queryset=DataType.objects.filter(devices__isnull=False).distinct(),
        label="device type",
        help_text="Filters devices by their type. The queryset is restricted to DataType objects associated with devices."
    )

    field_help_dict = {
        "type": "Numeric database ID of device datatype.",
        "id": "Numeric database ID of device.",
    }

    class Meta:
        model = Device
        fields = GenericFilterMixIn.get_fields().copy()
        fields.update({
            'type': ['exact', 'in'],
            'type__name': ['exact', 'icontains', 'in'],
            'device_ID': ['exact', 'icontains', 'in'],
            'model__name': ['exact', 'icontains', 'in'],
        })


class DataFileFilter(GenericFilterMixIn, ExtraDataFilterMixIn):
    """
    FilterSet for DataFile, supporting filters for favorite status, deployment activity, device type,
    observation presence and type, and observation uncertainty.

    Custom Methods:
        filter_obs_type: Filter files by associated observation types.
        filter_uncertain: Filter files by uncertainty status in observations.

    field_help_dict provides help text for common fields.
    """

    is_favourite = django_filters.BooleanFilter(
        field_name='favourite_of', exclude=True, lookup_expr='isnull',
        label='is favourite',
        help_text="Filter datafiles by whether a user has favourited them."
    )
    is_active = django_filters.BooleanFilter(
        field_name="deployment__is_active",
        help_text="Filter datafiles by whether their deployment is active"
    )
    device_type = django_filters.ModelChoiceFilter(
        field_name='deployment__device__type',
        queryset=DataType.objects.filter(devices__isnull=False).distinct(),
        label="device type",
        help_text="Data type of device"
    )
    has_observations = django_filters.BooleanFilter(
        field_name="observations", lookup_expr="isnull", exclude=True, label="Has observations",
        help_text="Filter datafiles by whether they have observations"
    )
    obs_type = django_filters.ChoiceFilter(
        choices=[
            ("no_obs", "No observations"),
            ("no_human_obs", "No human observations"),
            ("all_obs", "All observations"),
            ("has_human", "Human observations"),
            ("has_ai", "AI observations"),
            ("human_only", "Human observations only"),
            ("ai_only", "AI observations only"),
        ],
        method="filter_obs_type",
        label="Observation type",
        help_text="Filter datafiles by type of observation present."
    )

    def filter_obs_type(self, queryset, name, value):
        """
        Filter DataFiles based on observation type.

        Args:
            queryset (QuerySet): Initial queryset.
            name (str): Filter name (unused).
            value (str): Observation type to filter by.

        Returns:
            QuerySet: Filtered queryset.
        """
        if value == "no_obs":
            return queryset.filter(observations__isnull=True)
        elif value == "no_human_obs":
            return queryset.exclude(observations__source="human")
        elif value == "all_obs":
            return queryset.filter(observations__isnull=False)
        elif value == "has_human":
            return queryset.filter(observations__source="human")
        elif value == "has_ai":
            return queryset.filter(observations__in=Observation.objects.all().exclude(source="human"))
        elif value == "ai_only":
            return queryset.filter(observations__isnull=False).exclude(observations__source="human")
        elif value == "human_only":
            return queryset.filter(observations__source="human").exclude(observations__in=Observation.objects.all().exclude(source="human"))

    uncertain = django_filters.ChoiceFilter(
        choices=[
            ("no_uncertain", "No uncertain observations"),
            ("uncertain", "Uncertain observations"),
            ("other_uncertain", "Other's uncertain observations"),
            ("my_uncertain", "My uncertain observations"),
        ],
        method="filter_uncertain",
        label="Uncertain observations",
        help_text="Filter datafiles by whether they have uncertain observations."
    )

    def filter_uncertain(self, queryset, name, value):
        """
        Filter DataFiles based on uncertainty status of observations.

        Args:
            queryset (QuerySet): Initial queryset.
            name (str): Filter name (unused).
            value (str): Uncertainty type to filter by.

        Returns:
            QuerySet: Filtered queryset.
        """
        if value == "no_uncertain":
            return queryset.filter(Q(observations__isnull=True) | Q(observations__validation_requested=False))
        elif value == "uncertain":
            return queryset.filter(observations__validation_requested=True)
        elif value == "my_uncertain":
            return queryset.filter(observations__validation_requested=True, observations__owner=self.request.user)
        elif value == "other_uncertain":
            return queryset.filter(observations__validation_requested=True).exclude(observations__owner=self.request.user)

    field_help_dict = {
        "deployment__id": "Numeric database ID of deployment.",
        "id": "Numeric database ID of datafile.",
        "favourite_of__id": "Database ID of user that has favourited this file."
    }

    class Meta:
        model = DataFile
        fields = GenericFilterMixIn.get_fields().copy()
        fields.update({
            'deployment__id': ['exact', 'in'],
            'deployment__deployment_device_ID': ['exact', 'in', 'icontains'],
            'deployment__device': ['exact', 'in'],
            'file_type': ['exact', 'in'],
            'file_type__name': ['exact', 'icontains', 'in'],
            'file_name': ['exact', 'icontains', 'in'],
            'file_size': ['lte', 'gte'],
            'file_format': ['exact', 'icontains', 'in'],
            'upload_dt': ['exact', 'gte', 'lte'],
            'recording_dt': ['exact', 'date__exact', 'gte', 'lte', 'date__gte', 'date__lte', 'time__gte', 'time__lte'],
            'local_storage': ['exact'],
            'archived': ['exact'],
            'original_name': ['exact', 'icontains', 'in'],
            'favourite_of__id': ['exact', 'contains'],
        })


class DeviceModelFilter(GenericFilterMixIn, ExtraDataFilterMixIn):
    """
    FilterSet for DeviceModel, allowing queries on type and name fields.

    Meta:
        model: DeviceModel
        fields: type, type__name, name (with various lookup options)
    """

    class Meta:
        model = DeviceModel
        fields = GenericFilterMixIn.get_fields().copy()
        fields.update({
            'type': ['exact', 'in'],
            'type__name': ['exact', 'icontains', 'in'],
            'name': ['exact', 'icontains', 'in'],
        })
