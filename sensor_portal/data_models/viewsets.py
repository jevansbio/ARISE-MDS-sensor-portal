
import logging

from camtrap_dp_export.querysets import (get_ctdp_deployment_qs,
                                         get_ctdp_media_qs)
from camtrap_dp_export.serializers import (DataFileSerializerCTDP,
                                           DeploymentSerializerCTDP)
from django.conf import settings
from django.db import connection, transaction
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_cookie
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (OpenApiParameter, extend_schema,
                                   extend_schema_view)
from observation_editor.models import Observation
from observation_editor.serializers import ObservationSerializer
from rest_framework import parsers, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_gis import filters as filters_gis
from utils.viewsets import (AddOwnerViewSetMixIn, CheckAttachmentViewSetMixIn,
                            CheckFormViewSetMixIn,
                            OptionalPaginationViewSetMixIn)

from .file_handling_functions import create_file_objects
from .filtersets import (DataFileFilter, DataTypeFilter, DeploymentFilter,
                         DeviceFilter, DeviceModelFilter, ProjectFilter)
from .job_handling_functions import start_job_from_name
from .models import (DataFile, DataType, Deployment, Device, DeviceModel,
                     Project, Site)
from .permissions import perms
from .plotting_functions import get_all_file_metric_dicts
from .serializers import (DataFileCheckSerializer, DataFileSerializer,
                          DataFileUploadSerializer, DataTypeSerializer,
                          DeploymentSerializer, DeploymentSerializer_GeoJSON,
                          DeviceModelSerializer, DeviceSerializer,
                          GenericJobSerializer, ProjectSerializer,
                          SiteSerializer)
from .serializers_fake import (DummyDataFileSerializer,
                               DummyDataFileUploadSerializer,
                               DummyDeploymentSerializer,
                               DummyDeviceSerializer, ctdp_parameter,
                               geoJSON_parameter, inline_count_serializer,
                               inline_id_serializer,
                               inline_id_serializer_optional,
                               inline_job_start_serializer,
                               inline_metric_serialiser,
                               inline_upload_response_serializer)

logger = logging.getLogger(__name__)


@extend_schema(summary="Deployments",
               description="Deployments of devices in the field, with certain settings.",
               tags=["Deployments"],
               methods=["get", "post", "put", "patch", "delete"],
               responses=DummyDeploymentSerializer,
               request=DummyDeploymentSerializer,
               )
@extend_schema_view(
    list=extend_schema(summary='List deployments.',
                       parameters=[ctdp_parameter, geoJSON_parameter],
                       ),
    retrieve=extend_schema(summary='Get a single deployment',
                           parameters=[
                                   OpenApiParameter(
                                       "id",
                                       OpenApiTypes.INT,
                                       OpenApiParameter.PATH,
                                       description="Database ID of deployment to get.")]),
    update=extend_schema(summary='Update an deployment',
                         parameters=[
                                 OpenApiParameter(
                                     "id",
                                     OpenApiTypes.INT,
                                     OpenApiParameter.PATH,
                                     description="Database ID of deplyment to update.")]),
    partial_update=extend_schema(summary='Partially update a deployment',
                                 parameters=[
                                         OpenApiParameter(
                                             "id",
                                             OpenApiTypes.INT,
                                             OpenApiParameter.PATH,
                                             description="Database ID of deployment to update.")]),
    create=extend_schema(summary='Create a deployment'),
    destroy=extend_schema(summary='Delete a deployment',
                          parameters=[
                                  OpenApiParameter(
                                      "id",
                                      OpenApiTypes.INT,
                                      OpenApiParameter.PATH,
                                      description="Database ID of deployment to delete.")]),
    project_deployments=extend_schema(summary="Deployments from project",
                                      description="Get deployments from a specific project.",
                                      filters=True,
                                      parameters=[ctdp_parameter,
                                                  geoJSON_parameter,
                                                  OpenApiParameter(
                                                      "project_id",
                                                      OpenApiTypes.INT,
                                                      OpenApiParameter.PATH,
                                                      description="Database ID of project from which to get deployments.")]),
    device_deployments=extend_schema(summary="Deployments from device",
                                     description="Get deployments of a specific device.",
                                     filters=True,
                                     parameters=[ctdp_parameter,
                                                 geoJSON_parameter,
                                                 OpenApiParameter(
                                                     "device_id",
                                                     OpenApiTypes.INT,
                                                     OpenApiParameter.PATH,
                                                     description="Database ID of device from which to get deployments.")]),
    metrics=extend_schema(summary="Metrics",
                          description="Get metrics of specific object.",
                          responses=inline_metric_serialiser
                          ),
    ids_count=extend_schema(summary="Count selected IDs",
                            request=inline_id_serializer,
                            responses=inline_count_serializer),
    queryset_count=extend_schema(summary="Count filtered deployments",
                                 filters=True,
                                 responses=inline_count_serializer),
    start_job=extend_schema(summary="Start a job from these objects",
                            filters=True,
                            request=inline_id_serializer_optional,
                            responses=inline_job_start_serializer),
    project_queryset_count=extend_schema(summary="Count filtered deployments",
                                         filters=True,
                                         responses=inline_count_serializer,
                                         parameters=[OpenApiParameter(
                                             "project_id",
                                             OpenApiTypes.INT,
                                             OpenApiParameter.PATH,
                                             description="Database ID of project from which to get deployments.")]),
    project_start_job=extend_schema(summary="Start a job from these objects",
                                    filters=True,
                                    request=inline_id_serializer_optional,
                                    responses=inline_job_start_serializer,
                                    parameters=[OpenApiParameter(
                                        "project_id",
                                        OpenApiTypes.INT,
                                        OpenApiParameter.PATH,
                                        description="Database ID of project from which to get deployments.")]),
    device_queryset_count=extend_schema(summary="Count filtered deployments",
                                        filters=True,
                                        responses=inline_count_serializer,
                                        parameters=[OpenApiParameter(
                                            "device_id",
                                            OpenApiTypes.INT,
                                            OpenApiParameter.PATH,
                                            description="Database ID of device from which to get deployments.")]),
    device_start_job=extend_schema(summary="Start a job from these objects",
                                   filters=True,
                                   request=inline_id_serializer_optional,
                                   responses=inline_job_start_serializer,
                                   parameters=[OpenApiParameter(
                                       "device_id",
                                       OpenApiTypes.INT,
                                       OpenApiParameter.PATH,
                                       description="Database ID of device from which to get deployments.")])

)
class DeploymentViewSet(CheckAttachmentViewSetMixIn, AddOwnerViewSetMixIn, CheckFormViewSetMixIn, OptionalPaginationViewSetMixIn):
    """
    A viewset for managing Deployment objects with various functionalities such as filtering, pagination,
    and custom actions. This viewset integrates multiple mixins to provide extended capabilities.
    Attributes:
        search_fields (list): Fields to enable search functionality.
        ordering_fields (list): Fields to enable ordering functionality.
        queryset (QuerySet): The base queryset for Deployment objects.
        filterset_class (class): The filter class used for filtering the queryset.
        filter_backends (list): List of filter backends used for filtering the queryset.
    Actions:
        ids_count (POST): Returns the count of deployments from a list of IDs.
        queryset_count (GET): Returns the count of deployments in the filtered queryset.
        start_job (POST): Starts a job with the given name and arguments for the filtered deployments.
        metrics (GET): Retrieves metrics for a specific deployment.
        project_deployments (GET): Retrieves deployments associated with a specific project.
        device_deployments (GET): Retrieves deployments associated with a specific device.
    Methods:
        get_queryset(): Returns the queryset for deployments, optionally filtered by 'ctdp' parameter.
        get_serializer_class(): Returns the appropriate serializer class based on request parameters.
        check_attachment(serializer): Validates permissions for attaching deployments to projects and devices.
    Notes:
        - The viewset supports GeoJSON serialization and CTDP-specific filtering.
        - Pagination is applied to the queryset when applicable.
        - Custom permissions are enforced for certain actions.
    """

    search_fields = ['deployment_device_ID',
                     'device__name', 'device__device_ID', 'extra_data']
    ordering_fields = ordering = [
        'deployment_device_ID', 'created_on', 'device_type']
    queryset = Deployment.objects.all().distinct()
    filterset_class = DeploymentFilter
    filter_backends = viewsets.ModelViewSet.filter_backends + \
        [filters_gis.InBBoxFilter]

    def get_queryset(self):
        qs = Deployment.objects.all().distinct()
        if 'ctdp' in self.request.GET.keys():
            qs = get_ctdp_deployment_qs(qs)
        return qs

    def get_serializer_class(self):
        if 'geojson' in self.request.GET.keys():
            return DeploymentSerializer_GeoJSON
        elif 'ctdp' in self.request.GET.keys():
            return DeploymentSerializerCTDP
        else:
            return DeploymentSerializer

    def check_attachment(self, serializer):
        project_objects = serializer.validated_data.get('project')
        if project_objects is not None:
            for project_object in project_objects:
                if (not self.request.user.has_perm('data_models.change_project', project_object)) and \
                        (project_object.name != settings.GLOBAL_PROJECT_ID):
                    raise PermissionDenied(
                        f"You don't have permission to add a deployment to {project_object.project_ID}")
        device_object = serializer.validated_data.get('device')
        if device_object is not None:
            if not self.request.user.has_perm('data_models.change_device', device_object):
                raise PermissionDenied(
                    f"You don't have permission to deploy {device_object.device_ID}")

    @action(detail=False, methods=['post'])
    def ids_count(self, request, *args, **kwargs):
        queryset = Deployment.objects.filter(pk__in=request.data.get("ids"))
        return Response({"object_n": queryset.count()}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def queryset_count(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        return Response({"object_n": queryset.count()}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path=r'start_job/(?P<job_name>\w+)')
    def start_job(self, request, job_name, *args, **kwargs):

        queryset = self.filter_queryset(self.get_queryset())

        user_pk = request.user.pk

        if not (obj_pks := request.data.get("ids")):
            obj_pks = list(queryset.values_list('pk', flat=True))
        else:
            request.data.pop("ids")

        job_args = request.data
        success, detail, job_status = start_job_from_name(
            job_name, "deployment", obj_pks, job_args, user_pk)

        return Response({"detail": detail}, status=job_status)

    @action(detail=True, methods=['get'])
    def metrics(self, request, pk=None):
        deployment = self.get_object()
        user = request.user
        data_files = perms['data_models.view_datafile'].filter(
            user, deployment.files.all())
        if not data_files.exists():
            return Response({}, status=status.HTTP_200_OK)
        file_metric_dicts = get_all_file_metric_dicts(data_files)
        return Response(file_metric_dicts, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path=r'project/(?P<project_id>\w+)', url_name="project_deployments")
    def project_deployments(self, request, project_id=None):
        # Filter deployments based on the project primary key (project_id)
        deployment_qs = Deployment.objects.filter(
            project__pk=project_id)
        deployment_qs = self.filter_queryset(deployment_qs)

        if 'ctdp' in request.GET.keys():
            deployment_qs = get_ctdp_deployment_qs(deployment_qs)

        # Paginate the queryset
        page = self.paginate_queryset(deployment_qs)
        if page is not None:
            deployment_serializer = self.get_serializer(
                page, many=True, context={'request': request})
            return self.get_paginated_response(deployment_serializer.data)

        # If no pagination, serialize all data
        deployment_serializer = self.get_serializer(
            deployment_qs, many=True, context={'request': request})
        return Response(deployment_serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path=r'project/(?P<project_id>\w+)/queryset_count')
    def project_queryset_count(self, request, project_id, *args, **kwargs):

        queryset = Deployment.objects.filter(
            project__pk=project_id)

        queryset = self.filter_queryset(queryset)
        return Response({"object_n": queryset.count()}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path=r'project/(?P<project_id>\w+)/start_job/(?P<job_name>\w+)')
    def project_start_job(self, request, project_id, job_name, *args, **kwargs):

        queryset = Deployment.objects.filter(
            project__pk=project_id)

        queryset = self.filter_queryset(queryset)

        user_pk = request.user.pk

        if not (obj_pks := request.data.get("ids")):
            obj_pks = list(queryset.values_list('pk', flat=True))
        else:
            request.data.pop("ids")

        job_args = request.data
        success, detail, job_status = start_job_from_name(
            job_name, "deployment", obj_pks, job_args, user_pk)

        return Response({"detail": detail}, status=job_status)

    @action(detail=False, methods=['get'], url_path=r'device/(?P<device_id>\w+)', url_name="device_deployments")
    def device_deployments(self, request, device_id=None):
        # Filter deployments based on the device primary key (device_id)
        deployment_qs = Deployment.objects.filter(
            device__pk=device_id)

        deployment_qs = self.filter_queryset(deployment_qs)

        if 'ctdp' in request.GET.keys():
            deployment_qs = get_ctdp_deployment_qs(deployment_qs)

        # Paginate the queryset
        page = self.paginate_queryset(deployment_qs)
        if page is not None:

            deployment_serializer = self.get_serializer(
                page, many=True, context={'request': request})
            return self.get_paginated_response(deployment_serializer.data)

        # If no pagination, serialize all data
        deployment_serializer = self.get_serializer(
            deployment_qs, many=True, context={'request': request})
        return Response(deployment_serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path=r'device/(?P<device_id>\w+)/queryset_count')
    def device_queryset_count(self, request, device_id, *args, **kwargs):

        queryset = Deployment.objects.filter(
            device__pk=device_id)

        queryset = self.filter_queryset(queryset)
        return Response({"object_n": queryset.count()}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path=r'device/(?P<device_id>\w+)/start_job/(?P<job_name>\w+)')
    def device_start_job(self, request, device_id, job_name, *args, **kwargs):

        queryset = Deployment.objects.filter(
            device__pk=device_id)

        queryset = self.filter_queryset(queryset)

        user_pk = request.user.pk

        if not (obj_pks := request.data.get("ids")):
            obj_pks = list(queryset.values_list('pk', flat=True))
        else:
            request.data.pop("ids")

        job_args = request.data
        success, detail, job_status = start_job_from_name(
            job_name, "deployment", obj_pks, job_args, user_pk)

        return Response({"detail": detail}, status=job_status)


@extend_schema(summary="Projects",
               description="Projects to organise collections of deployments and scientific work.",
               tags=["Projects"],
               methods=["get", "post", "put", "patch", "delete"],
               )
@extend_schema_view(
    list=extend_schema(summary='List projects.'
                       ),
    retrieve=extend_schema(summary='Get a single project',
                           parameters=[
                                   OpenApiParameter(
                                       "id",
                                       OpenApiTypes.INT,
                                       OpenApiParameter.PATH,
                                       description="Database ID of project to get.")]),
    update=extend_schema(summary='Update an deployment',
                         parameters=[
                                 OpenApiParameter(
                                     "id",
                                     OpenApiTypes.INT,
                                     OpenApiParameter.PATH,
                                     description="Database ID of project to update.")]),
    partial_update=extend_schema(summary='Partially update a project',
                                 parameters=[
                                         OpenApiParameter(
                                             "id",
                                             OpenApiTypes.INT,
                                             OpenApiParameter.PATH,
                                             description="Database ID of project to update.")]),
    create=extend_schema(summary='Create a project'),
    destroy=extend_schema(summary='Delete a project',
                          parameters=[
                                  OpenApiParameter(
                                      "id",
                                      OpenApiTypes.INT,
                                      OpenApiParameter.PATH,
                                      description="Database ID of project to delete.")]),
    metrics=extend_schema(summary="Metrics",
                          description="Get metrics of specific object.",
                          responses=inline_metric_serialiser
                          ),
    ids_count=extend_schema(summary="Count selected IDs",
                            request=inline_id_serializer,
                            responses=inline_count_serializer),
    queryset_count=extend_schema(summary="Count filtered deployments",
                                 filters=True,
                                 responses=inline_count_serializer),
    species_list=extend_schema(
        summary="Get list of species", responses=serializers.ListSerializer(
            child=serializers.CharField(default="Bufo bufo"), many=False),
        filters=False,
    ),
    start_job=extend_schema(summary="Start a job from these objects",
                            filters=True,
                            request=inline_id_serializer_optional,
                            responses=inline_job_start_serializer),
)
class ProjectViewSet(AddOwnerViewSetMixIn, OptionalPaginationViewSetMixIn):
    """
    A viewset for managing Project objects with additional functionality for filtering, searching,
    and performing custom actions.
    Attributes:
        serializer_class (ProjectSerializer): Serializer class for Project objects.
        queryset (QuerySet): Base queryset for retrieving Project objects, excluding the global project ID.
        filterset_class (ProjectFilter): Filter class for filtering Project objects.
        search_fields (list): Fields to enable search functionality.
    Actions:
        ids_count (POST):
            Count the number of files associated with a list of project IDs provided in the request body.
            Returns the file count.
        queryset_count (GET):
            Count the number of files in the filtered queryset.
            Returns the file count.
        start_job (POST):
            Start a job with the specified job name and project IDs. If no IDs are provided,
            the job will be started for all objects in the filtered queryset.
            Returns the job status and details.
        species_list (GET):
            Retrieve a distinct list of species names associated with the project's data files
            that the user has permission to view.
            Returns the species list.
        metrics (GET):
            Retrieve metrics for the project's data files that the user has permission to view.
            Returns a list of file metric dictionaries.
    """

    serializer_class = ProjectSerializer
    queryset = Project.objects.all().distinct().exclude(
        name=settings.GLOBAL_PROJECT_ID)
    filterset_class = ProjectFilter
    search_fields = ['project_ID', 'name', 'organisation']

    @action(detail=False, methods=['post'])
    def ids_count(self, request, *args, **kwargs):
        queryset = Project.objects.filter(pk__in=request.data.get("ids"))
        return Response(queryset.file_count(), status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def queryset_count(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        return Response(queryset.file_count(), status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path=r'start_job/(?P<job_name>\w+)')
    def start_job(self, request, job_name, *args, **kwargs):

        queryset = self.filter_queryset(self.get_queryset())

        user_pk = request.user.pk

        if not (obj_pks := request.data.get("ids")):
            obj_pks = list(queryset.values_list('pk', flat=True))
        else:
            request.data.pop("ids")

        job_args = request.data
        success, detail, job_status = start_job_from_name(
            job_name, "project", obj_pks, job_args, user_pk)

        return Response({"detail": detail}, status=job_status)

    @action(detail=True, methods=['get'], pagination_class=None)
    def species_list(self, request, pk=None):
        project = self.get_object()
        user = request.user
        data_files = perms['data_models.view_datafile'].filter(
            user, DataFile.objects.filter(deployment__project=project))
        if not data_files.exists():
            return Response([], status=status.HTTP_200_OK)
        obs_obj = Observation.objects.filter(data_files__in=data_files)
        species_list = list(obs_obj.values_list(
            "taxon__species_name", flat=True).distinct())
        return Response(species_list, status=status.HTTP_200_OK)

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


@extend_schema(summary="Devices",
               description="Database representation of sensors.",
               tags=["Devices"],
               methods=["get", "post", "put", "patch", "delete"],
               responses=DummyDeviceSerializer,
               request=DummyDeviceSerializer
               )
@extend_schema_view(
    list=extend_schema(summary='List devices.',
                       ),
    retrieve=extend_schema(summary='Get a single device',
                           parameters=[
                                   OpenApiParameter(
                                       "id",
                                       OpenApiTypes.INT,
                                       OpenApiParameter.PATH,
                                       description="Database ID of device to get.")]),
    update=extend_schema(summary='Update a device',
                         parameters=[
                                 OpenApiParameter(
                                     "id",
                                     OpenApiTypes.INT,
                                     OpenApiParameter.PATH,
                                     description="Database ID of device to update.")]),
    partial_update=extend_schema(summary='Partially update a device',
                                 parameters=[
                                         OpenApiParameter(
                                             "id",
                                             OpenApiTypes.INT,
                                             OpenApiParameter.PATH,
                                             description="Database ID of device to update.")]),
    create=extend_schema(summary='Create a device'),
    destroy=extend_schema(summary='Delete a device',
                          parameters=[
                                  OpenApiParameter(
                                      "id",
                                      OpenApiTypes.INT,
                                      OpenApiParameter.PATH,
                                      description="Database ID of device to delete.")]),
    metrics=extend_schema(summary="Metrics",
                          description="Get metrics of specific object.",
                          responses=inline_metric_serialiser
                          ),
    ids_count=extend_schema(summary="Count selected IDs",
                            request=inline_id_serializer,
                            responses=inline_count_serializer),
    queryset_count=extend_schema(summary="Count filtered devices",
                                 filters=True,
                                 responses=inline_count_serializer),
    start_job=extend_schema(summary="Start a job from these objects",
                            filters=True,
                            request=inline_id_serializer_optional,
                            responses=inline_job_start_serializer)

)
class DeviceViewSet(AddOwnerViewSetMixIn, OptionalPaginationViewSetMixIn):
    """
    A viewset for managing Device objects with additional functionality for filtering, searching,
    and performing custom actions.
    Attributes:
        serializer_class (DeviceSerializer): The serializer class used for Device objects.
        queryset (QuerySet): The base queryset for Device objects, ensuring distinct results.
        filterset_class (DeviceFilter): The filter class used for filtering Device objects.
        search_fields (list): Fields that can be searched, including 'device_ID', 'name', and 'model__name'.
    Actions:
        ids_count (POST):
            Count the number of files associated with the provided Device IDs.
            Args:
                request (Request): The HTTP request containing a list of Device IDs in the body.
            Returns:
                Response: The count of files associated with the provided Device IDs.
        queryset_count (GET):
            Count the number of files in the filtered queryset.
            Args:
                request (Request): The HTTP request.
            Returns:
                Response: The count of files in the filtered queryset.
        start_job (POST):
            Start a job for the provided Device objects.
            Args:
                request (Request): The HTTP request containing job arguments and optional Device IDs.
                job_name (str): The name of the job to start.
            Returns:
                Response: A response containing the job status and details.
        metrics (GET):
            Retrieve metrics for a specific Device object.
            Args:
                request (Request): The HTTP request.
                pk (int): The primary key of the Device object.
            Returns:
                Response: A dictionary of file metrics for the Device object, or an empty dictionary if no data files are accessible.
    """

    serializer_class = DeviceSerializer
    queryset = Device.objects.all().distinct()
    filterset_class = DeviceFilter
    search_fields = ['device_ID', 'name', 'model__name']

    @action(detail=False, methods=['post'])
    def ids_count(self, request, *args, **kwargs):
        queryset = Device.objects.filter(pk__in=request.data.get("ids"))
        return Response(queryset.file_count(), status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def queryset_count(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        return Response(queryset.file_count(), status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path=r'start_job/(?P<job_name>\w+)')
    def start_job(self, request, job_name, *args, **kwargs):

        queryset = self.filter_queryset(self.get_queryset())

        user_pk = request.user.pk

        if not (obj_pks := request.data.get("ids")):
            obj_pks = list(queryset.values_list('pk', flat=True))
        else:
            request.data.pop("ids")

        job_args = request.data
        success, detail, job_status = start_job_from_name(
            job_name, "device", obj_pks, job_args, user_pk)

        return Response({"detail": detail}, status=job_status)

    @action(detail=True, methods=['get'])
    def metrics(self, request, pk=None):
        device = self.get_object()
        user = request.user
        data_files = perms['data_models.view_datafile'].filter(
            user, DataFile.objects.filter(deployment__device=device))
        if not data_files.exists():
            return Response({}, status=status.HTTP_200_OK)
        file_metric_dicts = get_all_file_metric_dicts(data_files)
        return Response(file_metric_dicts, status=status.HTTP_200_OK)


@extend_schema(summary="Data files",
               description="Files recorded by sensors.",
               tags=["DataFiles"],
               methods=["get", "post", "patch", "delete"],
               responses=DummyDataFileSerializer
               )
@extend_schema_view(
    list=extend_schema(summary='List datafiles.',
                       parameters=[ctdp_parameter],
                       ),
    retrieve=extend_schema(summary='Get a single datafile',
                           parameters=[
                                   OpenApiParameter(
                                       "id",
                                       OpenApiTypes.INT,
                                       OpenApiParameter.PATH,
                                       description="Database ID of datafile to get.")]),
    partial_update=extend_schema(summary='Partially update a datafile',
                                 parameters=[
                                         OpenApiParameter(
                                             "id",
                                             OpenApiTypes.INT,
                                             OpenApiParameter.PATH,
                                             description="Database ID of datafile to update.")]),
    create=extend_schema(summary='Upload datafiles',
                         request=DummyDataFileUploadSerializer,
                         responses=inline_upload_response_serializer,
                         description="Upload multiple datafiles or part of a lrger datafile"),
    destroy=extend_schema(summary='Delete a datafile',
                          parameters=[
                                  OpenApiParameter(
                                      "id",
                                      OpenApiTypes.INT,
                                      OpenApiParameter.PATH,
                                      description="Database ID of datafile to delete.")]),
    metrics=extend_schema(summary="Metrics",
                          description="Get metrics of specific object.",
                          responses=inline_metric_serialiser
                          ),
    ids_count=extend_schema(summary="Count selected IDs",
                            request=inline_id_serializer,
                            responses=inline_count_serializer),
    queryset_count=extend_schema(summary="Count filtered devices",
                                 filters=True,
                                 responses=inline_count_serializer),
    start_job=extend_schema(summary="Start a job from these objects",
                            filters=True,
                            request=inline_id_serializer_optional,
                            responses=inline_job_start_serializer),
    check_existing=extend_schema(summary="Check a list of filenames for files already in the database",
                                 filters=True,
                                 request=DataFileCheckSerializer,
                                 responses=serializers.ListSerializer(
                                     child=serializers.CharField(default="myfile.jpg"), many=False),
                                 ),
    project_datafiles=extend_schema(summary="Datafiles from project",
                                    description="Get datafiles from a specific project.",
                                    filters=True,
                                    parameters=[
                                                ctdp_parameter,
                                                OpenApiParameter(
                                                    "project_id",
                                                    OpenApiTypes.INT,
                                                    OpenApiParameter.PATH,
                                                    description="Database ID of project from which to get datafiles.")]),
    deployment_datafiles=extend_schema(summary="Datafiles from deployment",
                                       description="Get datafiles from a specific deployment.",
                                       filters=True,
                                       parameters=[
                                           ctdp_parameter,
                                           OpenApiParameter(
                                               "project_id",
                                               OpenApiTypes.INT,
                                               OpenApiParameter.PATH,
                                               description="Database ID of deployment from which to get datafiles.")]),
    device_datafiles=extend_schema(summary="Datafiles from device",
                                   description="Get datafiles from a specific device.",
                                   filters=True,
                                   parameters=[
                                       ctdp_parameter,
                                       OpenApiParameter(
                                           "project_id",
                                           OpenApiTypes.INT,
                                           OpenApiParameter.PATH,
                                           description="Database ID of device from which to get datafiles.")]),
    user_favourite_datafiles=extend_schema(summary="User favourite datafiles",
                                           description="Get datafiles favourited by the current user.",
                                           filters=True,
                                           parameters=[
                                               ctdp_parameter,
                                           ]),
    favourited_datafiles=extend_schema(summary="Favourited datafiles",
                                       description="Get datafiles favourited by users.",
                                       filters=True,
                                       parameters=[
                                           ctdp_parameter,
                                       ]),
    favourite_file=extend_schema(exclude=True),
    observations=extend_schema(exclude=True),
    deployment_datafiles_queryset_count=extend_schema(
        summary="Count DataFiles for Deployment",
        description="Return the count of DataFile objects for a given deployment. Returns an integer.",
        parameters=[
            OpenApiParameter("deployment_pk", OpenApiTypes.INT,
                             OpenApiParameter.PATH, description="Deployment ID"),
        ],
        responses=OpenApiTypes.INT
    ),
    deployment_datafiles_start_job=extend_schema(
        summary="Start a Job on Deployment DataFiles",
        description="Start a job on DataFiles for a given deployment.",
        parameters=[
            OpenApiParameter("deployment_pk", OpenApiTypes.INT,
                             OpenApiParameter.PATH, description="Deployment ID"),
            OpenApiParameter("job_name", OpenApiTypes.STR,
                             OpenApiParameter.PATH, description="Job name"),
        ],
        # or whatever serializer describes your POST body
        request=inline_id_serializer_optional,
        responses=inline_job_start_serializer,
    ),
    project_datafiles_queryset_count=extend_schema(
        summary="Count DataFiles for Project",
        description="Return the count of DataFile objects for a given project. Returns an integer.",
        parameters=[
            OpenApiParameter("project_id", OpenApiTypes.INT,
                             OpenApiParameter.PATH, description="Project ID"),
        ],
        responses=OpenApiTypes.INT
    ),
    project_datafiles_start_job=extend_schema(
        summary="Start a Job on Project DataFiles",
        description="Start a job on DataFiles for a given project.",
        parameters=[
            OpenApiParameter("project_id", OpenApiTypes.INT,
                             OpenApiParameter.PATH, description="Project ID"),
            OpenApiParameter("job_name", OpenApiTypes.STR,
                             OpenApiParameter.PATH, description="Job name"),
        ],
        request=inline_id_serializer_optional,
        responses=inline_job_start_serializer,
    ),
    device_datafiles_queryset_count=extend_schema(
        summary="Count DataFiles for Device",
        description="Return the count of DataFile objects for a given device. Returns an integer.",
        parameters=[
            OpenApiParameter("device_id", OpenApiTypes.INT,
                             OpenApiParameter.PATH, description="Device ID"),
        ],
        responses=OpenApiTypes.INT
    ),
    device_datafiles_start_job=extend_schema(
        summary="Start a Job on Device DataFiles",
        description="Start a job on DataFiles for a given device.",
        parameters=[
            OpenApiParameter("device_id", OpenApiTypes.INT,
                             OpenApiParameter.PATH, description="Device ID"),
            OpenApiParameter("job_name", OpenApiTypes.STR,
                             OpenApiParameter.PATH, description="Job name"),
        ],
        request=inline_id_serializer_optional,
        responses=inline_job_start_serializer,
    ),
    user_favourite_datafiles_queryset_count=extend_schema(
        summary="Count User Favourite DataFiles",
        description="Return the count of DataFile objects favourited by the current user. Returns an integer.",
        responses=OpenApiTypes.INT
    ),
    user_favourite_datafiles_start_job=extend_schema(
        summary="Start a Job on User Favourite DataFiles",
        description="Start a job on DataFiles favourited by the current user.",
        parameters=[
            OpenApiParameter("job_name", OpenApiTypes.STR,
                             OpenApiParameter.PATH, description="Job name"),
        ],
        request=inline_id_serializer_optional,
        responses=inline_job_start_serializer,
    ),
    favourited_datafiles_queryset_count=extend_schema(
        summary="Count Favourited DataFiles",
        description="Return the count of DataFile objects favourited by any user. Returns an integer.",
        responses=OpenApiTypes.INT
    ),
    favourited_datafiles_start_job=extend_schema(
        summary="Start a Job on Favourited DataFiles",
        description="Start a job on DataFiles favourited by any user.",
        parameters=[
            OpenApiParameter("job_name", OpenApiTypes.STR,
                             OpenApiParameter.PATH, description="Job name"),
        ],
        request=inline_id_serializer_optional,
        responses=inline_job_start_serializer,
    ),
)
class DataFileViewSet(CheckAttachmentViewSetMixIn, OptionalPaginationViewSetMixIn):
    """
    DataFileViewSet is a Django REST Framework viewset that provides various actions for managing and interacting
    with DataFile objects. It includes filtering, searching, pagination, and custom actions for specific use cases.
    Attributes:
        filterset_class (DataFileFilter): Specifies the filter class for filtering querysets.
        search_fields (list): Defines the fields that can be searched.
    Methods:
        get_queryset():
            Returns the queryset of DataFile objects, optionally filtered by 'ctdp' parameter.
        check_existing(request, *args, **kwargs):
            Custom action to check for existing data files based on 'original_names' or 'file_names' provided in the request.
        ids_count(request, *args, **kwargs):
            Custom action to count the number of DataFile objects based on provided IDs.
        queryset_count(request, *args, **kwargs):
            Custom action to count the number of DataFile objects in the filtered queryset.
        start_job(request, job_name, *args, **kwargs):
            Custom action to start a job with the specified name and associated DataFile objects.
        observations(request, pk=None):
            Custom action to retrieve observations associated with a specific DataFile object.
        favourite_file(request, pk=None):
            Custom action to toggle the favorite status of a DataFile object for the current user.
        check_attachment(serializer):
            Validates if the user has permission to add a DataFile to a deployment.
        get_serializer_class():
            Returns the appropriate serializer class based on the action and request parameters.
        create(request, *args, **kwargs):
            Handles the creation of new DataFile objects, including file uploads and validation.
        deployment_datafiles(request, deployment_pk=None):
            Custom action to retrieve DataFile objects associated with a specific deployment.
        project_datafiles(request, project_id=None):
            Custom action to retrieve DataFile objects associated with a specific project.
        device_datafiles(request, device_id=None):
            Custom action to retrieve DataFile objects associated with a specific device.
        user_favourite_datafiles(request):
            Custom action to retrieve DataFile objects favorited by the current user.
        favourited_datafiles(request):
            Custom action to retrieve DataFile objects that have been favorited by any user.
    Notes:
        - This viewset includes custom actions for specific use cases, such as filtering by deployment, project, or device.
        - Pagination is applied to querysets where applicable.
        - Permissions are checked for certain actions, such as adding a DataFile to a deployment.
    """
    http_method_names = ['get', 'patch', 'delete', 'post', 'head']
    filterset_class = DataFileFilter

    search_fields = ['=tag',
                     'file_name',
                     'observations__taxon__species_name',
                     'observations__taxon__species_common_name']

    def get_serializer_class(self):
        if self.action == 'create':
            return DataFileUploadSerializer
        else:
            if 'ctdp' in self.request.GET.keys():
                return DataFileSerializerCTDP
            else:
                return DataFileSerializer

    def get_queryset(self):
        qs = DataFile.objects.prefetch_related("deployment",
                                               "observations__taxon").all().distinct()

        if 'ctdp' in self.request.GET.keys():
            qs = get_ctdp_media_qs(qs)
        return qs

    @action(detail=False, methods=['post'], pagination_class=None)
    def check_existing(self, request, *args, **kwargs):
        queryset = perms['data_models.view_datafile'].filter(
            request.user, self.get_queryset())

        serializer = DataFileCheckSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        filter_params = request.data or request.GET
        if filter_params:
            queryfilter = self.filterset_class(
                filter_params, queryset=queryset)
            queryset = queryfilter.qs

        if (original_names := serializer.validated_data.get('original_names')):
            existing_names = queryset.filter(
                original_name__in=original_names).values_list('original_name', flat=True)
            existing_names = list(existing_names)
            missing_names = [
                x for x in original_names if x not in existing_names]

        elif (file_names := serializer.validated_data.get('file_names')):
            existing_names = queryset.filter(
                file_name__in=file_names).values_list('file_name', flat=True)
            missing_names = [
                x for x in original_names if x not in existing_names]
        else:
            return Response({"detail": "Either 'original_names' or 'file_names' must be provided."},
                            status=status.HTTP_400_BAD_REQUEST)

        return Response(missing_names, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def ids_count(self, request, *args, **kwargs):
        queryset = DataFile.objects.filter(pk__in=request.data.get("ids"))
        return Response(queryset.file_count(), status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def queryset_count(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        return Response(queryset.file_count(), status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path=r'start_job/(?P<job_name>\w+)')
    def start_job(self, request, job_name, *args, **kwargs):

        queryset = self.filter_queryset(self.get_queryset())

        user_pk = request.user.pk

        if not (obj_pks := request.data.get("ids")):
            obj_pks = list(queryset.values_list('pk', flat=True))
        else:
            request.data.pop("ids")

        job_args = request.data
        success, detail, job_status = start_job_from_name(
            job_name, "datafile", obj_pks, job_args, user_pk)

        return Response({"detail": detail}, status=job_status)

    @action(detail=True, methods=['get'])
    def observations(self, request, pk=None):
        data_file = DataFile.objects.get(pk=pk)

        # Filter observations based on URL query parameters
        observation_qs = Observation.objects.filter(
            data_files=data_file)

        # Paginate the queryset
        logger.info(self.request)
        page = self.paginate_queryset(observation_qs)
        if page is not None:
            observation_serializer = ObservationSerializer(
                page, many=True, context={'request': request})
            return self.get_paginated_response(observation_serializer.data)

        # If no pagination, serialize all data
        observation_serializer = ObservationSerializer(
            observation_qs, many=True, context={'request': request})
        return Response(observation_serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def favourite_file(self, request, pk=None):
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

    def check_attachment(self, serializer):
        deployment_object = serializer.validated_data.get(
            'deployment', serializer.instance.deployment)
        if not self.request.user.has_perm('data_models.change_deployment', deployment_object):
            raise PermissionDenied(f"You don't have permission to add a datafile"
                                   f" to {deployment_object.deployment_device_ID}")

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

        multipart = 'HTTP_CONTENT_RANGE' in request.META

        with transaction.atomic(), connection.cursor() as cursor:
            # Remove db limits during this function.
            cursor.execute('SET LOCAL statement_timeout TO 0;')
            uploaded_files, invalid_files, existing_files, status_code = create_file_objects(
                files, check_filename, recording_dt, extra_data, deployment_object, device_object,
                data_types, self.request.user, multipart)

        logger.info(
            f"Uploaded files: {uploaded_files}, Invalid files: {invalid_files}, Existing files: {existing_files}, Status code: {status_code}")

        if len(uploaded_files) > 0:
            returned_data = DataFileSerializer(data=uploaded_files, many=True)
            returned_data.is_valid()
            uploaded_files = returned_data.data

        return Response({"uploaded_files": uploaded_files, "invalid_files": invalid_files, "existing_files": existing_files},
                        status=status_code, headers=headers)

    # --- Deployment DataFiles ---

    @action(detail=False, methods=['get'], url_path=r'deployment/(?P<deployment_pk>\w+)', url_name="deployment_datafiles")
    def deployment_datafiles(self, request, deployment_pk=None):
        # Filter data files based on the deployment primary key (deployment_pk)
        data_file_qs = DataFile.objects.filter(deployment__pk=deployment_pk)

        # Apply filters from URL query parameters
        data_file_qs = self.filter_queryset(data_file_qs)

        if 'ctdp' in request.GET.keys():
            data_file_qs = get_ctdp_media_qs(data_file_qs)

        # Paginate the queryset
        page = self.paginate_queryset(data_file_qs)
        if page is not None:
            serializer = self.get_serializer(
                page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)

        # If no pagination, serialize all data
        serializer = self.get_serializer(
            data_file_qs, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path=r'deployment/(?P<deployment_pk>\w+)/queryset_count')
    def deployment_datafiles_queryset_count(self, request, deployment_pk=None):
        queryset = self.filter_queryset(
            DataFile.objects.filter(deployment__pk=deployment_pk))
        return Response(queryset.file_count(), status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path=r'deployment/(?P<deployment_pk>\w+)/start_job/(?P<job_name>\w+)')
    def deployment_datafiles_start_job(self, request, deployment_pk=None, job_name=None):
        queryset = self.filter_queryset(
            DataFile.objects.filter(deployment__pk=deployment_pk))
        user_pk = request.user.pk
        obj_pks = request.data.get("ids") or list(
            queryset.values_list('pk', flat=True))
        if "ids" in request.data:
            request.data.pop("ids")
        job_args = request.data
        success, detail, job_status = start_job_from_name(
            job_name, "datafile", obj_pks, job_args, user_pk)
        return Response({"detail": detail}, status=job_status)

    # --- Project DataFiles ---

    @action(detail=False, methods=['get'], url_path=r'project/(?P<project_id>\w+)', url_name="project_datafiles")
    def project_datafiles(self, request, project_id=None):
        # Filter data files based on the project primary key (project_id) through deployments
        data_file_qs = DataFile.objects.filter(
            deployment__project__pk=project_id)

        # Apply filters from URL query parameters
        data_file_qs = self.filter_queryset(data_file_qs)

        if 'ctdp' in request.GET.keys():
            data_file_qs = get_ctdp_media_qs(data_file_qs)

        # Paginate the queryset
        page = self.paginate_queryset(data_file_qs)
        if page is not None:
            serializer = self.get_serializer(
                page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)

        # If no pagination, serialize all data
        serializer = self.get_serializer(
            data_file_qs, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path=r'project/(?P<project_id>\w+)/queryset_count')
    def project_datafiles_queryset_count(self, request, project_id=None):
        queryset = self.filter_queryset(
            DataFile.objects.filter(project__pk=project_id))
        return Response(queryset.file_count(), status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path=r'project/(?P<project_id>\w+)/start_job/(?P<job_name>\w+)')
    def project_datafiles_start_job(self, request, project_id=None, job_name=None):
        queryset = self.filter_queryset(
            DataFile.objects.filter(project__pk=project_id))
        user_pk = request.user.pk
        obj_pks = request.data.get("ids") or list(
            queryset.values_list('pk', flat=True))
        if "ids" in request.data:
            request.data.pop("ids")
        job_args = request.data
        success, detail, job_status = start_job_from_name(
            job_name, "datafile", obj_pks, job_args, user_pk)
        return Response({"detail": detail}, status=job_status)

    # --- Device DataFiles ---

    @action(detail=False, methods=['get'], url_path=r'device/(?P<device_id>\w+)', url_name="device_datafiles")
    def device_datafiles(self, request, device_id=None):
        # Filter data files based on the device primary key (device_id) through deployments
        data_file_qs = DataFile.objects.filter(
            deployment__device__pk=device_id)

        # Apply filters from URL query parameters
        data_file_qs = self.filter_queryset(data_file_qs)

        if 'ctdp' in request.GET.keys():
            data_file_qs = get_ctdp_media_qs(data_file_qs)

        # Paginate the queryset
        page = self.paginate_queryset(data_file_qs)
        if page is not None:
            serializer = self.get_serializer(
                page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)

        # If no pagination, serialize all data

        serializer = self.get_serializer(
            data_file_qs, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path=r'device/(?P<device_id>\w+)/queryset_count')
    def device_datafiles_queryset_count(self, request, device_id=None):
        queryset = self.filter_queryset(
            DataFile.objects.filter(device__pk=device_id))
        return Response(queryset.file_count(), status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path=r'device/(?P<device_id>\w+)/start_job/(?P<job_name>\w+)')
    def device_datafiles_start_job(self, request, device_id=None, job_name=None):
        queryset = self.filter_queryset(
            DataFile.objects.filter(device__pk=device_id))
        user_pk = request.user.pk
        obj_pks = request.data.get("ids") or list(
            queryset.values_list('pk', flat=True))
        if "ids" in request.data:
            request.data.pop("ids")
        job_args = request.data
        success, detail, job_status = start_job_from_name(
            job_name, "datafile", obj_pks, job_args, user_pk)
        return Response({"detail": detail}, status=job_status)

    # --- User Favourite DataFiles ---

    @action(detail=False, methods=['get'], url_path=r'user', url_name="user_favourite_datafiles")
    def user_favourite_datafiles(self, request):
        # Get the data files favorited by the current user
        user = request.user
        if not user.is_authenticated:
            return Response({"detail": "Authentication credentials were not provided."}, status=status.HTTP_401_UNAUTHORIZED)

        data_file_qs = DataFile.objects.filter(favourite_of=user)

        # Apply filters from URL query parameters
        data_file_qs = self.filter_queryset(data_file_qs)

        if 'ctdp' in request.GET.keys():
            data_file_qs = get_ctdp_media_qs(data_file_qs)

        # Paginate the queryset
        page = self.paginate_queryset(data_file_qs)
        if page is not None:
            serializer = self.get_serializer(
                page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)

        # If no pagination, serialize all data
        serializer = self.get_serializer(
            data_file_qs, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='user_favourite/queryset_count')
    def user_favourite_datafiles_queryset_count(self, request):
        queryset = self.filter_queryset(
            DataFile.objects.filter(favourites=request.user))
        return Response(queryset.file_count(), status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='user_favourite/start_job/(?P<job_name>\w+)')
    def user_favourite_datafiles_start_job(self, request, job_name=None):
        queryset = self.filter_queryset(
            DataFile.objects.filter(favourites=request.user))
        user_pk = request.user.pk
        obj_pks = request.data.get("ids") or list(
            queryset.values_list('pk', flat=True))
        if "ids" in request.data:
            request.data.pop("ids")
        job_args = request.data
        success, detail, job_status = start_job_from_name(
            job_name, "datafile", obj_pks, job_args, user_pk)
        return Response({"detail": detail}, status=job_status)

    # --- Favourited DataFiles (by any user) ---

    @action(detail=False, methods=['get'], url_path=r'highlights', url_name="highlight_datafiles")
    def favourited_datafiles(self, request):

        user = request.user
        if not user.is_authenticated:
            return Response({"detail": "Authentication credentials were not provided."}, status=status.HTTP_401_UNAUTHORIZED)

        # Get the data files where the favourite_of column is not null
        data_file_qs = perms['data_models.view_datafile'].filter(
            user, DataFile.objects.filter(favourite_of__isnull=False))

        # Apply filters from URL query parameters
        data_file_qs = self.filter_queryset(data_file_qs)

        if 'ctdp' in request.GET.keys():
            data_file_qs = get_ctdp_media_qs(data_file_qs)

        # Paginate the queryset
        page = self.paginate_queryset(data_file_qs)
        if page is not None:
            serializer = self.get_serializer(
                page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)

        # If no pagination, serialize all data
        serializer = self.get_serializer(
            data_file_qs, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='favourited/queryset_count')
    def favourited_datafiles_queryset_count(self, request):
        queryset = self.filter_queryset(
            DataFile.objects.filter(favourites__isnull=False).distinct())
        return Response(queryset.file_count(), status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='favourited/start_job/(?P<job_name>\w+)')
    def favourited_datafiles_start_job(self, request, job_name=None):
        queryset = self.filter_queryset(
            DataFile.objects.filter(favourites__isnull=False).distinct())
        user_pk = request.user.pk
        obj_pks = request.data.get("ids") or list(
            queryset.values_list('pk', flat=True))
        if "ids" in request.data:
            request.data.pop("ids")
        job_args = request.data
        success, detail, job_status = start_job_from_name(
            job_name, "datafile", obj_pks, job_args, user_pk)
        return Response({"detail": detail}, status=job_status)


@extend_schema(summary="Site",
               description="Locations where devices are deployed.",
               tags=["Sites"],
               methods=["get", "put", "post", "patch", "delete"],
               )
@extend_schema_view(
    list=extend_schema(summary='List sites.',
                       ),
    retrieve=extend_schema(summary='Get a single site',
                           parameters=[
                                   OpenApiParameter(
                                       "id",
                                       OpenApiTypes.INT,
                                       OpenApiParameter.PATH,
                                       description="Database ID of site to get.")]),
    partial_update=extend_schema(summary='Partially update a site',
                                 parameters=[
                                         OpenApiParameter(
                                             "id",
                                             OpenApiTypes.INT,
                                             OpenApiParameter.PATH,
                                             description="Database ID of site to update.")]),
    create=extend_schema(summary='Create site',
                         description="Add a site"),
    destroy=extend_schema(summary='Delete a site',
                          parameters=[
                                  OpenApiParameter(
                                      "id",
                                      OpenApiTypes.INT,
                                      OpenApiParameter.PATH,
                                      description="Database ID of site to delete.")]),
)
class SiteViewSet(viewsets.ReadOnlyModelViewSet, OptionalPaginationViewSetMixIn):
    """
    SiteViewSet is a Django REST Framework viewset that provides read-only access to Site objects.

    methods:
        list: Returns a paginated list of all Site objects, cached for 2 hours.
    """
    serializer_class = SiteSerializer
    queryset = Site.objects.all().distinct()
    search_fields = ['name', 'short_name']

    def list(self, request):
        return super().list(request)


@extend_schema(summary="Data type",
               description="Type of devices or of datafiles.",
               tags=["Data type"],
               methods=["get", "put", "post", "patch", "delete"],
               )
@extend_schema_view(
    list=extend_schema(summary='List data types.',

                       ),
    retrieve=extend_schema(summary='Get a data type',
                           parameters=[
                                   OpenApiParameter(
                                       "id",
                                       OpenApiTypes.INT,
                                       OpenApiParameter.PATH,
                                       description="Database ID of data type to get.")]),
    partial_update=extend_schema(summary='Partially update a data type',
                                 parameters=[
                                         OpenApiParameter(
                                             "id",
                                             OpenApiTypes.INT,
                                             OpenApiParameter.PATH,
                                             description="Database ID of data type to update.")]),
    create=extend_schema(summary='Create data type',
                         description="Add a data type"),
    destroy=extend_schema(summary='Delete a data type',
                          parameters=[
                                  OpenApiParameter(
                                      "id",
                                      OpenApiTypes.INT,
                                      OpenApiParameter.PATH,
                                      description="Database ID of data type to delete.")]),
)
class DataTypeViewSet(viewsets.ReadOnlyModelViewSet, OptionalPaginationViewSetMixIn):
    """
    DataTypeViewSet is a Django REST Framework viewset that provides read-only access to DataType objects.

    It supports searching and filtering of DataType objects based on their name.

    Methods:
        list: Returns a paginated list of all DataType objects, cached for 2 hours
    """
    serializer_class = DataTypeSerializer
    queryset = DataType.objects.all().distinct()
    search_fields = ['name']
    filterset_class = DataTypeFilter

    @method_decorator(cache_page(60 * 60 * 2))
    def list(self, request):
        return super().list(request)


@extend_schema(summary="Device Model",
               description="Models of sensors, which determine how data is handled.",
               tags=["Device models"],
               methods=["get", "put", "post", "patch", "delete"],
               )
@extend_schema_view(
    list=extend_schema(summary='List device models.',

                       ),
    retrieve=extend_schema(summary='Get a device model',
                           parameters=[
                                   OpenApiParameter(
                                       "id",
                                       OpenApiTypes.INT,
                                       OpenApiParameter.PATH,
                                       description="Database ID of device model to get.")]),
    partial_update=extend_schema(summary='Partially update a device model',
                                 parameters=[
                                         OpenApiParameter(
                                             "id",
                                             OpenApiTypes.INT,
                                             OpenApiParameter.PATH,
                                             description="Database ID of device model to update.")]),
    create=extend_schema(summary='Create device model',
                         description="Add a device model"),
    destroy=extend_schema(summary='Delete a device model',
                          parameters=[
                                  OpenApiParameter(
                                      "id",
                                      OpenApiTypes.INT,
                                      OpenApiParameter.PATH,
                                      description="Database ID of device model to delete.")]),
)
class DeviceModelViewSet(viewsets.ReadOnlyModelViewSet, OptionalPaginationViewSetMixIn):
    """
    DeviceModelViewSet is a Django REST Framework viewset that provides read-only access to Device

    Methods:
        list: Returns a paginated list of all DeviceModel objects, cached for 2 hours.

    """
    serializer_class = DeviceModelSerializer
    queryset = DeviceModel.objects.all().distinct()
    search_fields = ['name']
    filterset_class = DeviceModelFilter

    @method_decorator(cache_page(60 * 60 * 2))
    def list(self, request):
        return super().list(request)


@extend_schema(summary="Jobs",
               description="Generic jobs that can be run on objects.",
               tags=["Jobs"],
               methods=["get"],
               )
class GenericJobViewSet(viewsets.ViewSet):
    """
    GenericJobViewSet is a Django REST Framework viewset that provides read-only access to generic jobs.
    It allows users to retrieve a list of available jobs and details about specific jobs.

    Methods:
        list: Returns a list of all available generic jobs, filtered by data type if specified.
        retrieve: Returns details of a specific job by its index in the settings.GENERIC_JOBS list.

    """

    # Required for the Browsable API renderer to have a nice form.
    serializer_class = GenericJobSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        job_list = settings.GENERIC_JOBS.values()
        if not user.is_staff:
            job_list = [x for x in job_list if not x["admin_only"]]

        data_type = self.request.query_params.get('data_type')
        if data_type is not None:
            job_list = [x for x in job_list if x["data_type"] == data_type]
        return job_list

    # @method_decorator(cache_page(60 * 60 * 2))
    # @method_decorator(vary_on_cookie)
    def list(self, request):

        serializer = self.serializer_class(
            instance=self.get_queryset(), many=True)

        return Response(serializer.data)

    # @method_decorator(cache_page(60 * 60 * 2))
    # @method_decorator(vary_on_cookie)
    def retrieve(self, request, pk=None):
        try:
            job_dict = list(settings.GENERIC_JOBS.values())[int(pk)]
        except (IndexError, ValueError):
            return Response(status=404)

        serializer = self.serializer_class(job_dict)
        return Response(serializer.data)
