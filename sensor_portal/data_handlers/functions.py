import logging
import os
from datetime import datetime as dt
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from PIL import ExifTags, Image, TiffImagePlugin, UnidentifiedImageError

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from data_models.models import DataFile


def open_exif(uploaded_file: Any) -> Dict[str, Any]:
    """
    Open an uploaded image file and extract its EXIF metadata.

    Args:
        uploaded_file: Uploaded file, expected to have a `.file` attribute.

    Returns:
        A dictionary mapping EXIF tag names to their corresponding values.
        Returns an empty dictionary if the EXIF data cannot be read.
    """
    try:
        si = uploaded_file.file
        image = Image.open(si)
        image_exif = {ExifTags.TAGS[k]: v for k,
                      v in image.getexif().items() if k in ExifTags.TAGS}

        return image_exif
    except OSError:
        logger.error("Unable to open exif")
        return {}
    except UnidentifiedImageError:
        logger.error("Unable to open exif")
        return {}


def check_exif_keys(
    image_exif: Dict[str, Any],
    exif_keys: List[str],
    round_val: int = 2
) -> Dict[str, Any]:
    """
    Check and extract specified EXIF keys from the image's EXIF data, rounding float values.

    Args:
        image_exif: EXIF data as a dictionary.
        exif_keys: List of keys to extract from the EXIF data.
        round_val: Number of decimal places to round float values to.

    Returns:
        A dictionary of the requested EXIF key-value pairs, with floats rounded.
    """
    new_data = {}

    for exif_key in exif_keys:
        val = image_exif.get(exif_key)
        if val is not None:
            if type(val) is TiffImagePlugin.IFDRational:
                val = float(val)
            if type(val) is float:
                val = round(val, round_val)
            new_data[exif_key] = val

    return new_data


def get_image_recording_dt(image_exif: Dict[str, Any]) -> Optional[dt]:
    """
    Get the recording datetime from image EXIF data.

    Args:
        image_exif: EXIF data as a dictionary.

    Returns:
        A datetime object representing when the image was recorded, or None if not available.
    """
    recording_dt = image_exif.get('DateTimeOriginal')
    if recording_dt is None:
        recording_dt = image_exif.get('DateTime')
    if recording_dt is None:
        return None
    return dt.strptime(recording_dt, '%Y:%m:%d %H:%M:%S')


def generate_thumbnail(
    data_file: 'DataFile',
    max_width: int = 250,
    max_height: int = 250
) -> Tuple[Any, List[str]]:
    """
    Generate a thumbnail for the given image file.

    Args:
        data_file: DataFile object.
        max_width: The maximum width of the thumbnail.
        max_height: The maximum height of the thumbnail.

    Returns:
        A tuple containing:
            - the modified data_file object (with updated thumbnail URL)
            - a list of modified attributes (['thumb_url'])
    """
    file_path = data_file.full_path()
    thumb_path = os.path.join(os.path.split(
        file_path)[0], data_file.file_name+"_THUMB.jpg")

    # open image file
    image = Image.open(file_path)
    image.thumbnail((max_width, max_height))

    # creating thumbnail
    image.save(thumb_path)
    data_file.set_thumb_url()

    return data_file, ["thumb_url"]
