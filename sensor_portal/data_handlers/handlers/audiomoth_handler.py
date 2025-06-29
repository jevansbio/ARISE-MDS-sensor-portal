from datetime import datetime
from typing import Tuple

from data_handlers.base_data_handler_class import DataTypeHandler
from data_handlers.functions import check_tag_keys
from dateutil import parser
from tinytag import TinyTag


class AudioMothHandler(DataTypeHandler):
    """
    Data handler for processing image files from various camera types.

    This handler extracts metadata from image files, especially EXIF data,
    to supplement or determine recording information and other image properties.
    """
    data_types = ["audio"]
    device_models = ["audiomoth"]
    safe_formats = [".mp3", ".wav", ".ogg", ".flac"]
    full_name = "Audiomoth audio handler"
    description = """Quick handler to deal with extracting info from audiomoth."""
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

        tag_info = TinyTag.get(file_obj=file).__dict__
        if tag_info is not None:

            comment = tag_info['comment']
            if comment is not None:
                audio_dt = None
                try:
                    start = comment.find("Recorded at ") + len("Recorded at ")
                    end = comment.find(' by AudioMoth')
                    audio_dt = comment[start:end]
                    audio_dt = audio_dt.replace(")", "").replace(
                        "(", "").replace("+", "-")
                    audio_dt = parser.parse(audio_dt, dayfirst=True)
                except:
                    start = comment.find("Recorded at ") + len("Recorded at ")
                    end = comment.find(' during deployment')
                    audio_dt = comment[start:end]
                    audio_dt = audio_dt.replace(")", "").replace(
                        "(", "").replace("+", "-")
                    audio_dt = parser.parse(audio_dt, dayfirst=True)
                if audio_dt is not None:
                    recording_dt = audio_dt

            new_extra_data = check_tag_keys(tag_info, [
                "bitrate",
                "samplerate",
                "duration",
                "channels",
                "comment",
            ], round_val=2)

            extra_data.update(new_extra_data)

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
