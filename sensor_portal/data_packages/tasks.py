import logging
from datetime import datetime
from typing import Any, List
from uuid import uuid4

from archiving.tasks import get_files_from_archive_task
from celery import shared_task
from data_models.file_handling_functions import group_files_by_size
from data_models.job_handling_functions import register_job
from data_models.models import DataFile
from data_models.permissions import perms
from django.conf import settings
from user_management.models import User

from sensor_portal.celery import app

from .models import DataPackage

logger = logging.getLogger(__name__)


@app.task(name="create_data_package")
@register_job(
    "Create data package",
    "create_data_package",
    "datafile",
    False,
    default_args={"metadata_type": "0", "include_files": True},
)
def start_make_data_package_task(
    datafile_pks: List[int],
    user_pk: int,
    metadata_type: int = 0,
    include_files: bool = True
) -> None:
    """
    Task to create data packages from selected DataFile primary keys.

    Args:
        datafile_pks (List[int]): List of primary keys for DataFile objects.
        user_pk (int): Primary key for the User initiating the task.
        metadata_type (int, optional): Type of metadata to include in the package. Defaults to 0.
        include_files (bool, optional): Whether to include files in the package. Defaults to True.
    """
    file_objs = DataFile.objects.filter(pk__in=datafile_pks)
    user = User.objects.get(pk=user_pk)

    file_objs = perms['data_models.view_datafile'].filter(user, file_objs)

    min_date = file_objs.min_date()
    min_date_str = min_date.strftime("%Y%m%d")
    max_date = file_objs.max_date()
    max_date_str = max_date.strftime("%Y%m%d")
    creation_dt = datetime.now().strftime("%Y%m%d_%H%M%S")

    all_package_pks: List[int] = []

    # if files, Split file objs by size, create all bundles
    if include_files:
        file_splits = group_files_by_size(file_objs)

        for suffix, group in enumerate(file_splits):
            bundle_file_objs = file_objs.filter(pk__in=group.get('file_pks'))
            uuid = str(uuid4())

            bundle_name = "_".join([
                uuid, user.username,
                min_date_str, max_date_str, creation_dt, str(suffix)
            ])
            # Create bundle object
            new_file_bundle = DataPackage.objects.create(
                name=bundle_name, owner=user, metadata_type=metadata_type
            )

            new_file_bundle.data_files.set(bundle_file_objs)
            all_package_pks.append(new_file_bundle.pk)

        archived_files = file_objs.filter(local_storage=False, archived=True)
        if archived_files.exists() and (
            (not settings.ONLY_SUPER_UNARCHIVE) or
            (settings.ONLY_SUPER_UNARCHIVE and user.is_superuser)
        ):
            bundle_objs = DataPackage.objects.filter(pk__in=all_package_pks)
            bundle_objs.update(status=1)
            archive_callback = make_data_package_task.si(all_package_pks).on_error(
                fail_data_package_task.si(all_package_pks)
            )

            get_files_from_archive_task(datafile_pks, archive_callback)
            return
        else:
            make_data_package_task(all_package_pks)
            return

    else:
        uuid = str(uuid4())
        # Note: 'suffix' is not defined in this scope, consider using '0' or another value
        bundle_name = "_".join([
            uuid, user.username,
            min_date_str, max_date_str, creation_dt, "0"
        ])
        new_file_bundle = DataPackage.objects.create(
            name=bundle_name, data_files=file_objs, owner=user,
            metadata_type=metadata_type, include_files=False
        )
        all_package_pks.append(new_file_bundle.pk)
        # go straight to finish bundle job
        make_data_package_task(all_package_pks)
        return


@app.task()
def make_data_package_task(all_package_pks: List[int]) -> None:
    """
    Task to finalize DataPackage creation and trigger zipping.

    Args:
        all_package_pks (List[int]): List of DataPackage primary keys to process.
    """
    bundle_objs = DataPackage.objects.filter(pk__in=all_package_pks)
    bundle_objs.update(status=2)
    for bundle_obj in bundle_objs:
        bundle_obj.make_zip()


@app.task()
def fail_data_package_task(all_package_pks: List[int]) -> None:
    """
    Task to mark DataPackages as failed.

    Args:
        all_package_pks (List[int]): List of DataPackage primary keys to mark as failed.
    """
    bundle_objs = DataPackage.objects.filter(pk__in=all_package_pks)
    bundle_objs.update(status=4)
