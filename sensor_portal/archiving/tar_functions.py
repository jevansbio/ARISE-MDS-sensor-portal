import logging
import os
from datetime import datetime
from posixpath import join as posixjoin
from typing import Any, Dict, List, Optional, Tuple

from data_models.file_handling_functions import group_files_by_size
from data_models.metadata_functions import metadata_json_from_files
from data_models.models import DataFile
from django.conf import settings
from django.db.models import QuerySet
from utils.general import (call_with_output, try_remove_file_clean_dirs,
                           try_to_remove_dirs)
from utils.ssh_client import SSH_client

from .bagit_functions import bag_info_from_files
from .models import Archive, TarFile

logger = logging.getLogger(__name__)


def create_tar_files(file_pks: List[int], archive_pk: int) -> None:
    """
    Split files into appropriately sized groups and create tar files for each group.

    Args:
        file_pks (List[int]): List of primary keys of DataFile objects to be archived.
        archive_pk (int): Primary key of the Archive object to associate tar files with.
    """
    file_objs = DataFile.objects.filter(pk__in=file_pks)

    # Assign these files to a dummy TAR
    in_progress_tar, created = TarFile.objects.get_or_create(
        name="in_progress", uploading=True)
    file_objs.update(tar_file=in_progress_tar)

    file_splits_ok = get_tar_splits(file_objs)
    archive_obj = Archive.objects.get(pk=archive_pk)

    for idx, file_split in enumerate(file_splits_ok):
        file_split_pks = file_split['file_pks']
        file_split_objs = DataFile.objects.filter(pk__in=file_split_pks)
        create_tar_file_and_obj(file_split_objs, archive_obj, idx)


def create_tar_file_and_obj(
    file_objs: QuerySet,
    archive_obj: Archive,
    name_suffix: int = 0
) -> bool:
    """
    Create a tar file from file_objs and register a TarFile object in the database.

    Args:
        file_objs (QuerySet): QuerySet of DataFile objects to be archived.
        archive_obj (Archive): Archive instance to associate TarFile with.
        name_suffix (int, optional): Suffix for the tar file name.

    Returns:
        bool: True if tar file creation succeeded, False otherwise.
    """
    success, tar_name, full_tar_path = create_tar_file(
        file_objs, name_suffix)
    if not success:
        # Free data file objects
        file_objs.update(tar_file=None)
        return False
    else:
        new_tar_obj = TarFile.objects.create(
            name=tar_name,
            path=os.path.split(full_tar_path)[0],
            archive=archive_obj)
        file_objs.update(tar_file=new_tar_obj)
        return True


def get_tar_splits(file_objs: QuerySet) -> List[Dict[str, Any]]:
    """
    Split a set of files into groups suitable for tarring, based on size.

    Args:
        file_objs (QuerySet): QuerySet of DataFile objects.

    Returns:
        List[Dict[str, Any]]: List of dictionaries describing file splits that meet size requirements.
    """
    file_splits = group_files_by_size(file_objs)

    too_small_split_pks = [
        x for y in file_splits if y["total_size_gb"] < settings.MIN_ARCHIVE_SIZE_GB for x in y['file_pks']]
    # Remove files whose TAR would not be large enough from the in progress tar
    too_small_file_objs = DataFile.objects.filter(pk__in=too_small_split_pks)
    n_removed_files = too_small_file_objs.update(tar_file=None)
    logger.info(f"{n_removed_files} in too small a grouping")

    file_splits_ok = [
        x for x in file_splits if x["total_size_gb"] >= settings.MIN_ARCHIVE_SIZE_GB]
    return file_splits_ok


def get_tar_name(file_objs: QuerySet, suffix: int = 0) -> str:
    """
    Generate a descriptive tar file name based on file attributes and date range.

    Args:
        file_objs (QuerySet): QuerySet of DataFile objects.
        suffix (int, optional): Suffix for the tar file name.

    Returns:
        str: The generated tar file name (without file extension).
    """
    min_date = file_objs.min_date()
    min_date_str = min_date.strftime("%Y%m%d")
    max_date = file_objs.max_date()
    max_date_str = max_date.strftime("%Y%m%d")
    combo_project = file_objs.values_list(
        "deployment__combo_project", flat=True).first().replace("-", "").replace(" ", "-")
    device_type = file_objs.device_type().values_list(
        "device_type", flat=True).first().replace(" ", "")

    creation_dt = datetime.now().strftime("%Y%m%d_%H%M%S")

    tar_name = ("_").join([combo_project, device_type,
                           min_date_str, max_date_str, creation_dt, str(suffix)])

    return tar_name


def create_tar_file(
    file_objs: QuerySet,
    name_suffix: int = 0
) -> Tuple[bool, str, Optional[str]]:
    """
    Create a tar.gz archive for the given files, add metadata, and clean up.

    Args:
        file_objs (QuerySet): QuerySet of DataFile objects to be archived.
        name_suffix (int, optional): Suffix for the tar file name.

    Returns:
        Tuple[bool, str, Optional[str]]: (Success status, tar file name, full tar file path if successful, else None)
    """
    # get TAR name
    tar_name = get_tar_name(file_objs, name_suffix)
    tar_name_format = tar_name+".tar.gz"

    device_type = file_objs.device_type().values_list(
        "device_type", flat=True).first().replace(" ", "")

    tar_path = os.path.join(settings.FILE_STORAGE_ROOT,
                            "archiving",
                            device_type,
                            datetime.now().strftime("%Y%m%d"))
    os.makedirs(tar_path, exist_ok=True)
    full_tar_path = os.path.join(tar_path, tar_name_format)
    # get list of file paths
    relative_paths = list(file_objs.relative_paths(
    ).values_list("relative_path", flat=True))

    metadata_dir_path = os.path.join(tar_path, tar_name)
    relative_metadata_dir_path = os.path.relpath(
        metadata_dir_path, settings.FILE_STORAGE_ROOT)

    # Generate bagit metadata
    all_metadata_paths = []
    try:
        logger.info(f"{tar_name}: generating bagit data")
        all_metadata_paths = bag_info_from_files(file_objs, metadata_dir_path)

        logger.info(f"{tar_name}: generating metadata file")
        # Generate metadata file
        metadata_json_path = metadata_json_from_files(
            file_objs, metadata_dir_path)

        all_metadata_paths.append(metadata_json_path)

        relative_metadata_paths = [os.path.relpath(
            x, settings.FILE_STORAGE_ROOT) for x in all_metadata_paths]

        logger.info(f"{tar_name}: generating TAR file")
        # Use transform command to generate data dir inside the TAR, move metadata files to root
        tar_command = ["tar", "zcvf", full_tar_path,
                       "--transform", f"s,^,data/,;s,data/{relative_metadata_dir_path}/,,",] + relative_paths + relative_metadata_paths
        success, output = call_with_output(
            tar_command, settings.FILE_STORAGE_ROOT)

    except Exception as e:
        logger.error(e)
        output = ""
        success = False

    # regardless of status, we remove the metadata files
    [try_remove_file_clean_dirs(x) for x in all_metadata_paths]
    try_to_remove_dirs(metadata_dir_path)

    if not success:
        logger.error(f"{tar_name}: Error creating TAR")
        logger.error(output)
        return False, tar_name, None
    logger.info(f"{tar_name}: succesfully created")
    return True, tar_name, full_tar_path


def check_tar_status(
    ssh_client: SSH_client,
    tar_path: str
) -> Tuple[int, Optional[str]]:
    """
    Check the status of a tar file on a remote system via SSH.

    Args:
        ssh_client (SSH_client): SSH client instance for remote command execution.
        tar_path (str): Path to the tar file on the remote system.

    Returns:
        Tuple[int, Optional[str]]: (Status code, tar file status string if successful, else None)
    """
    status_code, stdout, stderr = ssh_client.send_ssh_command(
        f"dals -l {posixjoin(tar_path)}")
    if status_code != 0:
        return status_code, None
    target_tar_status = stdout[1].split(" ")[-2]
    return status_code, target_tar_status
