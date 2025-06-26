import itertools
import logging
import os
from datetime import datetime as dt
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple, Union

from celery import chain
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile
from django.db.models import QuerySet
from django.utils import timezone as djtimezone
from rest_framework import status
from utils.general import convert_unit, get_md5

from sensor_portal.celery import app

from .general_functions import check_dt

logger = logging.getLogger(__name__)

# To avoid ciruclar imports
if TYPE_CHECKING:
    from data_models.models import DataFile, Deployment, Device
    from user_management.models import User


def create_file_objects(
    files: List[Union[object, UploadedFile]],
    check_filename: bool = False,
    recording_dt: Optional[List[Optional[dt]]] = None,
    extra_data: Optional[List[Dict[str,
                                   Union[str, int, float, bool, None]]]] = None,
    deployment_object: Optional["Deployment"] = None,
    device_object: Optional["Device"] = None,
    data_types: Optional[List[str]] = None,
    request_user: Optional["User"] = None,
    multipart: bool = False,
    verbose: bool = False
) -> Tuple[
    List["DataFile"],
    List[Dict[str, Dict[str, Union[str, int]]]],
    List[Dict[str, Dict[str, Union[str, int]]]],
    int
]:
    """
    Create file objects, handle uploads, validations, and database record creation.

    Args:
        files (List[Union[object, UploadedFile]]): List of file objects to process.
        check_filename (bool, optional): If True, check for duplicate filenames in the database. Defaults to False.
        recording_dt (Optional[List[Optional[datetime]]], optional): List of recording datetimes for the files. Defaults to None.
        extra_data (Optional[List[Dict[str, Union[str, int, float, bool, None]]]], optional): List of additional metadata for the files. Defaults to None.
        deployment_object (Optional[Deployment], optional): Deployment object associated with the files. Defaults to None.
        device_object (Optional[Device], optional): Device object associated with the files. Defaults to None.
        data_types (Optional[List[str]], optional): List of data types for the files. Defaults to None.
        request_user (Optional[User], optional): User object for permission checks. Defaults to None.
        multipart (bool, optional): If True, handle multipart file uploads. Defaults to False.
        verbose (bool, optional): If True, enable verbose logging. Defaults to False.

    Returns:
        Tuple[
            List[DataFile],  # Successfully uploaded file objects
            List[Dict[str, Dict[str, Union[str, int]]]],  # Invalid files with errors
            List[Dict[str, Dict[str, Union[str, int]]]],  # Files already in DB
            int  # HTTP status code
        ]

    Raises:
        ValidationError: If there is an error validating the database records.
        Exception: For any other errors during file handling or database operations.

    Notes:
        - Handles duplicate filename checks and multipart uploads.
        - Validates file types based on the device model.
        - Checks permissions for attaching files to deployments.
        - Filters files based on recording datetime and deployment validity.
        - Creates database records and saves valid files.
        - Supports automated tasks and checksum validation.
    """

    from data_models.models import DataFile, DataType, ProjectJob

    invalid_files = []
    existing_files = []
    uploaded_files = []
    if extra_data is None:
        extra_data = [{}]

    if verbose:
        logger.info("Initial files:", files)
        logger.info("Device object:", device_object)
        logger.info("Deployment object:", deployment_object)
        logger.info("Recording datetime:", recording_dt)
        logger.info("Extra data:", extra_data)
        logger.info("Data types:", data_types)
        logger.info("Request user:", request_user)

    # Get the current upload datetime
    upload_dt = djtimezone.now()

    # Check for duplicate filenames or handle multipart uploads
    if check_filename or multipart:
        if verbose:
            logger.info("Checking filenames or handling multipart upload...")

        # Extract filenames from the provided file objects
        filenames = [x.name for x in files]

        if multipart:
            if verbose:
                logger.info("Handling multipart upload...")

            # Ensure only one file chunk is provided for multipart uploads
            if len(filenames) > 1:
                invalid_files += [{x: {"message": "Multipart file upload expects a single file chunk", "status": 400}} for x,
                                  in filenames]
                return (uploaded_files, invalid_files, existing_files, status.HTTP_400_BAD_REQUEST)

            # Initialize multipart-related variables
            multipart_obj = None
            multipart_checksum = None

            # Query the database for existing multipart files with matching filenames
            existing_multipart_files = DataFile.objects.filter(
                original_name__in=filenames, extra_data__md5_checksum__isnull=True)
            if device_object:
                # Filter by device if a device object is provided
                existing_multipart_files = existing_multipart_files.filter(
                    deployment__device=device_object)

            if deployment_object:
                # Filter by deployment if a deployment object is provided
                existing_multipart_files = existing_multipart_files.filter(
                    deployment=deployment_object)

            if existing_multipart_files.exists():
                if verbose:
                    logger.info(
                        "Found existing multipart object in the database.")

                # Retrieve the first matching multipart object
                multipart_obj = existing_multipart_files.first()

                # Update recording datetime, deployment, and device based on the multipart object
                recording_dt = [multipart_obj.recording_dt]
                deployment_object = multipart_obj.deployment
                device_object = deployment_object.device

                # Extract checksum from extra data
                multipart_checksum = extra_data[0].get("md5_checksum")

        else:
            if verbose:
                logger.info(
                    "Checking for duplicate filenames in the database...")

            # Query the database for filenames that already exist
            db_filenames = list(
                DataFile.objects.filter(original_name__in=filenames).values_list('original_name', flat=True))

            # Identify files that are not duplicated
            not_duplicated = [x not in db_filenames for x in filenames]
            files = [x for x, y in zip(files, not_duplicated) if y]
            existing_files += [{x: {"message": "Already in database", "status": 200}} for x,
                               y in zip(filenames, not_duplicated) if not y]

            # If all files are duplicates, return early with a success status
            if len(files) == 0:
                if verbose:
                    logger.info("All files are already in the database.")
                return (uploaded_files, invalid_files, existing_files, status.HTTP_200_OK)

        # Filter recording datetime values based on non-duplicated files
        if recording_dt and len(recording_dt) > 1:
            recording_dt = [x for x, y in zip(
                recording_dt, not_duplicated) if y]
        # Filter extra data based on non-duplicated files
        if len(extra_data) > 1:
            extra_data = [x for x, y in zip(
                extra_data, not_duplicated) if y]
        # Filter data types based on non-duplicated files
        if data_types is not None:
            if len(data_types) > 1:
                data_types = [x for x, y in zip(
                    data_types, not_duplicated) if y]

    # If no device_object is provided but a deployment_object exists, set the device_object from the deployment_object
    if device_object is None and deployment_object:
        if verbose:
            logger.info("Setting device_object from deployment_object...")
        device_object = deployment_object.device

    # Initialize handler_tasks to None
    handler_tasks = None

    # If a device_object is available, process the files using the associated device model
    if device_object:
        if verbose:
            logger.info("Processing files with device_object...")

        # Retrieve the device model object and data handlers from settings
        device_model_object = device_object.model
        data_handlers = settings.DATA_HANDLERS

        # Get the appropriate data handler for the device model type and name
        data_handler = data_handlers.get_handler(
            device_model_object.type.name, device_model_object.name)

        # If a data handler is found, validate and process the files
        if data_handler is not None:
            if verbose:
                logger.info(
                    f"Using data handler for {device_model_object.name}...")

            # Validate the files using the data handler
            valid_files = data_handler.get_valid_files(files)

            # If no valid files are found, return an error response
            if len(valid_files) == 0:
                if verbose:
                    logger.info("No valid files found for the device model.")
                invalid_files += [{x.name: {"message": f"Invalid file type for {device_model_object.name}", "status": 400}}
                                  for x in files]
                return (uploaded_files, invalid_files, existing_files, status.HTTP_400_BAD_REQUEST)
            else:
                # Identify invalid files and update the invalid_files list
                valid_files_bool = [x in valid_files for x in files]
                invalid_files += [{x.name: {"message": f"Invalid file type for {device_model_object.name}", "status": 400}}
                                  for x, y in zip(files, valid_files_bool) if not y]

                # Filter out invalid files from the files list
                files = valid_files

                # Update recording_dt, extra_data, and other metadata based on valid files
                if recording_dt is not None and len(recording_dt) > 1:
                    recording_dt = [x for x, y in zip(
                        recording_dt, valid_files_bool) if y]
                if extra_data and len(extra_data) > 1:
                    extra_data = [x for x, y in zip(
                        extra_data, valid_files_bool) if y]

            # Initialize lists to store updated metadata for valid files
            new_recording_dt = []
            new_extra_data = []
            new_data_types = []
            new_tasks = []

            # Process each valid file using the data handler
            for i in range(len(files)):
                # Retrieve extra_data for the current file
                if len(extra_data) > 1:
                    file_extra_data = extra_data[i]
                else:
                    file_extra_data = extra_data[0]

                # Retrieve recording_dt for the current file
                if recording_dt is None:
                    file_recording_dt = recording_dt
                elif len(recording_dt) > 1:
                    file_recording_dt = recording_dt[i]
                else:
                    file_recording_dt = recording_dt[0]

                file = files[i]

                if verbose:
                    logger.info(
                        f"Handling file {file.name} with data handler...")

                # Use the data handler to process the file and extract updated metadata
                new_file_recording_dt, new_file_extra_data, new_file_data_type, new_file_task = \
                    data_handler.handle_file(
                        file,
                        file_recording_dt,
                        file_extra_data,
                        device_model_object.type.name
                    )

                # Append the updated metadata to the respective lists
                new_recording_dt.append(new_file_recording_dt)
                new_extra_data.append(new_file_extra_data)
                new_data_types.append(new_file_data_type)
                new_tasks.append(new_file_task)

            # Update recording_dt, extra_data, data_types, and handler_tasks with the processed values
            recording_dt = new_recording_dt
            extra_data = new_extra_data
            data_types = new_data_types
            handler_tasks = new_tasks

    else:
        # If no device_object is linked to the files, return an error response
        if verbose:
            logger.info("No linked device found for the files.")
        invalid_files += [{x.name: {"message": "No linked device", "status": 400}}
                          for x in files]
        return (uploaded_files, invalid_files, existing_files, status.HTTP_400_BAD_REQUEST)

    # Check if all recording dates are None, indicating an inability to extract recording date times
    if all([x is None for x in recording_dt]):
        # Add these files to the invalid_files list with an appropriate error message
        invalid_files += [{x.name: {"message": "Unable to extract recording date time", "status": 400}}
                          for x in files]
        # Return early with an HTTP 400 Bad Request status
        return (uploaded_files, invalid_files, existing_files, status.HTTP_400_BAD_REQUEST)

    # If a deployment object is provided, validate permissions and recording dates
    if deployment_object:
        if verbose:
            logger.info("Checking permissions for deployment_object...")
        if request_user:
            # Check if the user has permission to attach files to the deployment object
            if not request_user.has_perm('data_models.change_deployment', deployment_object):
                if verbose:
                    logger.info(
                        f"User does not have permission to attach files to {deployment_object.deployment_device_ID}.")
                # Add these files to the invalid_files list with a permission error message
                invalid_files += [
                    {x.name: {
                        "message": f"Not allowed to attach files to {deployment_object.deployment_device_ID}",
                        "status": 403}}
                    for x in files]
                # Return early with an HTTP 403 Forbidden status
                return (uploaded_files, invalid_files, existing_files, status.HTTP_403_FORBIDDEN)

        if verbose:
            logger.info("Validating recording dates for deployment_object...")
        # Validate the recording dates against the deployment object
        file_valid = deployment_object.check_dates(recording_dt)
        # Set deployment_objects to a list containing the deployment_object
        deployment_objects = [deployment_object]

    # If no deployment object is provided, determine deployments from the device object and recording dates
    elif device_object:
        if verbose:
            logger.info(
                "Determining deployments from device_object and recording dates...")
        # Use the device object to find deployments based on recording dates
        deployment_objects = [device_object.deployment_from_date(
            x) for x in recording_dt]
        # Check which deployments are valid (not None)
        file_valid = [x is not None for x in deployment_objects]
        # Filter out None values from deployment_objects
        deployment_objects = [
            x for x in deployment_objects if x is not None]

    if verbose:
        logger.info(
            "Filtering invalid files based on deployment and recording dates...")
    # Add invalid files to the invalid_files list with appropriate error messages
    if deployment_object:
        invalid_files += [{x.name:
                           {"message": f"Recording date time {z} does not exist in {deployment_object}",
                            "status": 400}} for x,
                          y, z in zip(files, file_valid, recording_dt) if not y]
    else:
        invalid_files += [{x.name:
                           {"message": f"no suitable deployment of {device_object} found for recording date time {z}",
                            "status": 400}} for x,
                          y, z in zip(files, file_valid, recording_dt) if not y]

    # Filter out invalid files from the files list
    files = [x for x, y in zip(files, file_valid) if y]

    # If no valid files remain after filtering, return an error response
    if len(files) == 0:
        if verbose:
            logger.info("No valid files remain after filtering.")
        return (uploaded_files, invalid_files, existing_files, status.HTTP_400_BAD_REQUEST)

    # Filter recording datetime values based on valid files
    if len(recording_dt) > 1:
        recording_dt = [x for x, y in zip(recording_dt, file_valid) if y]
    # Filter extra data based on valid files
    if len(extra_data) > 1:
        extra_data = [x for x, y in zip(extra_data, file_valid) if y]
    # Filter data types based on valid files
    if data_types is not None:
        if len(data_types) > 1:
            data_types = [x for x, y in zip(data_types, file_valid) if y]

    # Initialize lists to store project task primary keys, new DataFile objects, and handler tasks
    project_task_pks = []
    all_new_objects = []
    all_handler_tasks = []

    # Process each valid file
    for i in range(len(files)):
        file = files[i]
        filename = file.name

        # Determine the deployment object for the current file
        if len(deployment_objects) > 1:
            file_deployment = deployment_objects[i]
        else:
            file_deployment = deployment_objects[0]

        if verbose:
            logger.info(
                f"Processing file: {filename} for deployment: {file_deployment.deployment_device_ID}")

        # Check if the user has permission to attach the file to the deployment
        if request_user:
            if not request_user.has_perm('data_models.change_deployment', file_deployment):
                if verbose:
                    logger.info(
                        f"User does not have permission to attach file {filename} to {file_deployment.deployment_device_ID}.")
                invalid_files.append(
                    {filename: {"message": f"Not allowed to attach files to {file_deployment.deployment_device_ID}", "status": 403}})
                continue

        # Determine the recording datetime for the current file
        if len(recording_dt) > 1:
            file_recording_dt = recording_dt[i]
        else:
            file_recording_dt = recording_dt[0]

        # Retrieve the handler task for the current file, if available
        if handler_tasks is not None:
            file_handler_task = handler_tasks[i]
        else:
            file_handler_task = None

        if verbose:
            logger.info(
                f"Localizing recording date time for file: {filename}...")
        # Localize the recording datetime based on the deployment's timezone
        file_recording_dt = check_dt(
            file_recording_dt, file_deployment.time_zone)

        # Retrieve extra data for the current file
        if len(extra_data) > 1:
            file_extra_data = extra_data[i]
        else:
            file_extra_data = extra_data[0]

        # Determine the data type for the current file
        if data_types is None:
            file_data_type = file_deployment.device_type
        else:
            if len(data_types) > 1:
                file_data_type, created = DataType.objects.get_or_create(
                    name=data_types[i])
            else:
                file_data_type, created = DataType.objects.get_or_create(
                    name=data_types[0])

        if verbose:
            logger.info(f"Setting local path for file: {filename}...")
        # Set the local path for the file based on the storage root
        file_local_path = os.path.join(settings.FILE_STORAGE_ROOT)

        # Check if the file is not part of a multipart upload or if it's a new multipart object
        if not multipart or (multipart and multipart_obj is None):

            # Log the process of setting the path for the file
            if verbose:
                logger.info(f"Setting path for file: {filename}...")

            # Construct the file path using the data type name, deployment device ID, and upload date
            file_path = os.path.join(file_data_type.name,
                                     file_deployment.deployment_device_ID, str(upload_dt.date()))

            # Extract the file extension from the original filename
            file_extension = os.path.splitext(filename)[1]

            # Generate a new unique name for the file based on deployment, recording datetime, and file count
            new_file_name = get_new_name(file_deployment,
                                         file_recording_dt,
                                         file_local_path,
                                         file_path
                                         )

            # Get the size of the file
            file_size = file.size

            # Construct the full path where the file will be stored locally
            file_fullpath = os.path.join(
                file_local_path, file_path, f"{new_file_name}{file_extension}")

            # Log the creation of the database object for the file
            if verbose:
                logger.info(f"Creating database object for: {filename}...")

            # If the file is part of a multipart upload, mark it as incomplete in the extra data
            if multipart:
                file_extra_data["multipart_complete"] = False

            # Create a new DataFile object with all the relevant metadata
            new_datafile_obj = DataFile(
                deployment=file_deployment,  # Associated deployment
                file_type=file_data_type,  # Type of the file
                file_name=new_file_name,  # Generated unique name for the file
                original_name=filename,  # Original name of the file
                file_format=file_extension,  # File extension
                upload_dt=upload_dt,  # Upload datetime
                recording_dt=file_recording_dt,  # Recording datetime
                path=file_path,  # Relative path for the file
                local_path=file_local_path,  # Local storage path
                file_size=file_size,  # Size of the file
                extra_data=file_extra_data  # Additional metadata
            )
            try:
                # Validate the new DataFile object to ensure all fields meet the model's constraints
                new_datafile_obj.full_clean()
            except ValidationError as e:
                # Handle validation errors specific to the DataFile model
                if verbose:
                    logger.info(
                        f"Error creating database objects for: {filename}...")
                # Add the file to the invalid_files list with a detailed error message
                invalid_files.append(
                    {filename: {"message": f"Error creating database records {repr(e)}", "status": 400}})
                # Skip further processing for this file
                continue
            except Exception as e:
                # Handle any other unexpected exceptions during validation
                invalid_files.append(
                    {filename: {"message": repr(e), "status": 400}})
                # Skip further processing for this file
                continue

        else:
            # Retrieve the full path for the multipart object
            file_fullpath = multipart_obj.full_path()

        try:
            if verbose:
                logger.info(f"Saving file to path: {file_fullpath}...")
            # Try to save the file
            handle_uploaded_file(file, file_fullpath, multipart, verbose)
        except Exception as e:
            if verbose:
                logger.info(
                    f"Error handling uploaded file for: {filename} - {repr(e)}")
            invalid_files.append(
                {filename: {"message": repr(e), "status": 400}})
            if multipart:
                # This is a complete failure when multipart
                return (uploaded_files, invalid_files, existing_files, status.HTTP_400_BAD_REQUEST)

            continue

        if not multipart or (multipart and multipart_obj is None):
            # Set the file URL when first registered in the database
            if verbose:
                logger.info(f"Setting file URL for: {filename}...")
            new_datafile_obj.set_file_url()
            all_new_objects.append(new_datafile_obj)

        # If a single file or a completing (checksum received) multipart
        if not multipart or (multipart and multipart_checksum is not None):
            # Flag to append tasks for processing
            append_tasks = True

            if multipart:
                # Perform MD5 checksum validation for multipart file uploads
                if verbose:
                    logger.info(
                        f"Performing MD5 checksum validation for multipart file: {multipart_obj.original_name}...")
                # Calculate the server-side checksum of the uploaded file
                server_checksum = get_md5(multipart_obj.full_path())
                if verbose:
                    logger.info(
                        f"Server checksum: {server_checksum}, Client checksum: {multipart_checksum}")
                # Compare the server checksum with the client-provided checksum
                if not multipart_checksum == server_checksum:
                    # If the checksums do not match, log the mismatch and add an error to invalid_files
                    if verbose:
                        logger.info(
                            f"Checksum mismatch for multipart file: {multipart_obj.original_name}")
                    invalid_files += [{multipart_obj.original_name: {
                        "message": "Multipart file upload checksum mismatch", "status": 400}}]
                    # Return early with an HTTP 400 Bad Request status
                    return (uploaded_files, invalid_files, existing_files, status.HTTP_400_BAD_REQUEST)
                else:
                    # If the checksums match, log the success and update the multipart file metadata
                    if verbose:
                        logger.info(
                            f"Checksum validation passed for multipart file: {multipart_obj.original_name}")
                    # Update the extra_data field with the validated checksum
                    multipart_extra_data = multipart_obj.extra_data
                    multipart_extra_data['md5_checksum'] = server_checksum
                    # Remove the multipart_complete flag from the metadata
                    multipart_extra_data.pop("multipart_complete")
                    # Save the updated metadata to the database
                    multipart_obj.extra_data = multipart_extra_data
                    multipart_obj.save()

        else:
            # Do not perform post upload tasks
            append_tasks = False

        # If post upload tasks are to be performed
        if append_tasks:
            # Fetch deployment tasks associated with the current file's deployment
            if verbose:
                logger.info(
                    f"Fetching deployment tasks for file: {filename}...")
            file_deployment_tasks = list(file_deployment.project.all().values_list(
                'automated_tasks__pk', flat=True))  # Retrieve primary keys of automated tasks linked to the deployment
            file_deployment_tasks = [
                x for x in file_deployment_tasks if x is not None]  # Filter out None values from the task list
            if verbose:
                logger.info(
                    f"Deployment tasks for file {filename}: {file_deployment_tasks}")

            # Append the handler task for the current file to the list of all handler tasks
            all_handler_tasks.append(file_handler_task)
            if verbose:
                logger.info(
                    f"Handler task for file {filename}: {file_handler_task}")

            # Append the deployment tasks for the current file to the list of project task primary keys
            project_task_pks.append(file_deployment_tasks)

    final_status = status.HTTP_200_OK

    if len(all_new_objects) > 0 or multipart:
        # If new objects are to be created
        if len(all_new_objects) > 0:
            if verbose:
                logger.info(
                    f"Bulk creating {len(all_new_objects)} new DataFile objects...")
            uploaded_files = DataFile.objects.bulk_create(all_new_objects)
            uploaded_files_pks = [x.pk for x in uploaded_files]
            if verbose:
                logger.info(
                    f"Created DataFile objects with primary keys: {uploaded_files_pks}")
            final_status = status.HTTP_201_CREATED
        # Otherwise if this part of a multipart upload
        elif multipart:
            if verbose:
                logger.info(
                    f"Using existing multipart object with primary key: {multipart_obj.pk}")
            uploaded_files = [multipart_obj]
            uploaded_files_pks = [multipart_obj.pk]
            # Is multipart completing
            if multipart_checksum is not None:
                # Multipart done
                final_status = status.HTTP_200_OK
            else:
                # Multipart continues
                final_status = status.HTTP_100_CONTINUE

        # Get all tasks
        all_tasks = []

        # For unique data handler tasks, fire off jobs to perform them
        unique_tasks = list(
            set([x for x in all_handler_tasks if x is not None]))

        if len(unique_tasks) > 0:
            for task_name in unique_tasks:
                # get pks for this task
                task_file_pks = [x for x,
                                 y in zip(uploaded_files_pks, handler_tasks) if y == task_name]
                if len(task_file_pks) > 0:
                    new_task = app.signature(
                        task_name, [task_file_pks], immutable=True)
                    all_tasks.append(new_task)

        # For unique project tasks, fire off jobs to perform them
        flat_project_task_pks = [
            x for internal_list in project_task_pks for x in internal_list]

        unique_project_task_pks = list(set(flat_project_task_pks))
        if len(unique_project_task_pks) > 0:
            for project_task_pk in unique_project_task_pks:
                # get pks for this task
                task_file_pks = [x for x,
                                 y in zip(uploaded_files_pks, project_task_pks) if project_task_pk in y]
                if len(task_file_pks) > 0:
                    # get signature from the project job db object
                    task_obj = ProjectJob.objects.get(pk=project_task_pk)
                    new_task = task_obj.get_job_signature(task_file_pks)
                    all_tasks.append(new_task)

        if len(all_tasks) > 0:
            task_chain = chain(all_tasks)
            task_chain.apply_async()

    else:
        if verbose:
            logger.info("Determining final status based on invalid files...")
        final_status = status.HTTP_400_BAD_REQUEST
        if all([[y[x].get('status') == 403 for x in y.keys()][0] for y in invalid_files]):
            if verbose:
                logger.info(
                    "All invalid files have a status of 403. Setting final status to HTTP_403_FORBIDDEN.")
            final_status = status.HTTP_403_FORBIDDEN
    return (uploaded_files, invalid_files, existing_files, final_status)


def handle_uploaded_file(
    file: Union[object, UploadedFile],
    filepath: str,
    multipart: bool = False,
    verbose: bool = False
) -> None:
    """
    Upload and save a file to the specified filepath.

    Args:
        file (Union[object, UploadedFile]): The file object to save. Must provide a `chunks()` method.
        filepath (str): The destination path.
        multipart (bool, optional): If True, append to an existing file. Defaults to False.
        verbose (bool, optional): If True, log debug info. Defaults to False.

    Raises:
        OSError: If creating directories or writing to the file fails.

    Example:
        handle_uploaded_file(uploaded_file, '/path/to/save/file.txt', multipart=True, verbose=True)
    """
    os.makedirs(os.path.split(filepath)[0], exist_ok=True)
    if multipart and os.path.exists(filepath):
        if verbose:
            logger.info(f"Appending to {filepath}")
        with open(filepath, 'ab+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)
    else:
        if verbose:
            logger.info(f"Writing to {filepath}")
        with open(filepath, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)


def get_new_name(
    deployment: "Deployment",
    recording_dt: dt,
    file_local_path: str,
    file_path: str,
    file_n: Optional[int] = None
) -> str:
    """
    Generate a unique file name based on deployment, recording datetime, and file count.

    Args:
        deployment (Deployment): Associated deployment object.
        recording_dt (datetime): File recording datetime.
        file_local_path (str): Root local path for storage.
        file_path (str): Relative file path within storage root.
        file_n (Optional[int], optional): File count for uniqueness. Defaults to None.

    Returns:
        str: Unique file name in the format "{deployment_device_ID}_{YYYY-MM-DD_HH-MM-SS}_({file_n})"
    """
    if file_n is None:
        file_n = get_n_files(os.path.join(file_local_path, file_path)) + 1
    newname = f"{deployment.deployment_device_ID}_{dt.strftime(recording_dt, '%Y-%m-%d_%H-%M-%S')}_({file_n})"
    return newname


def get_n_files(dir_path: str) -> int:
    """
    Count the number of files in a directory that have an extension.

    Args:
        dir_path (str): Directory path.

    Returns:
        int: Number of files with an extension, or 0 if directory does not exist.
    """
    if os.path.exists(dir_path):
        all_files = os.listdir(dir_path)
        # Filter files that have an extension
        all_files = [x for x in all_files if '.' in x]
        n_files = len(all_files)
    else:
        n_files = 0
    return n_files


def group_files_by_size(
    file_objs: QuerySet,
    max_size: float = settings.MAX_ARCHIVE_SIZE_GB
) -> list[dict[str, float | list[int]]]:
    """
    Group files into batches by size, ensuring each batch does not exceed max_size (GB).

    Args:
        file_objs (QuerySet): Django QuerySet with 'pk' and 'file_size' attributes.
        max_size (float, optional): Maximum group size in GB. Defaults to settings.MAX_ARCHIVE_SIZE_GB.

    Returns:
        list[dict[str, float | list[int]]]: List of groups, where each dict contains:
            - "file_pks": List[int] - Primary keys of files in the group.
            - "total_size_gb": float - Total size of the group in GB.

    Notes:
        - Groups files in order of their 'recording_dt' attribute.
    """

    # Initialize variables to track the current group key, total size, and file information
    curr_key = 0
    curr_total = 0
    file_info = []

    # Order the file objects by their recording datetime to ensure logical grouping
    file_objs = file_objs.order_by('recording_dt')

    # Extract primary key and file size values from the file objects
    file_values = file_objs.values('pk', 'file_size')
    for file_value in file_values:
        # Convert the file size to GB for comparison
        file_size = convert_unit(file_value['file_size'], "GB")

        # Check if adding the current file would exceed the maximum allowed size for a group
        if (curr_total + file_size) > max_size:
            # If the new file would push over the max size, start a new group
            curr_total = file_size  # Reset the current total size to the new file's size
            curr_key += 1  # Increment the group key to start a new group
        else:
            # Otherwise, add the file's size to the current group's total size
            curr_total += file_size

        # Append the file's information along with its assigned group key
        file_info.append(
            {"pk": file_value['pk'], "file_size": file_size, "key": curr_key})

    # Initialize an empty list to store the grouped file information
    groups = []

    # Use itertools.groupby to group files by their assigned group key
    for k, g in itertools.groupby(file_info, lambda x: x.get("key")):
        # Convert the group iterator into a list for processing
        files = list(g)

        # Calculate the total size of the files in the current group
        total_size_gb = sum([x.get('file_size') for x in files])
        # Extract the primary keys of the files in the current group
        file_pks = [x.get('pk') for x in files]
        # Append the group information (file primary keys and total size) to the groups list
        groups.append({"file_pks": file_pks, "total_size_gb": total_size_gb})

    return groups
