import os

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.utils import timezone as djtimezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework_gis import filters as filters_gis
from utils.viewsets import (AddOwnerViewSetMixIn, CheckAttachmentViewSetMixIn,
                            CheckFormViewSetMixIn,
                            OptionalPaginationViewSetMixIn)

from .file_handling_functions import create_file_objects
from .filtersets import *
from .models import DataFile, DataType, Deployment, Device, Project, Site
from .permissions import perms
from .plotting_functions import get_all_file_metric_dicts
from .serializers import (DataFileSerializer, DataFileUploadSerializer,
                          DataTypeSerializer, DeploymentSerializer,
                          DeploymentSerializer_GeoJSON, DeviceSerializer,
                          ProjectSerializer, SiteSerializer)


class DeploymentViewSet(CheckAttachmentViewSetMixIn, AddOwnerViewSetMixIn, CheckFormViewSetMixIn, OptionalPaginationViewSetMixIn):
    search_fields = ['deployment_device_ID',
                     'device__name', 'device__device_ID',
                     'coordinate_uncertainty', 'gps_device',
                     'habitat', 'protocol_checklist']
    ordering_fields = ordering = [
        'deployment_device_ID', 'created_on', 'device_type']
    queryset = Deployment.objects.all().distinct()
    filterset_class = DeploymentFilter
    filter_backends = viewsets.ModelViewSet.filter_backends + \
        [filters_gis.InBBoxFilter]

    def get_serializer_class(self):
        if 'geoJSON' in self.request.GET.keys():
            return DeploymentSerializer_GeoJSON
        else:
            return DeploymentSerializer

    @action(detail=True, methods=['get'])
    def metrics(self, request, pk=None):
        deployment = self.get_object()
        user = request.user
        data_files = perms['data_models.view_datafile'].filter(
            user, deployment.files.all())
        if not data_files.exists():
            return Response({}, status=status.HTTP_200_OK)
        file_metric_dicts = get_all_file_metric_dicts(data_files)
        
        # Add folder size information
        file_metric_dicts['folder_size'] = deployment.get_folder_size()
        
        # Add last upload information
        last_upload = deployment.get_last_upload()
        if last_upload:
            file_metric_dicts['last_upload'] = last_upload
        
        return Response(file_metric_dicts, status=status.HTTP_200_OK)
        
    @action(detail=True, methods=['post'])
    def update_geo_info(self, request, pk=None):
        deployment = self.get_object()
        user = request.user
        
        if not user.has_perm('data_models.change_deployment', deployment):
            raise PermissionDenied("You don't have permission to update this deployment geo information")
            
        geo_fields = [
            'coordinate_uncertainty', 'gps_device', 'mic_height', 
            'mic_direction', 'habitat', 'protocol_checklist', 
            'score', 'comment'
        ]
        
        updates = {}
        for field in geo_fields:
            if field in request.data:
                updates[field] = request.data[field]
                
        # Update lat/long if provided
        if 'latitude' in request.data and 'longitude' in request.data:
            updates['latitude'] = request.data['latitude']
            updates['longitude'] = request.data['longitude']
                
        for key, value in updates.items():
            setattr(deployment, key, value)
            
        deployment.save()
        return Response(DeploymentSerializer(deployment).data, status=status.HTTP_200_OK)
        
    @action(detail=False, methods=['post'])
    def create_from_form(self, request):
        user = request.user
        
        data = request.data
        
        # Map form field names to model field names
        field_mapping = {
            'DeploymentID': 'deployment_ID',
            'Country': 'country',
            'Site': 'site_name',
            'StartDate': 'deployment_start',
            'EndDate': 'deployment_end',
            'Latitude': 'latitude',
            'Longitude': 'longitude',
            'Coordinate Uncertainty': 'coordinate_uncertainty',
            'GPS device': 'gps_device',
            'Microphone Height': 'mic_height',
            'Microphone Direction': 'mic_direction',
            'Habitat': 'habitat',
            'Score': 'score',
            'Protocol Checklist': 'protocol_checklist',
            'Adresse e-mail': 'user_email',
            'Comment/remark': 'comment'
        }
        
        # Create deployment data dictionary
        deployment_data = {}
        
        # Map form fields to model fields
        for form_field, model_field in field_mapping.items():
            if form_field in data:
                deployment_data[model_field] = data[form_field]
        
        # Handle active data if present
        if 'ActiveData' in data and isinstance(data['ActiveData'], dict):
            active_data = data['ActiveData']
            if 'batteryLevel' in active_data:
                deployment_data['battery_level'] = active_data['batteryLevel']
            # We no longer store last_upload or folder_size as they're calculated on-demand
        
        # Create serializer with the formatted data
        serializer = self.get_serializer(data=deployment_data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def check_attachment(self, serializer):
        project_objects = serializer.validated_data.get('project')
        if project_objects is not None:
            for project_object in project_objects:
                if (not self.request.user.has_perm('data_models.change_project', project_object)) and\
                        (project_object.name != settings.GLOBAL_PROJECT_ID):
                    raise PermissionDenied(
                        f"You don't have permission to add a deployment to {project_object.project_ID}")
        device_object = serializer.validated_data.get('device')
        if device_object is not None:
            if not self.request.user.has_perm('data_models.change_device', device_object):
                raise PermissionDenied(
                    f"You don't have permission to deploy {device_object.device_ID}")

    @action(detail=True, methods=['get'])
    def folder_size(self, request, pk=None):
        """
        Get the total size of all files in this deployment
        """
        deployment = self.get_object()
        
        # Get the unit if specified
        unit = request.query_params.get('unit', 'MB')
        
        folder_size = deployment.get_folder_size(unit)
        
        return Response({'folder_size': folder_size, 'unit': unit}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'])
    def last_upload(self, request, pk=None):
        """
        Get the datetime of the most recent file upload for this deployment
        """
        deployment = self.get_object()
        
        last_upload = deployment.get_last_upload()
        
        if last_upload:
            return Response({'last_upload': last_upload}, status=status.HTTP_200_OK)
        else:
            return Response({'last_upload': None}, status=status.HTTP_200_OK)


class ProjectViewSet(AddOwnerViewSetMixIn, OptionalPaginationViewSetMixIn):
    serializer_class = ProjectSerializer
    queryset = Project.objects.all().distinct()
    filterset_class = ProjectFilter
    search_fields = ['project_ID', 'name', 'organization']

    @action(detail=True, methods=['get'])
    def metrics(self, request, pk=None):
        project = self.get_object()
        user = request.user
        data_files = perms['data_models.view_datafile'].filter(
            user, DataFile.objects.filter(deployment__project=project))
        if not data_files.exists():
            return Response({}, status=status.HTTP_200_OK)
        file_metric_dicts = get_all_file_metric_dicts(data_files, False)
        return Response(file_metric_dicts, status=status.HTTP_200_OK)


class DeviceViewSet(AddOwnerViewSetMixIn, OptionalPaginationViewSetMixIn):
    serializer_class = DeviceSerializer
    queryset = Device.objects.all().distinct()
    filterset_class = DeviceFilter
    search_fields = ['device_ID', 'name', 'model__name', 'country', 'site_name', 'habitat']

    @action(detail=True, methods=['get'])
    def metrics(self, request, pk=None):
        device = self.get_object()
        user = request.user
        data_files = perms['data_models.view_datafile'].filter(
            user, DataFile.objects.filter(deployment__device=device))
        if not data_files.exists():
            return Response({}, status=status.HTTP_200_OK)
        file_metric_dicts = get_all_file_metric_dicts(data_files)
        
        # Add folder size information
        file_metric_dicts['folder_size'] = device.get_folder_size()
        
        # Add last upload information
        last_upload = device.get_last_upload()
        if last_upload:
            file_metric_dicts['last_upload'] = last_upload
        
        return Response(file_metric_dicts, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        device = self.get_object()
        user = request.user
        
        if not user.has_perm('data_models.change_device', device):
            raise PermissionDenied("You don't have permission to update this device status")
            
        status_fields = ['battery_level']  # Removed last_upload and folder_size
        updates = {}
        
        for field in status_fields:
            if field in request.data:
                updates[field] = request.data[field]
                
        if 'start_date' in request.data:
            updates['start_date'] = request.data['start_date']
            
        if 'end_date' in request.data:
            updates['end_date'] = request.data['end_date']
        
        for key, value in updates.items():
            setattr(device, key, value)
            
        device.save()
        
        # Get response data with calculated fields
        response_data = DeviceSerializer(device).data
        response_data['folder_size'] = device.get_folder_size()
        
        # Add last upload information
        last_upload = device.get_last_upload()
        if last_upload:
            response_data['last_upload'] = last_upload
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    @action(detail=True, methods=['post'])
    def update_form_info(self, request, pk=None):
        device = self.get_object()
        user = request.user
        
        if not user.has_perm('data_models.change_device', device):
            raise PermissionDenied("You don't have permission to update this device information")
            
        form_fields = [
            'country', 'site_name', 'coordinate_uncertainty', 'gps_device',
            'mic_height', 'mic_direction', 'habitat', 'score',
            'protocol_checklist', 'user_email', 'comment'
        ]
        
        updates = {}
        for field in form_fields:
            if field in request.data:
                updates[field] = request.data[field]
                
        for key, value in updates.items():
            setattr(device, key, value)
            
        device.save()
        return Response(DeviceSerializer(device).data, status=status.HTTP_200_OK)
        
    @action(detail=False, methods=['post'])
    def create_from_json(self, request):
        user = request.user
        
        data = request.data
        
        # Map field names if needed
        device_data = {
            'device_ID': data.get('device_ID'),
            'name': data.get('name'),
            'comment': data.get('extra_data', {}).get('comment')
        }
        
        # Add model if provided
        if 'model_id' in data:
            device_data['model'] = data['model_id']
            
        # Handle any other mappings needed for your specific JSON format
        
        # Create serializer with the formatted data
        serializer = self.get_serializer(data=device_data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @action(detail=True, methods=['get'])
    def folder_size(self, request, pk=None):
        """
        Get the total size of all files associated with this device
        """
        device = self.get_object()
        
        # Get the unit if specified
        unit = request.query_params.get('unit', 'MB')
        
        folder_size = device.get_folder_size(unit)
        
        return Response({'folder_size': folder_size, 'unit': unit}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'])
    def last_upload(self, request, pk=None):
        """
        Get the datetime of the most recent file upload for this device
        """
        device = self.get_object()
        
        last_upload = device.get_last_upload()
        
        if last_upload:
            return Response({'last_upload': last_upload}, status=status.HTTP_200_OK)
        else:
            return Response({'last_upload': None}, status=status.HTTP_200_OK)


class DataFileViewSet(CheckAttachmentViewSetMixIn, OptionalPaginationViewSetMixIn):

    queryset = DataFile.objects.all().distinct()
    filterset_class = DataFileFilter
    search_fields = ['file_name',
                     'deployment__deployment_device_ID',
                     'deployment__device__name',
                     'deployment__device__device_ID',
                     '=tag',
                     'config',
                     'sample_rate']

    @action(detail=False, methods=['get'])
    def test(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        # is this also filtering by permissions?
        print(self.filterset_class)
        print(queryset.count())
        return Response({queryset.count()}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=['data_models.view_datafile'])
    def favourite_file(self, request):
        data_file = self.get_object()
        user = request.user
        if user:
            if data_file.favourite_of.all().filter(pk=user.pk).exists():
                data_file.favourite_of.remove(user)
            else:
                data_file.favourite_of.add(user)
            return Response({}, status=status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_403_FORBIDDEN)

    @action(detail=True, methods=['post'])
    def update_audio_info(self, request, pk=None):
        data_file = self.get_object()
        user = request.user
        
        if not user.has_perm('data_models.change_datafile', data_file):
            raise PermissionDenied("You don't have permission to update this file information")
            
        audio_fields = ['config', 'sample_rate', 'file_length']
        
        updates = {}
        for field in audio_fields:
            if field in request.data:
                updates[field] = request.data[field]
                
        for key, value in updates.items():
            setattr(data_file, key, value)
            
        data_file.save()
        return Response(DataFileSerializer(data_file).data, status=status.HTTP_200_OK)
        
    @action(detail=False, methods=['post'])
    def register_audio_files(self, request):
        """
        Register audio files for a device or deployment
        """
        user = request.user
        
        # Get deployment or device
        deployment_id = request.data.get('deployment_id')
        device_id = request.data.get('device_id')
        
        try:
            if deployment_id:
                deployment = Deployment.objects.get(pk=deployment_id)
                if not user.has_perm('data_models.change_deployment', deployment):
                    raise PermissionDenied("You don't have permission to add files to this deployment")
            elif device_id:
                device = Device.objects.get(pk=device_id)
                if not user.has_perm('data_models.change_device', device):
                    raise PermissionDenied("You don't have permission to add files to this device")
                # Get active deployment for device
                deployment = device.deployments.filter(is_active=True).first()
                if not deployment:
                    return Response({"error": "No active deployment found for this device"}, 
                                    status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({"error": "Must provide either deployment_id or device_id"}, 
                                status=status.HTTP_400_BAD_REQUEST)
        except (Deployment.DoesNotExist, Device.DoesNotExist):
            return Response({"error": "Invalid deployment or device ID"}, 
                            status=status.HTTP_404_NOT_FOUND)
                
        # Get audio files from request
        audio_files = request.data.get('audioFiles', [])
        if not audio_files:
            return Response({"error": "No audio files provided"}, 
                            status=status.HTTP_400_BAD_REQUEST)
        
        # Process each audio file
        created_files = []
        for audio_file in audio_files:
            file_data = {
                'deployment': deployment.id,
                'file_name': audio_file.get('id'),
                'config': audio_file.get('config'),
                'sample_rate': audio_file.get('samplerate'),
                'file_length': audio_file.get('fileLength'),
                'file_size': audio_file.get('fileSize'),
                'file_format': '.wav'  # Default format - adjust as needed
            }
            
            serializer = DataFileSerializer(data=file_data)
            if serializer.is_valid():
                serializer.save()
                created_files.append(serializer.data)
            else:
                # Return errors for this file
                return Response({"error": f"Invalid file data: {serializer.errors}"}, 
                                status=status.HTTP_400_BAD_REQUEST)
        
        return Response({"created_files": created_files}, status=status.HTTP_201_CREATED)

    def check_attachment(self, serializer):
        deployment_object = serializer.validated_data.get(
            'deployment', serializer.instance.deployment)
        if not self.request.user.has_perm('data_models.change_deployment', deployment_object):
            raise PermissionDenied(f"You don't have permission to add a datafile"
                                   f" to {deployment_object.deployment_device_ID}")

    def get_serializer_class(self):
        if self.action == 'create':
            return DataFileUploadSerializer
        else:
            return DataFileSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        headers = self.get_success_headers(serializer.validated_data)

        instance = serializer.validated_data

        files = instance.get('files')
        recording_dt = instance.get('recording_dt')
        extra_data = instance.get('extra_data')
        deployment_object = instance.get('deployment_object')
        device_object = instance.get('device_object')
        data_types = instance.get('data_types')
        check_filename = instance.get('check_filename')

        uploaded_files, invalid_files, existing_files, status_code = create_file_objects(
            files, check_filename, recording_dt, extra_data, deployment_object, device_object, data_types, self.request.user)

        print([x.pk for x in uploaded_files])

        if status_code == status.HTTP_201_CREATED:
            returned_data = DataFileSerializer(data=uploaded_files, many=True)
            returned_data.is_valid()
            uploaded_files = returned_data.data

        return Response({"uploaded_files": uploaded_files, "invalid_files": invalid_files, "existing_files": existing_files},
                        status=status_code, headers=headers)


class SiteViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = SiteSerializer
    queryset = Site.objects.all().distinct()
    search_fields = ['name', 'short_name']


class DataTypeViewset(viewsets.ReadOnlyModelViewSet):
    serializer_class = DataTypeSerializer
    queryset = DataType.objects.all().distinct()
    search_fields = ['name']
    filterset_class = DataTypeFilter

