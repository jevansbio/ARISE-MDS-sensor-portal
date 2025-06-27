from datetime import datetime
from typing import Tuple

from data_handlers.base_data_handler_class import DataTypeHandler
from data_handlers.functions import (check_exif_keys, get_image_recording_dt,
                                     open_exif)


class DefaultImageHandler(DataTypeHandler):
    """
    Data handler for processing image files from various camera types.

    This handler extracts metadata from image files, especially EXIF data,
    to supplement or determine recording information and other image properties.
    """
    data_types = ["wildlifecamera", "insectcamera", "timelapsecamera"]
    device_models = ["default"]
    safe_formats = [".jpg", ".jpeg", ".png"]
    full_name = "Default image handler"
    description = """Data handler for image files."""
    validity_description =\
        """
    <ul>
    <li>Image format must be in available formats.</li>
    </ul>
    """
    handling_description = \
        """
    <ul>
    <li>Recording datetime is extracted from exif.</li>
    <li><strong>Extra metadata attached:</strong>
    <ul>
    <li> Image dimensions: extracted from exif</li>
    <li> Shutter speed: attempt to extract from exif</li>
    <li> Aperture value: attempt to extract from exif</li>
    </ul>
    </li>
    </ul>
    """

    def handle_file(self, file, recording_dt: datetime = None, extra_data: dict = None, data_type: str = None) -> Tuple[datetime, dict, str]:
        """
        Process an image file by extracting EXIF metadata and determining recording datetime.

        Args:
            file: The image file to process.
            recording_dt (datetime, optional): The initial recording datetime, if available.
            extra_data (dict, optional): Dictionary to store additional metadata.
            data_type (str, optional): Type of data being handled.

        Returns:
            Tuple containing:
                - recording_dt (datetime): The recording datetime from EXIF or input.
                - extra_data (dict): Updated metadata including image properties.
                - data_type (str): The data type.
                - task (str): The next processing task.
        """
        recording_dt, extra_data, data_type, task = super().handle_file(
            file, recording_dt, extra_data, data_type)

        image_exif = open_exif(file)
        recording_dt = get_image_recording_dt(image_exif)

        new_extra_data = check_exif_keys(image_exif, [
                                         "ExifImageWidth", "ExifImageHeight", "camerashutterspeed", "cameraaperture"])
        # YResolution XResolution Software

        extra_data.update(new_extra_data)

        return recording_dt, extra_data, data_type, task

    def get_post_download_task(self, file_extension: str, first_time: bool = True):
        """
        Returns the post-download processing task to perform for image files.

        Args:
            file_extension (str): The extension of the downloaded file.
            first_time (bool, optional): Whether this is the first time handling the file.

        Returns:
            str: The task name to perform after download (always generates a thumbnail).
        """
        # Always generate a thumbnail
        return "data_handler_generate_thumbnails"
