import os
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

import dateutil.parser
import soundfile as sf
from data_handlers.handlers.default_image_handler import DataTypeHandler
from django.core.files import File


class BUGGHandler(DataTypeHandler):
    """
    Data handler for BUGG and BUGGv3 audio devices.
    Provides methods to process audio files, extract recording datetime and audio metadata.
    """

    data_types = ["audio"]
    device_models = ["BUGG", "BUGGv3"]
    safe_formats = [".mp3"]
    full_name = "BUGG"
    description = """Data handler for BUGG"""
    validity_description = (
        """<ul>
        </ul>"""
        .replace("\n", "<br>")
    )
    handling_description = (
        """<ul>
        </ul>"""
        .replace("\n", "<br>")
    )

    def handle_file(
        self,
        file: File,
        recording_dt: Optional[datetime] = None,
        extra_data: Optional[Dict[str, Any]] = None,
        data_type: Optional[str] = None,
    ) -> Tuple[datetime, Dict[str, Any], Optional[str], Any]:
        """
        Process an uploaded audio file from a BUGG device.

        Args:
            file (File): The uploaded file object.
            recording_dt (Optional[datetime], optional): Recording date/time, if already known.
            extra_data (Optional[Dict[str, Any]], optional): Additional metadata to augment.
            data_type (Optional[str], optional): The type of data being handled.

        Returns:
            Tuple[datetime, Dict[str, Any], Optional[str], Any]: A tuple containing:
                - recording_dt (datetime): The parsed recording datetime.
                - extra_data (dict): Updated dictionary with extracted audio metadata (sample_rate, duration).
                - data_type (str): Updated or confirmed data type.
                - task: Any post-processing task, if applicable.
        """
        recording_dt, extra_data, data_type, task = super().handle_file(
            file, recording_dt, extra_data, data_type
        )

        split_filename = os.path.splitext(file.name)
        file_filename = split_filename[0]
        recording_dt = dateutil.parser.parse(
            file_filename.replace("_", ":"), yearfirst=True
        )

        with sf.SoundFile(file.file, 'rb') as f:
            extra_data.update({
                "sample_rate": f._info.samplerate,
                "duration": float(f._info.frames / f._info.samplerate)
            })

        return recording_dt, extra_data, data_type, task

    def get_post_download_task(
        self,
        file_extension: str,
        first_time: bool = True
    ) -> Optional[Any]:
        """
        Return any asynchronous post-download task related to BUGG files.

        Args:
            file_extension (str): Extension of the downloaded file.
            first_time (bool, optional):  Whether this is the first time handling the file.

        Returns:
            Optional[Any]: Celery task, if applicable. None by default.
        """
        task = None
        return task
