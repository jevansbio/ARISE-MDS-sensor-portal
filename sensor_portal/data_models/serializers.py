from datetime import datetime as dt

from bridgekeeper import perms
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.utils import timezone as djtimezone
from PIL import ExifTags, Image
from rest_framework import serializers
from rest_framework_gis import serializers as geoserializers
from timezone_field.rest_framework import TimeZoneSerializerField
from utils.serializers import (CheckFormMixIn, CreatedModifiedMixIn,
                               InstanceGetMixIn, ManagerMixIn, OwnerMixIn,
                               SlugRelatedGetOrCreateField)
from utils.validators import check_two_keys

from . import validators
from .models import (DataFile, DataType, Deployment, Device, DeviceModel,
                     Project, Site)


class DeploymentFieldsMixIn(InstanceGetMixIn, OwnerMixIn, ManagerMixIn, CreatedModifiedMixIn, CheckFormMixIn, serializers.ModelSerializer):
    """
    Mixin serializer for deployment-related fields and logic.

    Provides device, project, site, and timezone relationships, as well as
    custom validation for deployments, permission checks, and GeoJSON output.
    """

    device_type = serializers.SlugRelatedField(
        slug_field='name', queryset=DataType.objects.all(), required=False, allow_null=True)
    device_type_ID = serializers.PrimaryKeyRelatedField(source="device_type", queryset=DataType.objects.all(),
                                                        required=False, allow_null=True)
    device = serializers.SlugRelatedField(
        slug_field='device_ID', queryset=Device.objects.all(), required=False)
    device_ID = serializers.PrimaryKeyRelatedField(source="device", queryset=Device.objects.all(),
                                                   required=False)
    project = serializers.SlugRelatedField(many=True,
                                           slug_field='project_ID',
                                           queryset=Project.objects.all().exclude(name=settings.GLOBAL_PROJECT_ID),
                                           allow_null=True,
                                           required=False)
    project_ID = serializers.PrimaryKeyRelatedField(source="project",
                                                    many=True,
                                                    queryset=Project.objects.all().exclude(name=settings.GLOBAL_PROJECT_ID),
                                                    required=False,
                                                    allow_null=True)
    site = SlugRelatedGetOrCreateField(slug_field='name',
                                       queryset=Site.objects.all(),
                                       required=False, allow_null=True)
    site_ID = serializers.PrimaryKeyRelatedField(source="site", queryset=Site.objects.all(),
                                                 required=False, allow_null=True)

    time_zone = TimeZoneSerializerField(
        use_pytz=True, default=settings.TIME_ZONE)

    deployment_start = serializers.DateTimeField(
        default=djtimezone.now(), default_timezone=djtimezone.utc)
    deployment_end = serializers.DateTimeField(
        default_timezone=djtimezone.utc, required=False, allow_null=True)

    def to_representation(self, instance):
        """
        Customize serialized output for deployments, including GeoJSON and permissions.
        """
        initial_rep = super(DeploymentFieldsMixIn,
                            self).to_representation(instance)

        if initial_rep.get('properties') is not None:
            geojson_rep = initial_rep
            initial_rep = initial_rep.get('properties')
        else:
            geojson_rep = None

        device_model = instance.device.model
        device_type = instance.device_type
        initial_rep["colour"] = device_model.colour if device_model.colour != "" else device_type.colour
        initial_rep["symbol"] = device_model.symbol if device_model.symbol != "" else device_type.symbol

        projects_no_global = [(x, y) for x, y in zip(
            initial_rep["project"], initial_rep["project_ID"]) if x != settings.GLOBAL_PROJECT_ID]

        initial_rep["project"], initial_rep["project_ID"] = zip(
            *projects_no_global) if projects_no_global else ([], [])

        if geojson_rep is not None:
            geojson_rep['properties'] = initial_rep

        return initial_rep

    class Meta:
        model = Deployment
        exclude = ['last_image']

    def __init__(self, *args, **kwargs):
        """
        Initialize DeploymentFieldsMixIn, set management permission and flags.
        """
        self.clear_project = False
        self.management_perm = 'data_models.change_deployment'
        super(DeploymentFieldsMixIn, self).__init__(*args, **kwargs)

    def create(self, *args, **kwargs):
        """
        Create and persist a deployment instance.
        """
        instance = super(DeploymentFieldsMixIn, self).create(*args, **kwargs)
        instance.save()
        return instance

    def update(self, *args, **kwargs):
        """
        Update and persist a deployment instance.
        """
        instance = super(DeploymentFieldsMixIn, self).update(*args, **kwargs)
        instance.save()
        return instance

    def validate(self, data):
        """
        Validate deployment data for required relationships and constraints.
        Raises ValidationError on failure.
        """
        if self.form_submission & (data.get('project') is None):
            data['project'] = []

        data = super().validate(data)

        if not self.partial:
            result, message, data = check_two_keys(
                'device',
                'device_ID',
                data,
                Device,
                self.form_submission
            )
            if not result:
                raise serializers.ValidationError(message)

            result, message, data = check_two_keys(
                'site',
                'site_ID',
                data,
                Site,
                self.form_submission
            )
            if not result:
                raise serializers.ValidationError(message)

        result, message = validators.deployment_check_type(self.instance_get('device_type', data),
                                                           self.instance_get('device', data))
        if not result:
            raise serializers.ValidationError(message)

        result, message = validators.deployment_start_time_after_end_time(self.instance_get('deployment_start', data),
                                                                          self.instance_get('deployment_end', data))
        if not result:
            raise serializers.ValidationError(message)

        result, message = validators.deployment_check_overlap(self.instance_get('deployment_start', data),
                                                              self.instance_get(
            'deployment_end', data),
            self.instance_get(
            'device', data),
            self.instance_get('id', data))
        if not result:
            raise serializers.ValidationError(message)

        return data


class DeploymentSerializer(DeploymentFieldsMixIn, serializers.ModelSerializer):
    """
    Serializer for Deployment model for regular (non-GeoJSON) API endpoints.
    """

    class Meta:
        model = Deployment
        exclude = DeploymentFieldsMixIn.Meta.exclude + ['point']


class DeploymentSerializer_GeoJSON(DeploymentFieldsMixIn, geoserializers.GeoFeatureModelSerializer):
    """
    Serializer for Deployment model in GeoJSON format.
    Uses the 'point' field as the geographic representation.
    """

    def __init__(self, *args, **kwargs):
        self.Meta.geo_field = "point"
        super(DeploymentSerializer_GeoJSON, self).__init__(*args, **kwargs)


class ProjectSerializer(OwnerMixIn, ManagerMixIn, CreatedModifiedMixIn, serializers.ModelSerializer):
    """
    Serializer for Project model with ownership, management, and timestamps.
    """

    is_active = serializers.BooleanField(read_only=True)

    class Meta:
        model = Project
        exclude = ["data_storages", "automated_tasks", "archive"]

    def __init__(self, *args, **kwargs):
        self.management_perm = 'data_models.change_project'
        super(ProjectSerializer, self).__init__(*args, **kwargs)


class DeviceModelSerializer(CreatedModifiedMixIn, OwnerMixIn, serializers.ModelSerializer):
    """
    Serializer for DeviceModel with type fields, handler info, and ownership/timestamps.
    """

    type = serializers.SlugRelatedField(
        slug_field='name', queryset=DataType.objects.all(), required=False)
    type_ID = serializers.PrimaryKeyRelatedField(source="type", queryset=DataType.objects.all(),
                                                 required=False)

    class Meta:
        model = DeviceModel
        exclude = []

    def to_representation(self, instance):
        """
        Add data handler info to serialized DeviceModel if available.
        """
        initial_rep = super(DeviceModelSerializer,
                            self).to_representation(instance)

        handler = settings.DATA_HANDLERS.get_handler(
            instance.type.name, instance.name)
        if handler:
            initial_rep["data_handler"] = handler.full_name
            initial_rep["data_handler_id"] = handler.id
        else:
            initial_rep["data_handler"] = None
            initial_rep["data_handler_id"] = None
        return initial_rep


class DeviceSerializer(OwnerMixIn, ManagerMixIn, CreatedModifiedMixIn, CheckFormMixIn, serializers.ModelSerializer):
    """
    Serializer for Device model with type/model, user fields, and permission-based filtering.
    """

    type = serializers.SlugRelatedField(
        slug_field='name', queryset=DataType.objects.all(), required=False)
    type_ID = serializers.PrimaryKeyRelatedField(source="type", queryset=DataType.objects.all(),
                                                 required=False)
    model = serializers.SlugRelatedField(
        slug_field='name', queryset=DeviceModel.objects.all(), required=False)
    model_ID = serializers.PrimaryKeyRelatedField(source="model", queryset=DeviceModel.objects.all(),
                                                  required=False)

    username = serializers.CharField(required=False)
    password = serializers.CharField(required=False, write_only=True)
    is_active = serializers.BooleanField(read_only=True)

    class Meta:
        model = Device
        exclude = []

    def __init__(self, *args, **kwargs):
        self.management_perm = 'data_models.change_device'
        super(DeviceSerializer, self).__init__(*args, **kwargs)

    def to_representation(self, instance):
        """
        Remove sensitive fields, filter by permissions, and add handler/color/symbol info.
        """
        initial_rep = super(DeviceSerializer, self).to_representation(instance)
        fields_to_pop = ["username"]
        fields_to_always_pop = ["password"]
        [initial_rep.pop(field, '') for field in fields_to_always_pop]
        if self.context.get('request'):
            user_is_manager = self.context['request'].user.has_perm(
                self.management_perm, obj=instance)
        else:
            user_is_manager = False
        if not user_is_manager:
            [initial_rep.pop(field, '') for field in fields_to_pop]

        device_model = instance.model
        device_type = instance.type
        initial_rep["colour"] = device_model.colour if device_model.colour != "" else device_type.colour
        initial_rep["symbol"] = device_model.symbol if device_model.symbol != "" else device_type.symbol

        handler = settings.DATA_HANDLERS.get_handler(
            instance.type.name, instance.model.name)
        if handler:
            initial_rep["data_handler"] = handler.full_name
            initial_rep["data_handler_id"] = handler.id
        else:
            initial_rep["data_handler"] = None
            initial_rep["data_handler_id"] = None

        return initial_rep

    def validate(self, data):
        """
        Validate device data, ensuring a model is attached and fields are consistent.
        """
        data = super().validate(data)

        if not self.partial:
            result, message, data = check_two_keys(
                'model',
                'model_ID',
                data,
                Device,
                self.form_submission
            )
            if not result:
                raise serializers.ValidationError(message)

        return data


class DataFileCheckSerializer(serializers.Serializer):
    """
    Serializer for checking if files exist in the system.
    """

    file_names = serializers.ListField(
        child=serializers.CharField(), required=False
    )
    original_names = serializers.ListField(
        child=serializers.CharField(), required=False
    )


class DataFileSerializer(CreatedModifiedMixIn, serializers.ModelSerializer):
    """
    Serializer for DataFile model, including deployment, file type, and user-specific flags.
    """

    deployment = serializers.SlugRelatedField(
        slug_field='deployment_device_ID', queryset=Deployment.objects.all(), required=False)
    deployment_ID = serializers.PrimaryKeyRelatedField(source="deployment", queryset=Deployment.objects.all(),
                                                       required=False)
    file_type = serializers.StringRelatedField()
    recording_dt = serializers.DateTimeField(default_timezone=djtimezone.utc)

    def to_representation(self, instance):
        """
        Add 'favourite' and 'can_annotate' to serialized DataFile based on request user.
        """
        initial_rep = super(DataFileSerializer,
                            self).to_representation(instance)
        if self.context.get('request'):
            request_user = self.context['request'].user
            initial_rep["favourite"] = instance.favourite_of.all().filter(
                pk=request_user.pk).exists()
            initial_rep.pop('path')
            initial_rep["can_annotate"] = perms['data_models.annotate_datafile'].check(
                request_user, instance)

        return initial_rep

    class Meta:
        model = DataFile
        exclude = ["do_not_remove", "local_path", "favourite_of",
                   "tar_file"]

    def validate(self, data):
        """
        Validate DataFile, ensuring recording date and deployment are consistent.
        """
        data = super().validate(data)

        result, message = validators.data_file_in_deployment(
            data.get('recording_dt', self.instance.recording_dt), data.get('deployment', self.instance.deployment))
        if not result:
            raise serializers.ValidationError(message)
        return data


class DataFileUploadSerializer(serializers.Serializer):
    """
    Serializer for uploading data files with associated metadata and validation.
    """

    device = serializers.CharField(required=False)
    device_ID = serializers.IntegerField(required=False)
    deployment = serializers.CharField(required=False)
    deployment_ID = serializers.IntegerField(required=False)

    files = serializers.ListField(child=serializers.FileField(
        allow_empty_file=False, max_length=None), required=True)
    file_names = serializers.ListField(child=serializers.CharField(
    ), required=False)
    extra_data = serializers.ListField(
        child=serializers.JSONField(binary=True), required=False)
    recording_dt = serializers.ListField(
        child=serializers.DateTimeField(), required=False)
    autoupdate = serializers.BooleanField(default=False)
    rename = serializers.BooleanField(default=True)
    check_filename = serializers.BooleanField(default=True)
    data_types = serializers.ListField(child=serializers.SlugRelatedField(slug_field='name',
                                                                          queryset=DataType.objects.all()),
                                       required=False)
    is_active = serializers.BooleanField(
        source="deployment.is_active", read_only=True)

    def create(self, validated_data):
        """
        Return validated upload data unchanged.
        """
        return validated_data

    def validate(self, data):
        """
        Validate upload data for existence, deployment/device, and recording_dt.
        """
        data = super().validate(data)
        deployment = data.get('deployment')
        deployment_ID = data.get('deployment_ID')
        device = data.get('device')
        device_ID = data.get('device_ID')

        if deployment is None and deployment_ID is None and device is None and device_ID is None:
            raise serializers.ValidationError(
                "A deployment or a device must be supplied")

        if deployment or deployment_ID:
            try:
                deployment_object = Deployment.objects.get(Q(Q(deployment_device_ID=deployment) |
                                                             Q(pk=deployment_ID)))
            except ObjectDoesNotExist:
                raise serializers.ValidationError({"deployment":
                                                   f"Deployment {deployment} does not exist",
                                                   "deployment_ID": f"Deployment ID {deployment_ID} does not exist"})
            data['deployment_object'] = deployment_object
            data['device_object'] = deployment_object.device
        elif device or device_ID:
            try:
                device_object = Device.objects.get(
                    Q(Q(device_ID=device) | Q(pk=device_ID)))
            except ObjectDoesNotExist:
                raise serializers.ValidationError({"device":
                                                   f"Device {device} does not exist",
                                                   "device_ID": f"Device ID {device_ID} does not exist"})
            data['device_object'] = device_object

        files = data.get("files")
        recording_dt = data.get('recording_dt')
        if files:
            if recording_dt is not None:
                if len(recording_dt) > 1 and len(recording_dt) != len(data.get('files')):
                    raise serializers.ValidationError(
                        {"recording_dt": "More than one recording_dt was supplied, but the number does not match the number of files"})

        return data

    def update(self, validated_data):
        """
        Not used.
        """
        pass


class SiteSerializer(serializers.ModelSerializer):
    """
    Serializer for Site model (all fields).
    """
    class Meta:
        model = Site
        fields = '__all__'


class DataTypeSerializer(serializers.ModelSerializer):
    """
    Serializer for DataType model (all fields).
    """
    class Meta:
        model = DataType
        fields = '__all__'


class GenericJobSerializer(serializers.Serializer):
    """
    Serializer for displaying generic jobs.

    Attributes:
        id (int): Numeric job ID.
        name (str): Name of the job.
        task_name (str): Celery task name.
        data_type (str): Expected data type.
        admin_only (bool): If superuser is required.
        max_items (int): Max items for the job.
        default_args (dict): Default arguments as JSON.
    """
    id = serializers.IntegerField()
    name = serializers.CharField()
    task_name = serializers.CharField()
    data_type = serializers.CharField()
    admin_only = serializers.BooleanField()
    max_items = serializers.IntegerField()
    default_args = serializers.JSONField()
