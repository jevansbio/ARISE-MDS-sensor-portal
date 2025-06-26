import json
import os
from typing import Tuple
from zipfile import ZipFile

from camtrap_dp_export.metadata_functions import create_camtrap_dp_metadata
from data_models.metadata_functions import create_metadata_dict
from django.conf import settings
from django.db.models import F, QuerySet, Value
from django.db.models.functions import Concat
from observation_editor.metadata_functions import \
    create_metadata_dict as create_obs_metadata_dict
from observation_editor.models import Observation


def create_zip(
    zip_name: str,
    file_objs: QuerySet,
    metadata_type: int,
    includes_files: bool
) -> Tuple[bool, str]:
    """
    Creates a zip archive containing data or media files along with associated metadata.

    Args:
        zip_name (str): The base name of the zip file. ".zip" will be appended if not present.
        file_objs (QuerySet): A Django QuerySet of file objects to include in the zip.
        metadata_type (int): Type of metadata to include.
            0 = Standard metadata and observation metadata (metadata.json, observations.json).
            1 = Camtrap DP metadata (media.csv, observations.csv, deployments.csv, events.csv, datapackage.json).
        includes_files (bool): If True, only include files with local storage.

    Returns:
        Tuple[bool, str]: 
            - Success status (True if the zip was created, False otherwise).
            - Path to the created package directory (empty string if unsuccessful).
    """
    if includes_files:
        file_objs = file_objs.filter(local_storage=True)

    package_path = os.path.join(
        settings.FILE_STORAGE_ROOT, settings.PACKAGE_PATH)
    os.makedirs(package_path, exist_ok=True)

    if ".zip" not in zip_name:
        zip_name = f"{zip_name}.zip"

    file_objs = file_objs.full_paths()

    match metadata_type:
        case 0:
            file_objs = file_objs.annotate(zip_path=Concat(
                Value('data'), Value(os.sep), F('relative_path')))
        case 1:
            file_objs = file_objs.annotate(
                zip_path=Concat(Value('media'), Value(os.sep), F('relative_path')))

        case _:
            return False, ""

    with ZipFile(os.path.join(package_path, zip_name), 'w') as zip_file:

        if (includes_files):

            for file_obj in file_objs:
                zip_file.write(file_obj.full_path, file_obj.zip_path)

        match metadata_type:
            case 0:
                metadata_dict = create_metadata_dict(file_objs)
                observation_dict = create_obs_metadata_dict(
                    Observation.objects.filter(data_files__in=file_objs))

                metadata_dict["data_files"] = [
                    {**x, "path": os.path.join("data", x["path"])} for x in metadata_dict["data_files"]]

                with zip_file.open("metadata.json", "w") as f:
                    f.write(json.dumps(metadata_dict, indent=2).encode("utf-8"))

                with zip_file.open("observations.json", "w") as f:
                    f.write(json.dumps(observation_dict,
                            indent=2).encode("utf-8"))

            case 1:
                uuid = zip_name.split("_")[0]
                file_df, observation_df, deploy_df, event_df, metadata = create_camtrap_dp_metadata(
                    file_objs, uuid, zip_name)

                file_df["filePath"] = [os.path.join(
                    "media", x) for x in file_df["filePath"]]

                with zip_file.open("media.csv", "w") as df:
                    file_df.to_csv(df, index=False)

                with zip_file.open("observations.csv", "w") as df:
                    observation_df.to_csv(df, index=False)

                with zip_file.open("deployments.csv", "w") as df:
                    deploy_df.to_csv(df, index=False)

                with zip_file.open("events.csv", "w") as df:
                    event_df.to_csv(df, index=False)

                with zip_file.open("datapackage.json", "w") as f:
                    f.write(json.dumps(metadata, indent=2).encode("utf-8"))

            case _:
                return False, ""

    return True, package_path
