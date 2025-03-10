import itertools
import os
from datetime import datetime as dt

from celery import chord
from data_handlers.base_data_handler_class import DataTypeHandlerCollection
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone as djtimezone
from rest_framework import status
from utils.general import convert_unit

from sensor_portal.celery import app

from .general_functions import check_dt


def create_file_objects(files, check_filename=False, recording_dt=None, extra_data=None, deployment_object=None,
                        device_object=None, data_types=None, request_user=None):
    from data_models.models import DataFile, DataType

    invalid_files = []
    existing_files = []
    uploaded_files = []
    if extra_data is None:
        extra_data = [{}]

    print(files)

    upload_dt = djtimezone.now()

    if check_filename:
        #  check if the original name already exists in the database
        filenames = [x.name for x in files]
        db_filenames = list(
            DataFile.objects.filter(original_name__in=filenames).values_list('original_name', flat=True))
        not_duplicated = [x not in db_filenames for x in filenames]
        files = [x for x, y in zip(files, not_duplicated) if y]
        existing_files += [{x: {"message": "Already in database", "status": 200}} for x,
                           y in zip(filenames, not_duplicated) if not y]
        if len(files) == 0:
            return (uploaded_files, invalid_files, existing_files, status.HTTP_200_OK)

        if len(recording_dt) > 1:
            recording_dt = [x for x, y in zip(
                recording_dt, not_duplicated) if y]
        if len(extra_data) > 1:
            extra_data = [x for x, y in zip(
                extra_data, not_duplicated) if y]
        if data_types is not None:
            if len(data_types) > 1:
                data_types = [x for x, y in zip(
                    data_types, not_duplicated) if y]

    if device_object is None and deployment_object:
        device_object = deployment_object.device

    tasks = None

    if device_object:
        device_model_object = device_object.model
        data_handlers = settings.DATA_HANDLERS

        data_handler = data_handlers.get_handler(
            device_model_object.type.name, device_model_object.name)

        if data_handler is not None:

            valid_files = data_handler.get_valid_files(files)

            if len(valid_files) == 0:
                # More informative errors at some point
                invalid_files += [{x.name: {"message": f"Invalid file type for {device_model_object.name}", "status": 400}}
                                  for x in files]
                return (uploaded_files, invalid_files, existing_files, status.HTTP_400_BAD_REQUEST)
            else:
                valid_files_bool = [x in valid_files for x in files]
                invalid_files += [{x.name: {"message": f"Invalid file type for {device_model_object.name}", "status": 400}}
                                  for x, y in zip(files, valid_files_bool) if not y]

                files = valid_files
                if recording_dt is not None and len(recording_dt) > 1:
                    recording_dt = [x for x, y in zip(
                        recording_dt, valid_files_bool) if y]
                if len(extra_data) > 1:
                    extra_data = [x for x, y in zip(
                        extra_data, valid_files_bool) if y]

            new_recording_dt = []
            new_extra_data = []
            new_data_types = []
            new_tasks = []

            for i in range(len(files)):
                if len(extra_data) > 1:
                    file_extra_data = extra_data[i]
                else:
                    file_extra_data = extra_data[0]

                if recording_dt is None:
                    file_recording_dt = recording_dt
                elif len(recording_dt) > 1:
                    file_recording_dt = recording_dt[i]
                else:
                    file_recording_dt = recording_dt[0]
                file = files[i]

                new_file_recording_dt, new_file_extra_data, new_file_data_type, new_file_task = data_handler.handle_file(file,
                                                                                                                         file_recording_dt,
                                                                                                                         file_extra_data,
                                                                                                                         device_model_object.type.name)
                new_recording_dt.append(new_file_recording_dt)
                new_extra_data.append(new_file_extra_data)
                new_data_types.append(new_file_data_type)
                new_tasks.append(new_file_task)

            recording_dt = new_recording_dt
            extra_data = new_extra_data
            data_types = new_data_types
            tasks = new_tasks

    else:
        invalid_files += [{x.name: {"message": "No linked device", "status": 400}}
                          for x in files]
        return (uploaded_files, invalid_files, existing_files, status.HTTP_400_BAD_REQUEST)

    if all([x is None for x in recording_dt]):
        invalid_files += [{x.name: {"message": "Unable to extract recording date time", "status": 400}}
                          for x in files]
        return (uploaded_files, invalid_files, existing_files, status.HTTP_400_BAD_REQUEST)

    if deployment_object:
        if request_user:
            if not request_user.has_perm('data_models.change_deployment', deployment_object):
                invalid_files += [
                    {x.name: {
                        "message": f"Not allowed to attach files to {deployment_object.deployment_device_ID}", "status": 403}}
                    for x in files]
                return (uploaded_files, invalid_files, existing_files, status.HTTP_403_FORBIDDEN)

        file_valid = deployment_object.check_dates(recording_dt)
        deployment_objects = [deployment_object]

    elif device_object:
        deployment_objects = [device_object.deployment_from_date(
            x) for x in recording_dt]
        file_valid = [x is not None for x in deployment_objects]
        # Filter deployments to only valids
        deployment_objects = [
            x for x in deployment_objects if x is not None]

    #  split off invalid  files
    invalid_files += [{x.name: {"message": f"no suitable deployment of {device_object} found for recording date time {z}"}, "status": 400} for x,
                      y, z in zip(files, file_valid, recording_dt) if not y]
    files = [x for x, y in zip(files, file_valid) if y]

    if len(files) == 0:
        return (uploaded_files, invalid_files, existing_files, status.HTTP_400_BAD_REQUEST)

    if len(recording_dt) > 1:
        recording_dt = [x for x, y in zip(
            recording_dt, file_valid) if y]
    if len(extra_data) > 1:
        extra_data = [x for x, y in zip(extra_data, file_valid) if y]
    if data_types is not None:
        if len(data_types) > 1:
            data_types = [x for x, y in zip(
                data_types, file_valid) if y]

    all_new_objects = []
    for i in range(len(files)):
        file = files[i]
        filename = file.name
        if len(deployment_objects) > 1:
            file_deployment = deployment_objects[i]
        else:
            file_deployment = deployment_objects[0]

        if request_user:
            if not request_user.has_perm('data_models.change_deployment', file_deployment):
                invalid_files.append(
                    {filename: {"message": f"Not allowed to attach files to {file_deployment.deployment_device_ID}", "status": 403}})

                continue

        if len(recording_dt) > 1:
            file_recording_dt = recording_dt[i]
        else:
            file_recording_dt = recording_dt[0]

        # localise recording_dt to deployment tz or server tz
        file_recording_dt = check_dt(
            file_recording_dt, file_deployment.time_zone)

        if len(extra_data) > 1:
            file_extra_data = extra_data[i]
        else:
            file_extra_data = extra_data[0]

        if data_types is None:
            file_data_type = file_deployment.device_type
        else:
            if len(data_types) > 1:
                file_data_type, created = DataType.objects.get_or_create(
                    name=data_types[i])
            else:
                file_data_type, created = DataType.objects.get_or_create(
                    name=data_types[0])

        file_local_path = os.path.join(
            settings.FILE_STORAGE_ROOT)
        file_path = os.path.join(file_data_type.name,
                                 file_deployment.deployment_device_ID, str(upload_dt.date()))

        file_extension = os.path.splitext(filename)[1]
        new_file_name = get_new_name(file_deployment,
                                     file_recording_dt,
                                     file_local_path,
                                     file_path
                                     )

        file_size = file.size

        file_fullpath = os.path.join(
            file_local_path, file_path, f"{new_file_name}{file_extension}")

        new_datafile_obj = DataFile(
            deployment=file_deployment,
            file_type=file_data_type,
            file_name=new_file_name,
            original_name=filename,
            file_format=file_extension,
            upload_dt=upload_dt,
            recording_dt=file_recording_dt,
            path=file_path,
            local_path=file_local_path,
            file_size=file_size,
            extra_data=file_extra_data
        )
        try:
            new_datafile_obj.full_clean()
        except ValidationError as e:
            invalid_files.append(
                {filename: {"message": f"Error creating database records {repr(e)}", "status": 400}})
            continue
        except Exception as e:
            invalid_files.append(
                {filename: {"message": repr(e), "status": 400}})
            continue

        try:
            handle_uploaded_file(file, file_fullpath)
        except Exception as e:
            invalid_files.append(
                {filename: {"message": repr(e), "status": 400}})
            continue

        new_datafile_obj.set_file_url()
        all_new_objects.append(new_datafile_obj)

    final_status = status.HTTP_201_CREATED
    if len(all_new_objects) > 0:
        uploaded_files = DataFile.objects.bulk_create(all_new_objects, update_conflicts=True, update_fields=[
            "extra_data"], unique_fields=["file_name"])

        if tasks is not None:
            # For unique tasks, fire off jobs to perform them
            unique_tasks = list(set(tasks))
            for task_name in unique_tasks:
                # get filenames for this task
                task_file_names = [x.file_name for x,
                                   y in zip(uploaded_files, tasks) if y == task_name]

                new_task = app.signature(
                    task_name, [task_file_names], immutable=True)
                new_task.apply_async()

    else:
        final_status = status.HTTP_400_BAD_REQUEST
        if all([[y[x].get('status') == 403 for x in y.keys()][0] for y in invalid_files]):
            final_status = status.HTTP_403_FORBIDDEN
    return (uploaded_files, invalid_files, existing_files, final_status)


def handle_uploaded_file(file, filepath, multipart=False):
    os.makedirs(os.path.split(filepath)[0], exist_ok=True)
    if multipart and os.path.exists(filepath):
        print("append to file")
        with open(filepath, 'ab+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)
    else:
        with open(filepath, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)


def clear_uploaded_file(filepath):
    try:
        os.remove(filepath)
    except OSError:
        pass


def get_new_name(deployment, recording_dt, file_local_path, file_path, file_n=None):
    if file_n is None:
        file_n = get_n_files(os.path.join(file_local_path, file_path)) + 1
    newname = f"{deployment.deployment_device_ID}_{dt.strftime(recording_dt, '%Y-%m-%d_%H-%M-%S')}_({file_n})"
    return newname


def get_n_files(dir_path):
    if os.path.exists(dir_path):
        all_files = os.listdir(dir_path)
        # only with extension
        all_files = [x for x in all_files if '.' in x]
        n_files = len(all_files)
    else:
        n_files = 0
    return n_files


def group_files_by_size(file_objs,
                        max_size=settings.MAX_ARCHIVE_SIZE_GB):

    curr_key = 0
    curr_total = 0
    file_info = []

    file_objs = file_objs.order_by('recording_dt')

    file_values = file_objs.values('pk', 'file_size')
    for file_value in file_values:
        file_size = convert_unit(file_value['file_size'], "GB")

        if (curr_total+file_size) > max_size:
            # If the new file would push over the max size, start a new split
            curr_total = file_size
            curr_key += 1
        else:
            curr_total += file_size

        file_info.append(
            {"pk": file_value['pk'], "file_size": file_size, "key": curr_key})

    groups = []

    for k, g in itertools.groupby(file_info, lambda x: x.get("key")):
        files = list(g)

        total_size_gb = sum([x.get('file_size') for x in files])
        file_pks = [x.get('pk') for x in files]
        # Store group iterator as a list
        groups.append({"file_pks": file_pks, "total_size_gb": total_size_gb})

    return groups
