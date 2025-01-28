from data_handlers.base_data_handler_class import data_type_handler
from datetime import datetime
from typing import Tuple
from data_handlers.functions import open_exif, check_exif_keys, get_image_recording_dt


class DefaultImageHandler(DataTypeHandler):
    data_types = ["wildlifecamera", "insectcamera", "timelapsecamera"]
    device_models = ["default"]
    safe_formats = [".jpg", ".jpeg", ".png"]
    main_media_type = "image"
    full_name = "Default image handler"
    description = """Data handler for image files."""
    validity_description = """<ul>
    <li>Image format must be in available formats.</li>
    </ul>"""
    handling_description = """<ul>
    <li>Recording datetime is extracted from exif.</li>
    <li>Recording datetime is assumed to be in local timezone.</li>
    <li>New filename is generated, csv is saved with this new filename</li>
    <li><strong>Extra metadata attached:</strong>
    <ul>
    <li> Image dimensions: extracted from exif</li>
    <li> Shutter speed: attempt to extract from exif</li>
    <li> Aperture value: attempt to extract from exif</li>
    </ul>
    </li>
    </ul>"""

    def handle_file(self, file, recording_dt: datetime = None, extra_data: dict = None, data_type: str = None) -> Tuple[datetime, dict, str]:
        recording_dt, extra_data, data_type = super().handle_file(
            file, recording_dt, extra_data, data_type)
        image_exif = open_exif(file)
        recording_dt = get_image_recording_dt(image_exif)

        new_extra_data = check_exif_keys(image_exif, [
                                         "ExifImageWidth", "ExifImageHeight", "camerashutterspeed", "cameraaperture"])
        # YResolution XResolution Software

        extra_data.update(new_extra_data)

        return recording_dt, extra_data, data_type
