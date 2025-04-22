from datetime import datetime as dt

import magic
from bridgekeeper import perms
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

# from user_management.serializers import (
#     UserGroupMemberSerializer,
#     UserGroupProfileSerializer,
# )


class DeploymentFieldsMixIn(InstanceGetMixIn, OwnerMixIn, ManagerMixIn, CreatedModifiedMixIn, CheckFormMixIn,
                            serializers.ModelSerializer):
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
                                           queryset=Project.objects.all(),
                                           allow_null=True,
                                           required=False)
    project_ID = serializers.PrimaryKeyRelatedField(source="project",
                                                    many=True,
                                                    queryset=Project.objects.all(),
                                                    required=False,
                                                    allow_null=True)
    site = SlugRelatedGetOrCreateField(slug_field='short_name',
                                       queryset=Site.objects.all(),
                                       required=False, allow_null=True)
    site_ID = serializers.PrimaryKeyRelatedField(source="site", queryset=Site.objects.all(),
                                                 required=False, allow_null=True)

    time_zone = TimeZoneSerializerField(use_pytz=True)

    # always return in UTC regardless of server setting
    deployment_start = serializers.DateTimeField(
        default=djtimezone.now(), default_timezone=djtimezone.utc)
    deployment_end = serializers.DateTimeField(
        default_timezone=djtimezone.utc, required=False, allow_null=True)

    # check project permissions here or in viewpoint

    # Add new field for last_upload
    last_upload = serializers.SerializerMethodField()
    folder_size = serializers.SerializerMethodField()

    def get_folder_size(self, instance):
        return instance.get_folder_size()
    
    def get_last_upload(self, instance):
        """Get the datetime of the most recent file upload for this deployment"""
        return instance.get_last_upload()

    def to_representation(self, instance):
        initial_rep = super(DeploymentFieldsMixIn,
                            self).to_representation(instance)
        if not self.context.get('request'):
            initial_rep.pop('thumb_url')
        return initial_rep

    class Meta:
        model = Deployment
        exclude = ['last_image']

    def __init__(self, *args, **kwargs):
        self.clear_project = False
        self.management_perm = 'data_models.change_deployment'
        self.form_submission = False
        super(DeploymentFieldsMixIn, self).__init__(*args, **kwargs)

    def create(self, *args, **kwargs):
        instance = super(DeploymentFieldsMixIn, self).create(*args, **kwargs)
        instance.save()
        return instance

    def update(self, *args, **kwargs):
        instance = super(DeploymentFieldsMixIn, self).update(*args, **kwargs)
        instance.save()
        return instance

    def validate(self, data):
        if self.form_submission and (data.get('project') is None):
            data['project'] = []

        data = super().validate(data)

        # #check if a device type has been set via either method
        # result, message, data = validators.check_two_keys(
        #     'device_type',
        #     'device_type_ID',
        #     data,
        #     DataType
        # )
        # if not result:
        #     raise serializers.ValidationError(message)

        if not self.partial:
            # check if a device has been attached (via either method)
            result, message, data = check_two_keys(
                'device',
                'device_ID',
                data,
                Device,
                self.form_submission
            )
            if not result:
                raise serializers.ValidationError(message)

            # # check if a site has been attached (via either method)
            # result, message, data = check_two_keys(
            #     'site',
            #     'site_ID',
            #     data,
            #     Site,
            #     self.form_submission
            # )
            # if not result:
            #     raise serializers.ValidationError(message)
        print(data)
        result, message = validators.deployment_check_type(self.instance_get('device_type', data),
                                                           self.instance_get('device', data))
        if not result:
            raise serializers.ValidationError(message)

        result, message = validators.deployment_start_time_after_end_time(self.instance_get('deployment_start', data),
                                                                          self.instance_get('deployment_end', data))
        if not result:
            raise serializers.ValidationError(message)

        print(data)

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

    class Meta:
        model = Deployment
        exclude = DeploymentFieldsMixIn.Meta.exclude+['point']


class DeploymentSerializer_GeoJSON(DeploymentFieldsMixIn, geoserializers.GeoFeatureModelSerializer):
    def __init__(self, *args, **kwargs):
        self.Meta.geo_field = "point"
        super(DeploymentSerializer_GeoJSON, self).__init__(*args, **kwargs)


class ProjectSerializer(OwnerMixIn, ManagerMixIn, CreatedModifiedMixIn, serializers.ModelSerializer):
    is_active = serializers.BooleanField(
        read_only=True)

    class Meta:
        model = Project
        exclude = []

    def __init__(self, *args, **kwargs):
        self.management_perm = 'data_models.change_project'
        super(ProjectSerializer, self).__init__(*args, **kwargs)


class DeviceModelSerializer(CreatedModifiedMixIn, OwnerMixIn, ManagerMixIn, serializers.ModelSerializer):
    class Meta:
        model = DeviceModel
        exclude = []


class DeviceSerializer(OwnerMixIn, ManagerMixIn, CreatedModifiedMixIn, CheckFormMixIn, serializers.ModelSerializer):
    type = serializers.SlugRelatedField(
        slug_field='name', queryset=DataType.objects.all(), required=False)
    type_ID = serializers.PrimaryKeyRelatedField(source="type", queryset=DataType.objects.all(),
                                                 required=False)
    model = serializers.SlugRelatedField(
        slug_field='name', queryset=DeviceModel.objects.all(), required=False)
    model_ID = serializers.PrimaryKeyRelatedField(source="model", queryset=DeviceModel.objects.all(),
                                                  required=False)

    username = serializers.CharField(required=False)
    password = serializers.CharField(required=False)
    is_active = serializers.BooleanField(read_only=True)

    folder_size = serializers.SerializerMethodField()
    last_upload = serializers.SerializerMethodField()

    class Meta:
        model = Device
        exclude = []

    def __init__(self, *args, **kwargs):
        self.management_perm = 'data_models.change_device'
        super(DeviceSerializer, self).__init__(*args, **kwargs)
    
    def get_folder_size(self, instance):
        return instance.get_folder_size()

    def get_last_upload(self, instance):
        return instance.get_last_upload()

    def to_representation(self, instance):
        initial_rep = super(DeviceSerializer, self).to_representation(instance)
        fields_to_pop = [
            "username"
        ]
        fields_to_always_pop = [
            "password"
        ]
        [initial_rep.pop(field, '') for field in fields_to_always_pop]
        if self.context.get('request'):
            user_is_manager = self.context['request'].user.has_perm(
                self.management_perm, obj=instance)
        else:
            user_is_manager = False
        if not user_is_manager:
            [initial_rep.pop(field, '') for field in fields_to_pop]
        return initial_rep

    def validate(self, data):
        data = super().validate(data)

        if not self.partial:
            # check if a model has been attached (via either method)
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


class DataFileSerializer(serializers.ModelSerializer):
    deployment_device_ID = serializers.CharField(
        source='deployment.deployment_device_ID', read_only=True)
    recording_datetime = serializers.DateTimeField(
        source='recording_dt', read_only=True)
    is_favourite = serializers.SerializerMethodField()
    
    # Audio-specific fields
    config = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    sample_rate = serializers.IntegerField(required=False, allow_null=True)
    file_length = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    # Quality check fields
    quality_score = serializers.FloatField(read_only=True)
    quality_issues = serializers.ListField(read_only=True)
    quality_check_dt = serializers.DateTimeField(read_only=True)
    quality_check_status = serializers.CharField(read_only=True)

    class Meta:
        model = DataFile
        fields = ('id', 'deployment_device_ID', 'deployment', 'file_name', 'file_format',
                  'file_size', 'recording_datetime', 'file_type', 'path', 'file_url',
                  'thumb_url', 'is_favourite', 'tag', 'upload_dt', 'extra_data',
                  'config', 'sample_rate', 'file_length',
                  'quality_score', 'quality_issues', 'quality_check_dt', 'quality_check_status')
        read_only_fields = ('id', 'deployment_device_ID', 'upload_dt', 'file_url', 'thumb_url')

    def get_is_favourite(self, obj):
        user = None
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            user = request.user
        if user:
            return obj.favourite_of.filter(pk=user.pk).exists()
        return False

    def validate(self, data):
        data = super().validate(data)

        result, message = validators.data_file_in_deployment(
            data.get('recording_dt', self.instance.recording_dt), data.get('deployment', self.instance.deployment))
        if not result:
            raise serializers.ValidationError(message)
        return data


class DataFileUploadSerializer(serializers.Serializer):
    device = serializers.CharField(required=False)
    device_ID = serializers.IntegerField(required=False)
    deployment = serializers.CharField(required=False)
    deployment_ID = serializers.IntegerField(required=False)

    files = serializers.ListField(child=serializers.FileField(
        allow_empty_file=False, max_length=None), required=True)
    file_names = serializers.ListField(child=serializers.CharField(
    ), required=False)
    extra_data = serializers.ListField(
        child=serializers.JSONField(), required=False)
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
        return validated_data

    def validate(self, data):
        data = super().validate(data)
        deployment = data.get('deployment')
        deployment_ID = data.get('deployment_ID')
        device = data.get('device')
        device_ID = data.get('device_ID')

        #  Check a deployment or device is supplied
        if deployment is None and deployment_ID is None and device is None and device_ID is None:
            raise serializers.ValidationError(
                "A deployment or a device must be supplied")

        # Check if deployment or device exists
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

        #  if not an image, user must supply the recording date time
        files = data.get("files")
        recording_dt = data.get('recording_dt')
        if files:
            is_not_image = ["image" not in magic.from_buffer(
                x.read(), mime=True) for x in files]
            if any(is_not_image) and recording_dt is None:
                raise serializers.ValidationError(
                    {"recording_dt": "Recording date times can only be extracted from images, please provide 'recording_dt' or upload only images"})

            #  check recording_dt and number of files match
            if recording_dt is not None:

                if len(recording_dt) > 1 and len(recording_dt) != len(data.get('files')):
                    raise serializers.ValidationError(
                        {"recording_dt": "More than one recording_dt was supplied, but the number does not match the number of files"})

        return data

    def update(self, validated_data):
        # Not used
        pass


class SiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Site
        fields = '__all__'


class DataTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataType
        fields = '__all__'


def get_image_recording_dt(uploaded_file):
    si = uploaded_file.file
    image = Image.open(si)
    exif = image.getexif()
    exif_tags = {ExifTags.TAGS[k]: v for k,
                 v in exif.items() if k in ExifTags.TAGS}
    recording_dt = exif_tags.get('DateTimeOriginal')
    if recording_dt is None:
        recording_dt = exif_tags.get('DateTime')
    if recording_dt is None:
        raise serializers.ValidationError(f"Unable to get recording_dt from image {uploaded_file.name}, "
                                          f"consider supplying recording_dt manually")

    return dt.strptime(recording_dt, '%Y:%m:%d %H:%M:%S')
