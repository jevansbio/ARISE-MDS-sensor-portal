from datetime import datetime
from typing import Tuple

from data_handlers.base_data_handler_class import DataTypeHandler
from data_handlers.functions import (check_exif_keys, get_image_recording_dt,
                                     open_exif)


class DefaultImageHandler(DataTypeHandler):
    data_types = ["wildlifecamera", "insectcamera", "timelapsecamera"]
    device_models = ["default"]
    safe_formats = [".jpg", ".jpeg", ".png"]
    full_name = "Default image handler"
    description = """Data handler for image files."""
    validity_description = """<ul>
    <li>Image format must be in available formats.</li>
    </ul>"""
    handling_description = """<ul>
    <li>Recording datetime is extracted from exif.</li>
    <li><strong>Extra metadata attached:</strong>
    <ul>
    <li> Image dimensions: extracted from exif</li>
    <li> Shutter speed: attempt to extract from exif</li>
    <li> Aperture value: attempt to extract from exif</li>
    </ul>
    </li>
    </ul>"""

    def handle_file(self, file, recording_dt: datetime = None, extra_data: dict = None, data_type: str = None) -> Tuple[datetime, dict, str]:
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
        # Always generate a thumbnail
        return "data_handler_generate_thumbnails"
