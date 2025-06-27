import json
import os

from django.db.models import QuerySet

from .models import DataFile, Deployment, Device, Project
from .serializers import (DataFileSerializer, DeploymentSerializer,
                          DeviceSerializer, ProjectSerializer)


def metadata_json_from_files(file_objs: QuerySet[DataFile], output_path: str):
    """
    Create a JSON file containing metadata for a collection of DataFile objects.

    This function gathers metadata from the provided DataFile queryset, serializes it
    (including related projects, devices, and deployments), and writes the result to
    a "metadata.json" file in the specified output directory.

    Args:
        file_objs (QuerySet[DataFile]): Queryset of DataFile objects whose metadata will be included.
        output_path (str): Directory path where the resulting JSON file should be saved.

    Returns:
        str: Full file path to the generated "metadata.json".

    Raises:
        OSError: If the output directory cannot be created or the file cannot be written.

    Notes:
        - The output directory will be created if it does not already exist.
        - The resulting JSON file is formatted with an indentation of 2 spaces.
        - Related metadata for projects, devices, and deployments is automatically included.
    """

    metadata_dict = create_metadata_dict(file_objs)
    os.makedirs(output_path, exist_ok=True)
    metadata_json_path = os.path.join(output_path, "metadata.json")

    # json dump file
    with open(metadata_json_path, "w") as f:
        f.write(json.dumps(metadata_dict, indent=2))

    return metadata_json_path


def create_metadata_dict(file_objs: QuerySet[DataFile]) -> dict:
    """
    Construct a dictionary of serialized metadata for the given DataFile objects.

    This function collects all related deployments, projects, and devices associated
    with the provided DataFile queryset, and serializes each entity type using their
    respective serializers. The result is a dictionary suitable for JSON export.

    Args:
        file_objs (QuerySet[DataFile]): Queryset of DataFile objects for which to generate metadata.

    Returns:
        dict: A dictionary with the following structure:
            {
                "projects": [<serialized Project objects>],
                "devices": [<serialized Device objects>],
                "deployments": [<serialized Deployment objects>],
                "data_files": [<serialized DataFile objects>]
            }

    Notes:
        - Only projects, devices, and deployments related to the input files are included.
        - DataFile objects are serialized as provided in the input queryset.
    """

    deployment_objs = Deployment.objects.filter(files__in=file_objs).distinct()
    project_objs = Project.objects.filter(
        deployments__in=deployment_objs).distinct()
    device_objs = Device.objects.filter(
        deployments__in=deployment_objs).distinct()

    file_dict = DataFileSerializer(file_objs, many=True).data
    deployment_dict = DeploymentSerializer(deployment_objs, many=True).data
    project_dict = ProjectSerializer(project_objs, many=True).data
    device_dict = DeviceSerializer(device_objs, many=True).data

    all_dict = {"projects": project_dict, "devices": device_dict,
                "deployments": deployment_dict, "data_files": file_dict}

    return all_dict
