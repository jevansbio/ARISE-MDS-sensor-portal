from datetime import datetime
from typing import Tuple

from data_handlers.base_data_handler_class import DataTypeHandler


class BasicAudio(DataTypeHandler):
    """
    Data handler for processing image files from various camera types.

    This handler extracts metadata from image files, especially EXIF data,
    to supplement or determine recording information and other image properties.
    """
    data_types = ["audio"]
    device_models = ["default"]
    safe_formats = [".mp3", ".wav", ".ogg"]
    full_name = "Basic audio handler"
    description = """Empty handler when downloading an audio file where a specific model handler is unavailable."""
    validity_description =\
        """

    """
    handling_description = \
        """

    """

    def handle_file(self, file, recording_dt: datetime = None, extra_data: dict = None, data_type: str = None) -> Tuple[datetime, dict, str]:
        """
        Empty handler when downloading an audio file where a specific model handler is unavailable (or could be extended to handle other media types).

        Args:
            file: The image file to process.
            recording_dt (datetime, optional): The initial recording datetime, if available.
            extra_data (dict, optional): Dictionary to store additional metadata.
            data_type (str, optional): Type of data being handled.

        Returns:
            Tuple containing:
                - recording_dt (datetime): The recording datetime input.
                - extra_data (dict): Input metadata.
                - data_type (str): The data type.
                - task (str): The next processing task.
        """
        recording_dt, extra_data, data_type, task = super().handle_file(
            file, recording_dt, extra_data, data_type)

        return recording_dt, extra_data, data_type, task

    def get_post_download_task(self, file_extension: str, first_time: bool = True):
        """
        Returns the post-download processing task to perform.

        Args:
            file_extension (str): The extension of the downloaded file.
            first_time (bool, optional): Whether this is the first time handling the file.

        Returns:
            str: The task name to perform after download.
        """
        return None
