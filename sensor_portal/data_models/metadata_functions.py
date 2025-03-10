import json
import os

from django.db.models import QuerySet

from .models import DataFile, Deployment, Device, Project
from .serializers import (DataFileSerializer, DeploymentSerializer,
                          DeviceSerializer, ProjectSerializer)


def metadata_json_from_files(file_objs: QuerySet[DataFile], output_path: str):
    metadata_dict = create_metadata_dict(file_objs)
    os.makedirs(output_path, exist_ok=True)
    metadata_json_path = os.path.join(output_path, "metadata.json")

    # json dump file
    with open(metadata_json_path, "w") as f:
        f.write(json.dumps(metadata_dict, indent=2))

    return metadata_json_path


def create_metadata_dict(file_objs: QuerySet[DataFile]) -> list[dict]:
    """_summary_

    Args:
        file_objs (QuerySet[DataFile]): _description_

    Returns:
        list[dict]: _description_
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
