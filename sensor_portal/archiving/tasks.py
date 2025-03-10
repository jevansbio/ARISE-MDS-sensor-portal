
import os
from posixpath import join as posixjoin

from celery import chord, group, shared_task
from data_models.models import DataFile, TarFile
from django.conf import settings
from django.utils import timezone as djtimezone
from utils.general import divide_chunks
from utils.task_functions import TooManyTasks, check_simultaneous_tasks

from sensor_portal.celery import app

from .exceptions import TAROffline
from .models import Archive
from .tar_functions import check_tar_status, create_tar_files


@shared_task
def check_all_archive_projects_task():
    all_archives = Archive.objects.all()
    for archive in all_archives:
        archive.check_projects()


@shared_task
def check_all_uploads_task():
    all_archives = Archive.objects.all()
    for archive in all_archives:
        archive.check_upload()


@shared_task
def create_tar_files_task(file_pks: list[int], archive_pk: int):
    """
    Task wrapper for create_tar_files function.

    Args:
        file_pks (list[int]): pks of files to be TARred
        archive_pk (int): pk of archive to which these TARs will be attached
    """
    create_tar_files(file_pks, archive_pk)


@shared_task
def check_archive_upload_task(archive_pk: int):
    archive = Archive.objects.get(pk=archive_pk)
    archive.check_upload()


@shared_task
def get_files_from_archive_task(file_pks, callback=None):
    file_objs = DataFile.objects.filter(pk__in=file_pks, archived=True)

    # Get unique TAR files
    tar_file_objs = TarFile.objects.filter(
        pk__in=file_objs.values_list('tar_file__pk', flat=True).distinct())
    tar_file_pks = list(tar_file_objs.values_list('pk', flat=True))

    all_tasks = []
    # For each TAR create job to retrieve files
    for tar_file_pk in tar_file_pks:
        target_file_pks = list(file_objs.filter(
            tar_file__pk=tar_file_pk).values_list('pk', flat=True))
        all_tasks.append(get_files_from_archived_tar_task.si(
            tar_file_pk, target_file_pks))

    task_group = group(all_tasks)

    post_tasks = [post_get_file_from_archive_task.s()]
    if callback is not None:
        post_tasks.append(callback)
    post_task_group = group(post_tasks)
    task_chord = chord(task_group, post_task_group)
    task_chord.apply_async()


@shared_task
def post_get_file_from_archive_task(all_file_pks):
    # flatten list of lists

    all_file_pks_flat = [item for items in all_file_pks for item in items]
    # schedule post download tasks
    file_objs = DataFile.objects.filter(pk__in=all_file_pks_flat)
    # get unique sensor models
    device_models = file_objs.values_list(
        "deployment__device__model", flat=True).distinct()
    # for each sensor model

    for device_model in device_models:
        sensor_model_file_objs = file_objs.filter(
            deployment__device__model=device_model)
        data_handler = settings.DATA_HANDLERS.get_handler(
            device_model.type.name, device_model.name)
        # get unique file formats
        device_file_formats = sensor_model_file_objs.values_list(
            "file_format", flat=True).distinct()

        for device_file_format in device_file_formats:
            # get files with this sensor model ,this file format
            device_model_format_file_objs = sensor_model_file_objs.filter(
                file_format=device_file_format)
            device_model_format_file_file_names = list(
                device_model_format_file_objs.values_list("file_name", flat=True))
            task_name = data_handler.get_post_download_task(
                device_file_format, False)
            if task_name is not None:
                new_task = app.signature(
                    task_name, [device_model_format_file_file_names], immutable=True)
                # submit jobs
                new_task.apply_async()


@shared_task(autoretry_for=(TooManyTasks, TAROffline),
             max_retries=None,
             retry_backoff=2*60,
             retry_backoff_max=5 * 60,
             retry_jitter=True,
             bind=True)
def get_files_from_archived_tar_task(self, tar_file_pk, target_file_pks):

    check_simultaneous_tasks(self, 4)

    tar_file_obj = TarFile.objects.get(pk=tar_file_pk)
    file_objs = DataFile.objects.filter(pk__in=target_file_pks)
    file_names = file_objs.full_names()
    # Connect to archive
    archive_obj = tar_file_obj.archive
    ssh_client = archive_obj.init_ssh_client()

    # Find target TAR file
    tar_name = tar_file_obj.name+'.tar.gz'
    tar_path = posixjoin(tar_file_obj.path, tar_name)
    status_code, stdout, stderr = ssh_client.send_ssh_command(
        f"dmls -l {tar_path}")

    status_code, target_tar_status = check_tar_status(ssh_client, tar_path)
    print(
        f"{tar_path}: Get TAR status {status_code}")

    if status_code == 1:
        tar_name = tar_file_obj.name
        tar_path = posixjoin(tar_file_obj.path, tar_name)
        status_code, target_tar_status = check_tar_status(ssh_client, tar_path)
        print(
            f"{tar_path}: Get TAR status  {status_code}")
        if status_code == 1:
            raise Exception(f"{tar_path}: TAR file not present at this path")

    print(
        f"{tar_path}: Get TAR status {status_code} {target_tar_status}")

    online_statuses = ['(REG)', '(DUL)', '(MIG)']
    if target_tar_status not in online_statuses:
        initial_offline = True
        print(f"{tar_path}: Offline")
        if target_tar_status != '(UNM)':
            status_code, stdout, stderr = ssh_client.send_ssh_command(
                f"dmget {tar_path}")
            print(
                f"{tar_path}: Get TAR from tape {status_code} {stdout}")

            status_code, target_tar_status = check_tar_status(
                ssh_client, tar_path)
        else:
            # TAR is already unmigrating
            raise (TAROffline(f"{tar_path}: already unmigrating"))

        if target_tar_status not in online_statuses:
            # This shouldn't happen.
            raise Exception(f"{tar_path}: TAR file could not be staged")

    else:
        initial_offline = False

    temp_path = posixjoin(tar_file_obj.path, "temp", self.request.id)
    ftp_connection_success = ssh_client.connect_to_ftp()
    if not ftp_connection_success:
        raise Exception("Unable to connect to FTP")

    ssh_client.mkdir_p(temp_path)

    status_code, stdout, stderr = ssh_client.send_ssh_command(
        f"tar tvf {tar_path}", return_strings=False)

    print(f"{tar_path}: List files in TAR")

    in_tar_file_paths = []
    in_tar_found_files = []
    for file_line in stdout:
        # extract the tar output line's filepath
        split_file_line = file_line.split(" ")
        line_file_path = split_file_line[-1].replace("\n", "")
        found_file_paths = [x for x in file_names if x in line_file_path]
        if len(found_file_paths) > 0:
            # If this file is one of our target file, save the in-tar path
            in_tar_file_paths.append(line_file_path)
            in_tar_found_files.append(found_file_paths[0])
            print(f"{tar_path}: {len(in_tar_file_paths)}/{len(file_names)}")

        if len(in_tar_file_paths) == len(file_names):
            # If we have found all our target_files
            print(f"{tar_path}: All files_found")
            break

    if len(in_tar_file_paths) == 0:
        raise Exception(f"{tar_path}: No files found in TAR")
    else:
        missing_files = [x for x in file_names if x not in in_tar_found_files]
        if len(missing_files) > 0:
            print(f"{tar_path}: Files not found: {missing_files}")

    chunked_in_tar_file_paths = [
        x for x in divide_chunks(in_tar_file_paths, 500)]
    for idx, in_tar_file_paths_set in enumerate(chunked_in_tar_file_paths):
        print(f"{tar_path}: Extract file chunk {idx}/{len(chunked_in_tar_file_paths)}")
        combined_in_tar_file_paths = (
            " ".join([f"'{x}'" for x in in_tar_file_paths_set]))
        status_code, stdout, stderr = ssh_client.send_ssh_command(
            f"tar -zxvf {tar_path} -C {temp_path} {combined_in_tar_file_paths}"
        )
        print(
            f"{tar_path}: Extract file chunk {idx}/{len(chunked_in_tar_file_paths)} {status_code}")

    ssh_client.connect_to_scp()
    file_objs_to_update = []
    all_pks = []
    for idx, in_tar_file_path in enumerate(in_tar_file_paths):
        try:
            full_file_name = os.path.split(in_tar_file_path)[1]
            file_name = os.path.splitext(full_file_name)[0]

            # get file object
            file_obj = file_objs.get(file_name=file_name)
            local_dir = os.path.join(settings.FILE_STORAGE_ROOT, file_obj.path)
            os.makedirs(local_dir, exist_ok=True)
            local_file_path = os.path.join(local_dir, full_file_name)

            temp_file_path = posixjoin(temp_path, in_tar_file_path)
            if not os.path.exists(local_file_path):
                ssh_client.scp_c.get(
                    temp_file_path, local_file_path, preserve_times=True)

            file_obj.modified_on = djtimezone.now()
            file_obj.local_path = settings.FILE_STORAGE_ROOT
            file_obj.local_storage = True
            file_objs_to_update.append(file_obj)
            all_pks.append(file_obj.pk)
        except Exception as e:
            print(f"{tar_path}: Error retrieving file: {repr(e)}")
    print(f"{tar_path}: Update database")
    DataFile.objects.bulk_update(file_objs_to_update, fields=[
                                 "local_path", "local_storage", "modified_on"])
    print(f"{tar_path}: Clear temporary files")
    status_code, stdout, stderr = ssh_client.send_ssh_command(
        f"rm -rf {temp_path}")

    ssh_client.close_connection()

    return all_pks
