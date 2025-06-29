import logging
import os
from glob import glob

from archiving.models import Archive, TarFile
from celery import shared_task
from data_models.models import DataFile, DataType
from django.conf import settings
from django.db.models import F, Q, Value
from django.db.models.functions import Concat
from observation_editor.models import Observation
from user_management.models import User
from utils.general import try_remove_file_clean_dirs

from sensor_portal.celery import app

logger = logging.getLogger(__name__)


@app.task()
def check_all_paths():
    """
    Task to check all paths in the file system against DataFile records.
    This will log any discrepancies and attempt to fix them.
    """
    root_folder = settings.FILE_STORAGE_ROOT
    all_data_types = DataType.objects.all().values_list('name', flat=True)
    logger.info(f"Checking paths in {root_folder}")
    for data_type in all_data_types:
        check_paths(os.path.join(root_folder, data_type))


@app.task()
def check_paths(root_folder):

    if not os.path.exists(root_folder):
        logger.error(f"{root_folder} not found")
        return

    logger.info(f"Starting file walk in {root_folder}")
    for dirpath, _, filenames in os.walk(root_folder):
        logger.info(dirpath)
        for filename in filenames:
            filename = filename.replace("_THUMB", "")
            filename = filename.replace("_ANIM", "")
            filename = filename.replace("_CONCAT", "")

            logger.info(f"Found file: {filename}")
            try:
                data_file = DataFile.objects.get(
                    local_storage=True, file_name=os.path.splitext(filename)[0])

                logger.info(
                    f"Matched DataFile {data_file.file_name} - {filename}")

                if data_file.full_path() != os.path.join(dirpath, filename):
                    logger.info(
                        f"Updating DataFile {data_file.file_name} path from {data_file.full_path()} to {os.path.join(dirpath, filename)}")
                    data_file.local_path = settings.FILE_STORAGE_ROOT
                    data_file.path = os.path.relpath(
                        dirpath, settings.FILE_STORAGE_ROOT)
                    data_file.set_file_url()
                    data_file.save()

            except DataFile.DoesNotExist:
                logger.error(
                    f"No matching local DataFile found for: {filename}")
                try_remove_file_clean_dirs(os.path.join(dirpath, filename))
            except Exception:
                pass


@app.task()
def check_file_path(file_pks):
    logger.info("Starting fix_file_storage task...")
    file_objs = DataFile.objects.filter(local_storage=True, pk__in=file_pks)

    batch_size = 2000
    total_obs = file_objs.count()
    logger.info(f"Total files to process: {total_obs}")
    for start in range(0, total_obs, batch_size):
        logger.info(
            f"Processing batch {start // batch_size + 1} of {((total_obs - 1) // batch_size) + 1}")
        objs_to_update = []
        batch = file_objs[start:start + batch_size]
        for file_obj in batch.iterator():
            file_exists = os.path.exists(file_obj.full_path())
            if not file_exists:
                logger.info(f"Updating file ID {file_obj.id}")
                # Use glob to recursively search for the file
                search_path = os.path.join(
                    settings.FILE_STORAGE_ROOT, '**', (file_obj.file_name+file_obj.file_format))
                matching_files = glob(search_path, recursive=True)

                if matching_files:
                    # Update the file path if a match is found
                    file_obj.local_path = settings.FILE_STORAGE_ROOT
                    file_obj.path = os.path.relpath(
                        os.path.split(matching_files[0])[0], settings.FILE_STORAGE_ROOT)
                    file_obj.set_file_url()
                    objs_to_update.append(file_obj)
                else:
                    file_obj.local_storage = False
                    file_obj.set_file_url()
                    objs_to_update.append(file_obj)

        logger.info("Update objects")
        DataFile.objects.bulk_update(
            objs_to_update, ["local_path", "path", "file_url", "local_storage"], 500)

    logger.info("Completed fix_file_storage task.")


@app.task()
def fix_file_storage():
    logger.info("Starting fix_file_storage task...")
    file_objs = DataFile.objects.filter(local_storage=True).exclude(
        local_path=settings.FILE_STORAGE_ROOT)

    batch_size = 2000
    total_obs = file_objs.count()
    logger.info(f"Total files to process: {total_obs}")
    for start in range(0, total_obs, batch_size):
        logger.info(
            f"Processing batch {start // batch_size + 1} of {((total_obs - 1) // batch_size) + 1}")
        objs_to_update = []
        batch = file_objs[start:start + batch_size]
        for file_obj in batch.iterator():
            logger.info(f"Updating file ID {file_obj.id}")
            first_part = file_obj.local_path.replace('/media/exportdir/', '')
            file_obj.local_path = settings.FILE_STORAGE_ROOT
            file_obj.path = os.path.join(first_part, file_obj.path)
            file_obj.set_file_url()
            objs_to_update.append(file_obj)
        logger.info("Update objects")
        DataFile.objects.bulk_update(
            objs_to_update, ["local_path", "path", "file_url"], 500)

    logger.info("Completed fix_file_storage task.")


@app.task()
def fix_tar_paths():
    old_path = "/nfs/archive04/uvaarise"
    surf_archive = Archive.objects.get(name="UVAARISE SURF data archive")
    all_tars = TarFile.objects.filter(path__contains=old_path)
    surf_archive_path = surf_archive.root_folder

    objs_to_update = []
    for tar_obj in all_tars:
        tar_obj.path = tar_obj.path.replace(old_path, surf_archive_path)
        tar_obj.archive = surf_archive
        objs_to_update.append(tar_obj)

    TarFile.objects.bulk_update(objs_to_update, ["path", "archive"])


@app.task()
def fix_obs():

    users = User.objects.all()
    users = users.annotate(full_name=Concat(
        F("first_name"), Value(" "), F("last_name")))
    validation_through_table = Observation.validation_of.through

    obs_to_modify = Observation.objects.filter(Q(extra_data__confidence__isnull=False) |
                                               Q(extra_data__Confidence__isnull=False) |
                                               Q(extra_data__accuracy__isnull=False) |
                                               Q(extra_data__bbox__isnull=False) |
                                               Q(extra_data__classifiedBy__isnull=False) |
                                               Q(extra_data__confirmationOf__isnull=False) |
                                               Q(extra_data__probability__isnull=False)
                                               )
    batch_size = 2000
    total_obs = obs_to_modify.count()
    for start in range(0, total_obs, batch_size):
        logger.info(
            f"Processing batch {start // batch_size + 1} of {((total_obs - 1) // batch_size) + 1}")

        objs_to_update = []
        through_rows_to_add = []
        batch = obs_to_modify[start:start + batch_size]
        for obs in batch.iterator():
            extra_data = obs.extra_data
            change = False
            new_through = False

            if (confidence := extra_data.get("confidence")) is not None or \
                (confidence := extra_data.get("Confidence")) is not None or \
                (confidence := extra_data.get("accuracy")) is not None or \
                    (confidence := extra_data.get("probability")) is not None:
                logger.info(f"Updating confidence for observation ID {obs.id}")
                obs.confidence = confidence
                [extra_data.pop(x) for x in [y for y in [
                    "probability", "confidence", "Confidence", "accuracy"] if y in extra_data.keys()]]
                change = True

            if (bbox := extra_data.get("bbox")) is not None:
                logger.info(
                    f"Updating bounding box for observation ID {obs.id}")
                obs.bounding_box = bbox
                extra_data.pop("bbox")
                change = True

            if (validation := extra_data.get("confirmationOf")) is not None:
                logger.info(
                    f"Updating validation_of for observation ID {obs.id}")
                try:
                    other_obs = Observation.objects.all().get(pk=validation)
                    new_validation = validation_through_table(
                        from_observation_id=obs.pk, to_observation_id=other_obs.pk)
                    through_rows_to_add.append(new_validation)
                    extra_data.pop("confirmationOf")
                    change = True
                    new_through = True
                except Exception as e:
                    logger.info(e)
                    pass

            if (annotated_by := extra_data.get("classifiedBy")) is not None:
                logger.info(f"Updating owner for observation ID {obs.id}")
                try:
                    user_matches = users.filter(full_name=annotated_by)
                    if user_matches.exists():
                        obs.owner = user_matches.first()
                        extra_data.pop("classifiedBy")
                        change = True
                except Exception as e:
                    logger.info(e)
                    pass

            if change:
                obs.extra_data = extra_data
                objs_to_update.append(obs)

        validation_through_table.objects.bulk_create(
            through_rows_to_add, 500)

        Observation.objects.bulk_update(
            objs_to_update, ["extra_data", "owner", "bounding_box", "confidence"], 500)
