from datetime import datetime as dt
from PIL import ExifTags, Image, TiffImagePlugin
import os


def open_exif(uploaded_file):
    si = uploaded_file.file
    image = Image.open(si)
    image_exif = {ExifTags.TAGS[k]: v for k,
                  v in image.getexif().items() if k in ExifTags.TAGS}

    return image_exif


def check_exif_keys(image_exif, exif_keys, round_val=2):
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


def get_image_recording_dt(image_exif):

    recording_dt = image_exif.get('DateTimeOriginal')
    if recording_dt is None:
        recording_dt = image_exif.get('DateTime')
    if recording_dt is None:
        return None
    return dt.strptime(recording_dt, '%Y:%m:%d %H:%M:%S')


def generate_thumbnail(data_file, max_width=100, max_height=100):
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
