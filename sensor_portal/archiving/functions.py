import os
import traceback

from celery import chord, group
from data_models.models import DataFile
from django.conf import settings
from scp import SCPException

from .models import Archive


def check_archive_projects(archive: Archive):
    from .tasks import check_archive_upload_task, create_tar_files_task

    # Get all projects linked to this archive
    all_project_combos = list(archive.linked_projects.values_list(
        "deployments__combo_project", flat=True).distinct())
    all_tasks = []
    for project_combo in all_project_combos:
        print(f"Check {project_combo} for archiving")
        all_file_objs = DataFile.objects.filter(
            deployment__combo_project=project_combo, tar_file__isnull=True)

        if not all_file_objs.exists():
            print(f"Check {project_combo} for archiving: No files")
            continue

        device_types = list(all_file_objs.values_list(
            "deployment__device__type", flat=True).distinct())
        for device_type in device_types:
            print(f"Check {project_combo} for archiving: check {device_type}")
            # Get datafiles for this project, sensor type
            file_objs = all_file_objs.filter(
                deployment__device__type=device_type)
            if not file_objs.exists():
                print(
                    f"Check {project_combo} for archiving: check {device_type}: No files")
                continue

            # check files for archiving
            total_file_size = file_objs.file_size("GB")
            if total_file_size > settings.MIN_ARCHIVE_SIZE_GB:
                print(
                    f"Check {project_combo} for archiving: check {device_type}: Sufficient files")
                file_pks = list(file_objs.values_list('pk', flat=True))
                tar_task = create_tar_files_task.si(file_pks, archive.pk)
                all_tasks.append(tar_task)
            else:
                print(
                    f"Check {project_combo} for archiving: check {device_type}: Insufficient files")

    if len(all_tasks) > 0:
        print("Submitting archiving jobs")
        task_group = group(all_tasks)
        task_chord = chord(
            task_group, check_archive_upload_task.si(archive.pk))
        task_chord.apply_async()


def check_archive_upload(archive: Archive):
    tars_to_upload = archive.tar_files.filter(archived=False, uploading=False)

    archive_ssh = archive.init_ssh_client()
    connect_ftp_success = archive_ssh.connect_to_ftp()
    connect_scp_success = archive_ssh.connect_to_scp()
    if not connect_scp_success or not connect_ftp_success:
        return

    for tar_obj in tars_to_upload:

        if tar_obj.uploading or tar_obj.archived:
            continue
        print(f"{tar_obj.name} uploading")
        tar_obj.uploading = True
        tar_obj.save()

        tar_full_name = tar_obj.name+".tar.gz"

        upload_path = os.path.join(archive.root_folder,
                                   os.path.relpath(tar_obj.path,
                                                   os.path.join(settings.FILE_STORAGE_ROOT,
                                                                "archiving")))

        full_tar_upload_path = os.path.join(
            upload_path, tar_full_name)

        full_tar_local_path = os.path.join(
            settings.FILE_STORAGE_ROOT, tar_obj.path, tar_full_name)
        success = False
        try:
            archive_ssh.mkdir_p(upload_path)

            archive_ssh.scp_c.put(full_tar_local_path,
                                  full_tar_upload_path,
                                  preserve_times=True)
            success = True
        except SCPException as e:
            print("SCP error:")
            print(repr(e))
            traceback.print_exc()

        except Exception as e:
            print(repr(e))
            traceback.print_exc()

        tar_obj.uploading = False
        if success:
            print(f"{tar_obj.name} uploading succesful")
            tar_obj.clean_tar()
            tar_obj.archived = True
            tar_obj.path = upload_path
            tar_obj.files.update(archived=True)

        else:
            print(f"{tar_obj.name} uploading failed")
        tar_obj.save()

        archive_ssh.close_connection()
