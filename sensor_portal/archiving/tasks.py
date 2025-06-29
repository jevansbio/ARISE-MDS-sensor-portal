import logging
import os
from posixpath import join as posixjoin
from typing import Any, Callable, List, Optional

from celery import chord, group, shared_task
from data_models.job_handling_functions import register_job
from data_models.models import DataFile, TarFile
from django.conf import settings
from django.utils import timezone as djtimezone
from utils.general import divide_chunks
from utils.task_functions import TooManyTasks, check_simultaneous_tasks

from sensor_portal.celery import app

from .exceptions import TAROffline
from .models import Archive
from .tar_functions import check_tar_status, create_tar_files

logger = logging.getLogger(__name__)


@app.task(name="unarchive_files")
@register_job("Unarchive files", "unarchive_files", "datafile", True,
              default_args={})
def unarchive_files(datafile_pks: List[int], **kwargs):
    file_objs = DataFile.objects.filter(
        pk__in=datafile_pks, archived=True, local_storage=False)
    get_files_from_archive_task(list(file_objs.values_list('pk', flat=True)))


@app.task()
def check_all_archive_projects_task() -> None:
    """
    Check all archive projects by iterating through all Archive objects and calling their check_projects method.
    """
    all_archives = Archive.objects.all()
    # Iterate through every archive and check its projects
    for archive in all_archives:
        archive.check_projects()


@app.task()
def check_all_uploads_task() -> None:
    """
    Check uploads for all Archive objects by calling their check_upload method.
    """
    all_archives = Archive.objects.all()
    # Iterate through every archive and check its uploads
    for archive in all_archives:
        archive.check_upload()


@app.task()
def create_tar_files_task(file_pks: List[int], archive_pk: int) -> None:
    """
    Task wrapper for create_tar_files function.

    Args:
        file_pks (List[int]): Primary keys of files to be TARred.
        archive_pk (int): Primary key of archive to which these TARs will be attached.
    """
    # Calls the actual function to handle TAR file creation
    create_tar_files(file_pks, archive_pk)


@app.task()
def check_archive_upload_task(archive_pk: int) -> None:
    """
    Check upload for a specific archive.

    Args:
        archive_pk (int): Primary key of the archive.
    """
    # Find the archive by PK and trigger upload check
    archive = Archive.objects.get(pk=archive_pk)
    archive.check_upload()


@app.task()
def get_files_from_archive_task(file_pks: List[int], callback: Optional[Callable] = None) -> None:
    """
    For a list of DataFile PKs, orchestrate their retrieval from archives using Celery groups and chords.

    Args:
        file_pks (List[int]): Primary keys of files to retrieve.
        callback (Optional[Callable]): Optional callback task to run after retrieval.
    """
    # Filter for only archived files matching the provided PKs
    file_objs = DataFile.objects.filter(pk__in=file_pks, archived=True)

    logger.info("Get TAR files")

    # Get unique TAR files containing these files
    tar_file_objs = TarFile.objects.filter(
        pk__in=file_objs.values_list('tar_file__pk', flat=True).distinct())
    tar_file_pks = list(tar_file_objs.values_list('pk', flat=True))

    all_tasks = []
    # For each TAR, create an async job for its files
    for tar_file_pk in tar_file_pks:
        target_file_pks = list(file_objs.filter(
            tar_file__pk=tar_file_pk).values_list('pk', flat=True))
        logger.info(f"TAR {tar_file_pk} has {len(target_file_pks)} files")
        all_tasks.append(get_files_from_archived_tar_task.si(
            tar_file_pk, target_file_pks))

    task_group = group(all_tasks)  # Celery group for parallel execution

    # Callback tasks to run after all file retrieval jobs
    post_tasks = [post_get_file_from_archive_task.s()]
    if callback is not None:
        post_tasks.append(callback)
    post_task_group = group(post_tasks)
    # Chord schedules post-tasks after all group tasks
    task_chord = chord(task_group, post_task_group)
    logger.info("Start unarchiving tasks")
    task_chord.apply_async()


@app.task()
def post_get_file_from_archive_task(all_file_pks: List[List[int]]) -> None:
    """
    After files are retrieved from archive, process them by sensor model and file format.

    Args:
        all_file_pks (List[List[int]]): Nested lists of file PKs.
    """
    # Flatten the list of lists of PKs into a single list
    all_file_pks_flat = [item for items in all_file_pks for item in items]
    # Query all DataFile objects just downloaded
    file_objs = DataFile.objects.filter(pk__in=all_file_pks_flat)
    # Find all unique device models (sensor models) present in these files
    device_models = file_objs.values_list(
        "deployment__device__model", flat=True).distinct()

    # For each unique device model, process files by format
    for device_model in device_models:
        sensor_model_file_objs = file_objs.filter(
            deployment__device__model=device_model)
        # Look up the handler for this model
        data_handler = settings.DATA_HANDLERS.get_handler(
            device_model.type.name, device_model.name)
        # Find all unique file formats for files from this model
        device_file_formats = sensor_model_file_objs.values_list(
            "file_format", flat=True).distinct()

        # For each file format, create and dispatch a post-download task if available
        for device_file_format in device_file_formats:
            device_model_format_file_objs = sensor_model_file_objs.filter(
                file_format=device_file_format)
            device_model_format_file_file_names = list(
                device_model_format_file_objs.values_list("file_name", flat=True))
            task_name = data_handler.get_post_download_task(
                device_file_format, False)
            if task_name is not None:
                new_task = app.signature(
                    task_name, [device_model_format_file_file_names], immutable=True)
                new_task.apply_async()  # Schedule the post-download processing


@app.task(autoretry_for=(TooManyTasks, TAROffline),
          max_retries=None,
          retry_backoff=10*60,
          retry_backoff_max=60 * 60,
          retry_jitter=True,
          bind=True)
def get_files_from_archived_tar_task(self: Any, tar_file_pk: int, target_file_pks: List[int]) -> List[int]:
    """
    Retrieve specified files from a TAR archive, handling staging, extraction, and local placement.

    Args:
        self (Any): Task instance (provided by Celery when bind=True).
        tar_file_pk (int): Primary key of the TarFile object.
        target_file_pks (List[int]): List of file PKs to retrieve.

    Returns:
        List[int]: Primary keys of successfully retrieved DataFile objects.
    """
    # Limit the number of simultaneous tasks of this type to avoid overloading resources
    check_simultaneous_tasks(self, 4)

    tar_file_obj = TarFile.objects.get(pk=tar_file_pk)
    file_objs = DataFile.objects.filter(pk__in=target_file_pks)
    file_names = file_objs.full_names().values_list("full_name", flat=True)

    # Connect to the archive server via SSH
    archive_obj = tar_file_obj.archive
    ssh_client = archive_obj.init_ssh_client()

    # Try to locate the compressed TAR file first

    if not tar_file_obj.name.endswith('.tar.gz'):
        tar_name = tar_file_obj.name + '.tar.gz'
    tar_path = posixjoin(tar_file_obj.path, tar_name)

    # Check if the TAR file is online or needs to be staged from tape
    status_code, target_tar_status = check_tar_status(ssh_client, tar_path)
    logger.info(f"{tar_path}: Get TAR status {status_code}")

    # If not found, try without .tar.gz extension
    if status_code == 1:
        tar_name = tar_file_obj.name
        tar_path = posixjoin(tar_file_obj.path, tar_name)
        status_code, target_tar_status = check_tar_status(ssh_client, tar_path)
        logger.info(f"{tar_path}: Get TAR status  {status_code}")
        if status_code == 1:
            raise Exception(f"{tar_path}: TAR file not present at this path")

    logger.info(
        f"{tar_path}: Get TAR status {status_code} {target_tar_status}")

    # If not online, try to retrieve from tape storage (or handle unmigrating state)
    online_statuses = ['(REG)', '(DUL)', '(MIG)', '(NA)', '(QUE)']
    if target_tar_status not in online_statuses:
        initial_offline = True
        logger.info(f"{tar_path}: Offline")
        if target_tar_status != '(UNM)':
            # Request data to be staged from tape
            status_code, stdout, stderr = ssh_client.send_ssh_command(
                f"daget {tar_path}")
            logger.info(
                f"{tar_path}: Get TAR from tape {status_code} {stdout}")
            status_code, target_tar_status = check_tar_status(
                ssh_client, tar_path)
        else:
            raise (TAROffline(f"{tar_path}: already unmigrating"))

        if target_tar_status not in online_statuses:
            # If still not online after staging attempt, raise error
            raise Exception(f"{tar_path}: TAR file could not be staged")
    else:
        initial_offline = False

    # Create a temporary extraction directory for this job
    temp_path = posixjoin(tar_file_obj.path, "temp", self.request.id)
    ftp_connection_success = ssh_client.connect_to_ftp()
    if not ftp_connection_success:
        raise Exception("Unable to connect to FTP")

    ssh_client.mkdir_p(temp_path)

    # List files inside the TAR to locate the desired files
    status_code, stdout, stderr = ssh_client.send_ssh_command(
        f"tar tvf {tar_path}", return_strings=False)
    logger.info(f"{tar_path}: List files in TAR")

    in_tar_file_paths: List[str] = []
    in_tar_found_files: List[Any] = []
    for file_line in stdout:
        # Parse each line of tar output to extract the file path
        split_file_line = file_line.split(" ")
        line_file_path = split_file_line[-1].replace("\n", "")
        # Check if this is one of our requested files
        found_file_paths = [x for x in file_names if x in line_file_path]
        if len(found_file_paths) > 0:
            in_tar_file_paths.append(line_file_path)
            in_tar_found_files.append(found_file_paths[0])
            logger.info(
                f"{tar_path}: {len(in_tar_file_paths)}/{len(file_names)}")
        if len(in_tar_file_paths) == len(file_names):
            # Stop early if all target files found
            logger.info(f"{tar_path}: All files_found")
            break

    if len(in_tar_file_paths) == 0:
        # None of the requested files were found in the TAR archive
        raise Exception(f"{tar_path}: No files found in TAR")
    else:
        # Log any requested files not found in the archive
        missing_files = [x for x in file_names if x not in in_tar_found_files]
        if len(missing_files) > 0:
            logger.info(f"{tar_path}: Files not found: {missing_files}")

    # Extract files in manageable chunks to avoid command length limits
    chunked_in_tar_file_paths = [
        x for x in divide_chunks(in_tar_file_paths, 500)]
    for idx, in_tar_file_paths_set in enumerate(chunked_in_tar_file_paths):
        logger.info(
            f"{tar_path}: Extract file chunk {idx}/{len(chunked_in_tar_file_paths)}")
        combined_in_tar_file_paths = (
            " ".join([f"'{x}'" for x in in_tar_file_paths_set]))
        status_code, stdout, stderr = ssh_client.send_ssh_command(
            f"tar -zxvf {tar_path} -C {temp_path} {combined_in_tar_file_paths}")
        logger.info(
            f"{tar_path}: Extract file chunk {idx}/{len(chunked_in_tar_file_paths)} {status_code}")

    # Connect to SCP for file transfer from archive to local storage
    ssh_client.connect_to_scp()
    file_objs_to_update: List[DataFile] = []
    all_pks: List[int] = []
    for idx, in_tar_file_path in enumerate(in_tar_file_paths):
        try:
            full_file_name = os.path.split(in_tar_file_path)[1]
            file_name = os.path.splitext(full_file_name)[0]
            # Get the corresponding DataFile object
            file_obj = file_objs.get(file_name=file_name)
            # Prepare the local storage directory
            local_dir = os.path.join(settings.FILE_STORAGE_ROOT, file_obj.path)
            os.makedirs(local_dir, exist_ok=True)
            local_file_path = os.path.join(local_dir, full_file_name)

            temp_file_path = posixjoin(temp_path, in_tar_file_path)
            if not os.path.exists(local_file_path):
                # Transfer file from archive temp path to local storage
                ssh_client.scp_c.get(
                    temp_file_path, local_file_path, preserve_times=True)

            # Mark file as locally available and update metadata
            file_obj.modified_on = djtimezone.now()
            file_obj.local_path = settings.FILE_STORAGE_ROOT
            file_obj.local_storage = True
            file_objs_to_update.append(file_obj)
            all_pks.append(file_obj.pk)
        except Exception as e:
            # Log and continue on any per-file errors
            logger.info(f"{tar_path}: Error retrieving file: {repr(e)}")
    logger.info(f"{tar_path}: Update database")
    DataFile.objects.bulk_update(file_objs_to_update, fields=[
                                 "local_path", "local_storage", "modified_on"])
    logger.info(f"{tar_path}: Clear temporary files")
    # Remove temporary extraction files from the archive server
    status_code, stdout, stderr = ssh_client.send_ssh_command(
        f"rm -rf {temp_path}")

    ssh_client.close_connection()

    return all_pks
