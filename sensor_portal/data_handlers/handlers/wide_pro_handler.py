import io
import os
from datetime import datetime
from typing import Any, List, Tuple

import dateutil.parser
import pandas as pd
from celery import shared_task
from data_handlers.functions import (check_exif_keys, get_image_recording_dt,
                                     open_exif)
from data_handlers.handlers.default_image_handler import DataTypeHandler
from django.core.files import File


class Snyper4GHandler(DataTypeHandler):
    data_types = ["wildlifecamera", "timelapsecamera"]
    device_models = ["4G Wide Pro"]
    safe_formats = [".jpg", ".jpeg", ".txt"]
    full_name = "Wide 4G handler"
    description = """Data handler for wide 4G wildlifecamera"""
    validity_description = """<ul>
    <li>File format must be in available formats.</li>
    <li>Image naming convention must be in the format []-[Image type (ME, TL, DR)]-[]., e.g '860946060409946-ME-27012025134802-SYPW1128' or '860946060409946-DR-27012025120154-SYPW1120'</li>
    <li>Text file must be in the structure of SOMETHING</li>
    </ul>"""
    handling_description = """<ul>
    <li>Recording datetime is extracted from exif.</li>
    <li><strong>Extra metadata attached:</strong>
    <ul>
    <li> YResolution, XResolutiom, Software: extracted from exif</li>
    <li> 'daily_report': Added if the file is a daily report text file or image. Extracted from filename or format.
    </ul>
    </li>
    </ul>"""

    def handle_file(self, file, recording_dt: datetime = None, extra_data: dict = None, data_type: str = None) -> Tuple[datetime, dict, str]:
        recording_dt, extra_data, data_type, task = super().handle_file(
            file, recording_dt, extra_data, data_type)

        split_filename = os.path.splitext(file.name)
        file_extension = split_filename[1]

        if file_extension == ".txt":

            report_dict = parse_report_file(file)

            dates = [dateutil.parser.parse(x, dayfirst=True)
                     for x in report_dict['Date']]
            recording_dt = min(dates)
            extra_data["daily_report"] = True

            data_type = "report"

        else:
            split_image_filename = split_filename[0].split("-")

            match split_image_filename[1]:
                case "TL":
                    data_type = "timelapsecamera"
                case "DR":
                    data_type = "timelapsecamera"
                    extra_data["daily_report"] = True
                case "ME":
                    data_type = "wildlifecamera"
                case _:
                    data_type = "wildlifecamera"

            image_exif = open_exif(file)
            recording_dt = get_image_recording_dt(image_exif)

            # YResolution XResolution Software
            new_extra_data = check_exif_keys(image_exif, [
                "YResolution", "XResolution", "Software"])

            extra_data.update(new_extra_data)
            task = "data_handler_generate_thumbnails"

        return recording_dt, extra_data, data_type, task


def get_post_download_task(self, file_extension: str, first_time: bool = True):
    task = None
    if file_extension == ".txt" and first_time:
        task = "snyper4G_convert_daily_report"
    elif file_extension.lower() in [".jpeg", ".jpeg"]:
        task = "data_handler_generate_thumbnails"
    return task


def parse_report_file(file):
    report_dict = {}
    # Should extract date time from file
    for line in file.file:
        line = line.decode("utf-8")
        line_split = line.split(":", 1)
        line_split[1] = line_split[1].replace("\n", "")
        line_split[1] = line_split[1].replace("\r", "")

        if line_split[0] not in report_dict.keys():
            report_dict[line_split[0]] = []

        report_dict[line_split[0]].append(line_split[1])
    return report_dict


@shared_task(name="snyper4G_convert_daily_report")
def convert_daily_report_task(file_names: List[str]):
    from data_handlers.post_upload_task_handler import post_upload_task_handler
    post_upload_task_handler(file_names, convert_daily_report)


def convert_daily_report(data_file) -> Tuple[Any | None, List[str] | None]:
    # specific handler task
    data_file_path = data_file.full_path()
    # open txt file
    with File(open(data_file_path, mode='rb'), os.path.split(data_file_path)[1]) as txt_file:
        report_dict = parse_report_file(txt_file)

        report_dict['Date'] = [dateutil.parser.parse(x, dayfirst=True)
                               for x in report_dict['Date']]

        report_dict = {k.lower(): v for k, v in report_dict.items()}

        # convert to CSV file
        report_df = pd.DataFrame.from_dict(report_dict)

        # specific handling of columns
        if 'battery' in report_df.columns:
            # remove string from number
            report_df['battery'] = report_df['battery'].apply(
                lambda x: x.replace("%", ""))

        if 'temp' in report_df.columns:
            # remove string from number
            report_df['temp'] = report_df['temp'].apply(
                lambda x: x.replace(" Celsius Degree", ""))

        if 'sd' in report_df.columns:
            # split by /, remove the M, convert to number, divide.
            def divide(num_1, num_2):
                return num_1/num_2

            report_df['sd'] = report_df['sd'].apply(lambda x: divide(*[int(y.replace("M", ""))
                                                                       for y in x.split("/")]))

        # rename columns more informatively or to skip in plotting
        report_df = report_df.rename(columns={"imei": "imei__",
                                              "csq": "csq__",
                                              "temp": "temp__temperature_degrees_celsius",
                                              "battery": "battery__battery_%",
                                              "sd": "sd__proportion_sd"})

        # write CSV, delete txt
        data_file_path_split = os.path.split(data_file_path)
        data_file_name = os.path.splitext(data_file_path_split[1])[0]

        data_file_csv_path = os.path.join(
            data_file_path_split[0], data_file_name+".csv")

        report_df.to_csv(data_file_csv_path, index_label=False, index=False)
        # update file object
        data_file.file_size = os.stat(data_file_csv_path).st_size
        data_file.modified_on = datetime.now()
        data_file.file_format = ".csv"

        # remove original file
        os.remove(data_file_path)

        return data_file, [
            "file_size", "modified_on", "file_format"]

        # end specific handler task
