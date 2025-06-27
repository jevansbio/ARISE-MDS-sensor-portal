import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from aerocam_handler.reader import DatReader
from celery import shared_task
from data_handlers.base_data_handler_class import DataTypeHandler

from sensor_portal.celery import app


class AeroCamHandler(DataTypeHandler):
    """
    Data handler for Aeroecology camera .dat files.
    Handles decoding, validation, and post-download processing.
    """
    data_types: List[str] = ["aeroecologycamera"]
    device_models: List[str] = ["default"]
    safe_formats: List[str] = [".dat"]
    full_name: str = "Aeroecology handler"
    description: str = "Data handler for aeroecology files."
    validity_description: str = """
    <ul>
    <li>Must be a swiss bird radar aerocam dat file</li>
    </ul>
    """
    handling_description: str = """
    <ul>
    <li>dat files are decoded for human viewing</li>
    </li>
    </ul>
    """

    def handle_file(
        self,
        file: Any,
        recording_dt: Optional[datetime] = None,
        extra_data: Optional[Dict] = None,
        data_type: Optional[str] = None
    ) -> Tuple[datetime, Dict, str, Any]:
        """
        Handles a newly uploaded AeroCam file.

        Args:
            file: The file object to handle.
            recording_dt: Optional datetime when the recording was made.
            extra_data: Optional extra metadata about the file.
            data_type: Optional string describing the data type.

        Returns:
            Tuple containing the recording datetime, extra data dictionary, data type string, and any task info.
        """
        recording_dt, extra_data, data_type, task = super().handle_file(
            file, recording_dt, extra_data, data_type
        )

        if recording_dt is None:
            recording_dt = datetime.now()

        return recording_dt, extra_data, data_type, task

    def get_post_download_task(
        self,
        file_extension: str,
        first_time: bool = True
    ) -> str:
        """
        Returns the post-download task to be performed for this handler.

        Args:
            file_extension: The file extension of the downloaded file.
            first_time: Whether this is the first time this file is being handled.

        Returns:
            The name of the Celery task to run.
        """
        # Always convert the file
        return "aerocam_converter"


@app.task(name="aerocam_converter")
def aerocam_converter_task(file_pks: List[int]) -> None:
    """
    Celery task to process AeroCam files after upload.

    Args:
        file_pks: List of primary keys of DataFile objects to process.

    Returns:
        None
    """
    from data_handlers.post_upload_task_handler import post_upload_task_handler
    from data_models.models import DataFile, Deployment

    post_upload_task_handler(file_pks, aerocam_convert)

    deployment_pk = DataFile.objects.filter(pk__in=file_pks).values_list(
        'deployment__pk', flat=True).distinct()
    deployment_objs = Deployment.objects.filter(pk__in=deployment_pk)
    for deployment_obj in deployment_objs:
        deployment_obj.set_thumb_url()

    Deployment.objects.bulk_update(deployment_objs, ["thumb_url"])


def aerocam_convert(data_file: Any) -> Tuple[Optional[Any], Optional[List[str]]]:
    """
    Converts an AeroCam .dat file into image outputs and links them to the DataFile.

    Args:
        data_file: The DataFile object representing the .dat file.

    Returns:
        Tuple containing the updated DataFile and a list of updated fields.
    """
    dat_file_path: str = data_file.full_path()

    # Create DatReader instance
    dat_handler: DatReader = DatReader()

    thumb_path: str = os.path.join(
        os.path.split(dat_file_path)[0], data_file.file_name + "_THUMB.jpg"
    )
    concat_path: str = os.path.join(
        os.path.split(dat_file_path)[0], data_file.file_name + "_CONCAT.jpg"
    )
    anim_path: str = os.path.join(
        os.path.split(dat_file_path)[0], data_file.file_name + "_ANIM.gif"
    )

    # Load a file
    with open(dat_file_path, 'rb') as f:
        dat_handler.open_dat_file(f)

    if dat_handler.image_list:
        # Get largest image from sequence to use as a thumbnail
        thumb = max(
            dat_handler.image_list,
            key=lambda img: img.size[0] * img.size[1]
        ).copy()
        thumb.thumbnail((100, 100))
        thumb.save(thumb_path)
    else:
        thumb = None

    dat_handler.save_concatenated_image(concat_path)
    dat_handler.save_animation(anim_path)

    data_file.set_thumb_url()
    data_file.linked_files = {
        "Image": {"path": concat_path},
        "Animation": {"path": anim_path},
    }
    data_file.set_linked_files_urls()
    return data_file, ["thumb_url", "linked_files"]
