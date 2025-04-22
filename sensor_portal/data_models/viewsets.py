import os

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.utils import timezone as djtimezone
from django.http import HttpResponse
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
from .models import DataFile, DataType, Deployment, Device, DeviceModel, Project, Site
from .permissions import perms
from .plotting_functions import get_all_file_metric_dicts
from .serializers import (DataFileSerializer, DataFileUploadSerializer,
                          DataTypeSerializer, DeploymentSerializer,
                          DeploymentSerializer_GeoJSON, DeviceSerializer,
                          ProjectSerializer, SiteSerializer)
from data_models.services.audio_quality import AudioQualityChecker



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
        
    @action(detail=False, methods=['post'])
    def upsert_deployment(self, request):
        """
        Update or create (upsert) a Deployment object based on the provided fields.
        
        - deployment_ID is required.
        - If deployment_ID exists, update the Deployment object with the provided (non-empty) fields.
        - Otherwise, create a new Deployment using the provided data.
        - If 'site' is not provided, a default Site object is used.
        
        Returns:
        - 200 OK with the updated deployment if found/updated.
        - 201 Created if a new deployment is created.
        - 400 Bad Request if required fields are missing.
        - 200 OK with a message if no deployment-related fields are provided.
        """

        user = request.user
        data = request.data.copy()  

        # Mapping from external field names to internal field names
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
            'Comment/remark': 'comment',
        }

        # Translate field names and filter out empty values
        translated_data = {
            field_mapping.get(key, key): value
            for key, value in data.items()
            if value not in [None, ""]
        }

        # Handle any ActiveData if present
        active_data = data.get("ActiveData")
        if isinstance(active_data, dict) and active_data.get("batteryLevel") not in [None, ""]:
            translated_data["battery_level"] = active_data["batteryLevel"]

        # If device_ID is provided, upsert the Device and link it (no error if missing)
        if device_id := data.get("device_ID"):
            # create or update minimal Device so relation never breaks
            device_defaults = {'model': DeviceModel.objects.first()}  # use default model
            device_obj, _ = Device.objects.get_or_create(
                device_ID=device_id,
                defaults=device_defaults
            )
            translated_data["device"] = device_obj

        # Handle the 'site' field
        if "site" not in translated_data:
            default_site = Site.objects.first()
            if default_site:
                translated_data["site"] = default_site
            else:
                return Response(
                    {"error": "No Site instance found in the database."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            site_val = translated_data["site"]
            if not isinstance(site_val, Site):
                try:
                    translated_data["site"] = Site.objects.get(pk=int(site_val))
                except (ValueError, Site.DoesNotExist):
                    try:
                        translated_data["site"] = Site.objects.get(short_name=site_val)
                    except Site.DoesNotExist:
                        return Response(
                            {"error": f"Provided Site '{site_val}' does not exist."},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    
        many_to_many_projects = translated_data.pop("project", None)
        if many_to_many_projects is None:
            default_project = Project.objects.first()
            if default_project:
                many_to_many_projects = [default_project.pk]

        deployment_field_keys = [
            "country", "site_name", "deployment_start", "deployment_end", "latitude",
            "longitude", "coordinate_uncertainty", "gps_device", "mic_height",
            "mic_direction", "habitat", "score", "protocol_checklist", "user_email", "comment"
        ]

        deployment_fields_provided = any(key in translated_data for key in deployment_field_keys)
        if not deployment_fields_provided:
            return Response(
                {"message": "No deployment information provided. Deployment was not updated/created."},
                status=status.HTTP_200_OK
            )

        deployment_id = translated_data.get("deployment_ID")
        if not deployment_id:
            return Response(
                {"error": "Deployment ID is required when providing deployment information."},
                status=status.HTTP_400_BAD_REQUEST
            )

        deployment, created = Deployment.objects.get_or_create(
            deployment_ID=deployment_id,
            defaults=translated_data
        )

        if many_to_many_projects:
            if not isinstance(many_to_many_projects, list):
                many_to_many_projects = [many_to_many_projects]
            deployment.project.set(many_to_many_projects)

        serializer = DeploymentSerializer(deployment, data=translated_data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        if created:
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.data, status=status.HTTP_200_OK)


    @action(detail=False, methods=['get'], url_path='by_site/(?P<site_name>[^/]+)')
    def by_site(self, request, site_name=None):
        """
        Fetch a single Deployment based on site_name (case-insensitive).

        - Expects site_name to be provided in the URL.
        - Assumes that site_name is unique across Deployments.
        - Returns 404 if no matching Deployment is found.

        Returns:
            - 200 OK with serialized deployment data if found.
            - 400 Bad Request if site_name is not provided.
            - 404 Not Found if no Deployment matches the given site_name.
        """
        if site_name is None:
            return Response({"error": "site_name is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        deployment = self.queryset.filter(site_name__iexact=site_name).first()
        
        if not deployment:
            return Response({"error": "Deployment not found"}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = self.get_serializer(deployment)
        return Response(serializer.data, status=status.HTTP_200_OK)

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

    @action(detail=True, methods=['post'])
    def check_quality_bulk(self, request, pk=None):
        """
        Trigger quality check for all audio files in a deployment
        """
        try:
            deployment = self.get_object()
            if not request.user.has_perm('data_models.change_deployment', deployment):
                raise PermissionDenied("You don't have permission to check quality for this deployment")

            # Get all audio files for this deployment
            audio_files = DataFile.objects.filter(
                deployment=deployment,
                file_format__in=['.wav', '.WAV', '.mp3', '.MP3']  # Common audio formats
            )

            if not audio_files.exists():
                return Response({
                    "error": "No audio files found in this deployment"
                }, status=status.HTTP_404_NOT_FOUND)

            # Start quality checks for each file
            results = []
            for data_file in audio_files:
                try:
                    quality_data = AudioQualityChecker.update_file_quality(data_file)
                    results.append({
                        'file_id': data_file.id,
                        'file_name': data_file.file_name,
                        'status': 'completed',
                        'quality_score': quality_data.get('quality_score')
                    })
                except Exception as e:
                    results.append({
                        'file_id': data_file.id,
                        'file_name': data_file.file_name,
                        'status': 'failed',
                        'error': str(e)
                    })

            return Response({
                'deployment_id': pk,
                'total_files': len(audio_files),
                'results': results
            }, status=status.HTTP_200_OK)

        except PermissionDenied as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_403_FORBIDDEN
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


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

    lookup_field = 'device_ID'          
    lookup_url_kwarg = 'device_ID'      

    @action(detail=False, methods=['post'])
    def upsert_device(self, request):
        data = request.data
        device_id = data.get('device_ID')
        if not device_id:
            return Response({"error": "device_ID is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        device_data = {
            'configuration': data.get('configuration'),
            'sim_card_icc': data.get('sim_card_icc'),
            'sim_card_batch': data.get('sim_card_batch'),
            'sd_card_size': float(data['sd_card_size']) if data.get('sd_card_size') not in [None, ""] else None,
        }
        
        model = DeviceModel.objects.first()
        if not model:
            return Response({"error": "No default device model found."}, status=status.HTTP_400_BAD_REQUEST)
        device_data['model'] = model

        device, created = Device.objects.get_or_create(
            device_ID=device_id,
            defaults=device_data
        )

        if not created:
            serializer = DeviceSerializer(device, data=device_data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()

        # Connect the device to an existing deployment if deployment_ID is provided
        deployment_id = data.get('deployment_ID')
        if deployment_id:
            # create or fetch the Deployment so we never 400 on missing
            dep_defaults = {}  # you can supply default fields here if you like
            deployment, _ = Deployment.objects.get_or_create(
                deployment_ID=deployment_id,
                defaults=dep_defaults
            )
            device.deployments.add(deployment)  # Associate (or re‑associate) the device

        serializer = DeviceSerializer(device)
        return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='by_site/(?P<site_name>[^/]+)')
    def by_site(self, request, site_name=None):
        if not site_name:
            return Response({"error": "site_name is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        deployment = Deployment.objects.filter(site_name__iexact=site_name).first()
        if not deployment:
            return Response({"error": "No deployment found for site"}, status=status.HTTP_404_NOT_FOUND)
        
        device = deployment.device
        if not device:
            return Response({"error": "No device linked to the deployment"}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = self.get_serializer(device)
        return Response(serializer.data, status=status.HTTP_200_OK)


    @action(detail=True, methods=['get'])
    def datafiles(self, request, device_ID=None):
   
        device = self.get_object()
        user = request.user

        datafiles_qs = DataFile.objects.filter(deployment__device=device)

        datafiles_qs = perms['data_models.view_datafile'].filter(user, datafiles_qs)

        serializer = DataFileSerializer(datafiles_qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['get'], url_path='datafiles/(?P<datafile_id>[^/.]+)')
    def datafile_detail(self, request, device_ID=None, datafile_id=None):
        device = self.get_object()
        user = request.user

        # Hent datafilen som er knyttet til en deployment som igjen tilhører device
        try:
            datafile = DataFile.objects.get(deployment__device=device, pk=datafile_id)
        except DataFile.DoesNotExist:
            return Response({"error": "DataFile not found."}, status=status.HTTP_404_NOT_FOUND)

        # Sjekk om brukeren har lov til å se datafilen (permissions)
        datafile_perm = perms['data_models.view_datafile'].filter(
            user, DataFile.objects.filter(pk=datafile_id)
        ).first()
        if not datafile_perm:
            raise PermissionDenied("You don't have permission to view this datafile")

        serializer = DataFileSerializer(datafile)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'], url_path='datafiles/(?P<datafile_id>[^/.]+)/download')
    def download_datafile(self, request, pk=None, datafile_id=None):
        """Download a specific data file from a device"""
        device = self.get_object()
        user = request.user

        try:
            datafile = DataFile.objects.get(deployment__device=device, pk=datafile_id)
        except DataFile.DoesNotExist:
            return Response({"error": "DataFile not found."}, status=status.HTTP_404_NOT_FOUND)

        if not perms['data_models.view_datafile'].filter(user, DataFile.objects.filter(pk=datafile_id)).first():
            raise PermissionDenied("You don't have permission to download this datafile")

        file_path = datafile.full_path()
        
        if not os.path.exists(file_path):
            return Response({"error": f"File not found at {file_path}"}, status=status.HTTP_404_NOT_FOUND)
        
        try:
            with open(file_path, 'rb') as f:
                file_content = f.read()
                mime_type = 'audio/mpeg' if datafile.file_format.lower().replace('.', '') == 'mp3' else f"audio/{datafile.file_format.lower().replace('.', '')}"
                response = HttpResponse(file_content, content_type=mime_type)
                response['Content-Disposition'] = f'inline; filename="{datafile.file_name}{datafile.file_format}"'
                response['Content-Length'] = len(file_content)
                return response
        except IOError as e:
            return Response({"error": f"Error reading file: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
    def update_device_info(self, request, pk=None):
        device = self.get_object()
        user = request.user

        if not user.has_perm('data_models.change_device', device):
            raise PermissionDenied("You don't have permission to update this device information")
            
        # Kun device-feltene
        device_fields = ['device_ID', 'configuration', 'sim_card_icc', 'sim_card_batch', 'sd_card_size']
        updates = {}
        for field in device_fields:
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
    def date_range(self, request):
        """
        Get the first and last recording dates for a site
        """
        site_name = request.query_params.get('site_name')
        if not site_name:
            return Response({"error": "site_name is required"}, status=status.HTTP_400_BAD_REQUEST)

        # Get the first and last recording dates for the site
        first_date = DataFile.objects.filter(
            deployment__site_name=site_name
        ).order_by('recording_dt').values_list('recording_dt', flat=True).first()

        last_date = DataFile.objects.filter(
            deployment__site_name=site_name
        ).order_by('-recording_dt').values_list('recording_dt', flat=True).first()

        return Response({
            'first_date': first_date,
            'last_date': last_date
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Download a specific data file"""
        datafile = self.get_object()
        user = request.user

        # Check permissions
        if not perms['data_models.view_datafile'].filter(user, DataFile.objects.filter(pk=pk)).first():
            raise PermissionDenied("You don't have permission to download this datafile")

        if not datafile.path:
            return Response({"error": "File path not found."}, status=status.HTTP_404_NOT_FOUND)

        # Construct full path by joining the base directory with local_path
        file_path = os.path.join(datafile.path, datafile.local_path, f"{datafile.file_name}{datafile.file_format}")
        
        if not os.path.exists(file_path):
            return Response({"error": f"File not found at {file_path}"}, status=status.HTTP_404_NOT_FOUND)
        
        try:
            with open(file_path, 'rb') as f:
                file_content = f.read()
                mime_type = 'audio/mpeg' if datafile.file_format.lower().replace('.', '') == 'mp3' else f"audio/{datafile.file_format.lower().replace('.', '')}"
                response = HttpResponse(file_content, content_type=mime_type)
                response['Content-Disposition'] = f'inline; filename="{datafile.file_name}{datafile.file_format}"'
                response['Content-Length'] = len(file_content)
                return response
        except IOError as e:
            return Response({"error": f"Error reading file: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=False, methods=['get'])
    def filter_by_date(self, request):
        # Retrieve the query parameters: start_date and end_date
        start_date = request.GET.get('start_date', None)
        end_date = request.GET.get('end_date', None)
        site_name = request.GET.get('site_name', None)
        
        # Validate the date format
        if start_date and end_date:
            try:
                start_date = djtimezone.datetime.strptime(start_date, '%m-%d-%Y')
                end_date = djtimezone.datetime.strptime(end_date, '%m-%d-%Y')
                
                # Add one day to end_date to include the entire end date
                end_date = end_date + djtimezone.timedelta(days=1)
            except ValueError:
                return Response({"error": "Invalid date format. Use MM-DD-YYYY."}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"error": "Both start_date and end_date are required."}, status=status.HTTP_400_BAD_REQUEST)
        
        # Build the initial queryset to filter by date range
        filters = {
            'recording_dt__gte': start_date,
            'recording_dt__lt': end_date
        }

        # If site_name is provided, filter by the related Deployment's site_name as well
        if site_name:
            filters['deployment__site_name'] = site_name

        # Perform the filtering in a single query using the filters dictionary
        result_queryset = DataFile.objects.filter(**filters)
        
        # Serialize and return the results
        serializer = self.get_serializer(result_queryset, many=True)
        return Response(serializer.data)
        
        
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

    @action(detail=True, methods=['post'])
    def check_quality(self, request, pk=None):
        """
        Trigger quality check for an audio file
        """
        data_file = self.get_object()
        user = request.user
        
        if not user.has_perm('data_models.change_datafile', data_file):
            raise PermissionDenied("You don't have permission to check quality for this file")
            
        try:
            quality_data = AudioQualityChecker.update_file_quality(data_file)
            return Response(quality_data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'])
    def quality_status(self, request, pk=None):
        """
        Get the current quality check status for a file
        """
        data_file = self.get_object()
        return Response({
            'status': data_file.quality_check_status,
            'score': data_file.quality_score,
            'issues': data_file.quality_issues,
            'last_check': data_file.quality_check_dt
        })


class SiteViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = SiteSerializer
    queryset = Site.objects.all().distinct()
    search_fields = ['name', 'short_name']


class DataTypeViewset(viewsets.ReadOnlyModelViewSet):
    serializer_class = DataTypeSerializer
    queryset = DataType.objects.all().distinct()
    search_fields = ['name']
    filterset_class = DataTypeFilter

