
import os
from datetime import datetime
from posixpath import join as posixjoin

from data_models.file_handling_functions import group_files_by_size
from data_models.metadata_functions import metadata_json_from_files
from data_models.models import DataFile
from django.conf import settings
from django.db.models import QuerySet
from utils.general import call_with_output
from utils.ssh_client import SSH_client

from .bagit_functions import bag_info_from_files
from .models import Archive, TarFile


def create_tar_files(file_pks, archive_pk):
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


def create_tar_file_and_obj(file_objs, archive_obj, name_suffix=0):
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


def get_tar_splits(file_objs):
    file_splits = group_files_by_size(file_objs)

    too_small_split_pks = [
        x for y in file_splits if y["total_size_gb"] < settings.MIN_ARCHIVE_SIZE_GB for x in y['file_pks']]

    # Remove files whose TAR would not be large enough from the in progress tar
    too_small_file_objs = DataFile.objects.filter(pk__in=too_small_split_pks)
    n_removed_files = too_small_file_objs.update(tar_file=None)
    print(f"{n_removed_files} in too small a grouping")

    file_splits_ok = [
        x for x in file_splits if x["total_size_gb"] >= settings.MIN_ARCHIVE_SIZE_GB]
    return file_splits_ok


def get_tar_name(file_objs: QuerySet[DataFile], suffix=0):
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


def create_tar_file(file_objs, name_suffix=0):

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
    relative_paths = file_objs.relative_paths()

    metadata_dir_path = os.path.join(tar_path, tar_name)
    relative_metadata_dir_path = os.path.relpath(
        metadata_dir_path, settings.FILE_STORAGE_ROOT)

    print(f"{tar_name}: generating bagit data")
    # Generate bagit metadata
    all_metadata_paths = bag_info_from_files(file_objs, metadata_dir_path)

    # Generate metadata file

    metadata_json_path = metadata_json_from_files(file_objs, metadata_dir_path)

    all_metadata_paths.append(metadata_json_path)

    relative_metadata_paths = [os.path.relpath(
        x, settings.FILE_STORAGE_ROOT) for x in all_metadata_paths]

    # TAR files
    # Use transform command to generate data dir inside the TAR, move metadata files to root

    tar_command = ["tar", "zcvf", full_tar_path,
                   "--transform", f"s,^,data/,;s,data/{relative_metadata_dir_path}/,,",] + relative_paths + relative_metadata_paths
    success, output = call_with_output(tar_command, settings.FILE_STORAGE_ROOT)

    # regardless of status, we remove the metadata files
    [os.remove(x) for x in all_metadata_paths]
    os.removedirs(metadata_dir_path)

    if not success:
        print(f"{tar_name}: Error creating TAR")
        print(output)
        return False, tar_name, None
    print(f"{tar_name}: succesfully created")
    return True, tar_name, full_tar_path


def check_tar_status(ssh_client: SSH_client, tar_path: str) -> tuple[int, str]:
    status_code, stdout, stderr = ssh_client.send_ssh_command(
        f"dmls -l {posixjoin(tar_path)}")
    if status_code != 0:
        return status_code, None
    target_tar_status = stdout[0].split(" ")[-2]
    return status_code, target_tar_status
