
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import dateutil.parser
import pandas as pd
from data_handlers.functions import (check_exif_keys, get_image_recording_dt,
                                     open_exif)
from data_handlers.handlers.default_image_handler import DataTypeHandler
from django.core.files import File

from sensor_portal.celery import app


class Snyper4GHandler(DataTypeHandler):
    """
    Data handler for the 'Snyper Commander 4G Wireless' and 'Wilsus Tradenda 4G Wireless' wildlife  cameras.
    Handles image and daily report text files, extracting metadata and performing post-processing.
    """
    data_types = ["wildlifecamera", "timelapsecamera"]
    device_models = ["Snyper Commander 4G Wireless",
                     "Wilsus Tradenda 4G Wireless"]
    safe_formats = [".jpg", ".jpeg", ".txt", ".csv"]
    full_name = "Wide 4G handler"
    description = """Data handler for wide 4G wildlifecamera"""
    validity_description = \
        """<ul>
    <li>File format must be in available formats.</li>
    <li>Image naming convention must be in the format []-[Image type (ME, TL, DR)]-[]., e.g '860946060409946-ME-27012025134802-SYPW1128' or '860946060409946-DR-27012025120154-SYPW1120'</li>
    <li>Text file must be in the structure of SOMETHING</li>
    </ul>
    """.replace("\n", "<br>")
    handling_description = \
        """<ul>
    <li>Recording datetime is extracted from exif.</li>
    <li><strong>Extra metadata attached:</strong>
    <ul>
    <li> YResolution, XResolutiom, Software: extracted from exif</li>
    <li> 'daily_report': Added if the file is a daily report text file or image. Extracted from filename or format.</li>
    </ul>
    </li>
    <li>Thumbnails are generated.</li>
    </ul>
    """.replace("\n", "<br>")

    def handle_file(
        self,
        file: Any,
        recording_dt: Optional[datetime] = None,
        extra_data: Optional[Dict[str, Any]] = None,
        data_type: Optional[str] = None
    ) -> Tuple[Optional[datetime], Dict[str, Any], str, Optional[str]]:
        """
        Handles a file (image or text report), extracting metadata and determining data type.

        Args:
            file: The file object to process.
            recording_dt: An optional datetime object representing the recording time.
            extra_data: Optional dict for extra metadata.
            data_type: Optional string to indicate the data type.

        Returns:
            Tuple containing the recording datetime, extra metadata, data type, and a post-processing task name.
        """
        recording_dt, extra_data, data_type, task = super().handle_file(
            file, recording_dt, extra_data, data_type)

        split_filename = os.path.splitext(file.name)
        file_extension = split_filename[1]

        if file_extension == ".txt":
            report_dict = parse_report_file(file)
            if report_dict.get('Date') is None:
                recording_dt = None
            else:
                dates = [dateutil.parser.parse(x, dayfirst=True)
                         for x in report_dict['Date']]
                recording_dt = min(dates)
            extra_data["daily_report"] = True
            data_type = "report"
        else:
            split_image_filename = split_filename[0].split("-")
            expected_codes = ["TL", "DR", "ME", "RC"]
            type_code = split_image_filename[1]
            # Support some different software versions
            if type_code not in expected_codes:
                type_code = split_image_filename[0]
            if type_code not in expected_codes:
                type_code = "ME"

            match type_code:
                case "TL":
                    data_type = "timelapsecamera"
                case "DR":
                    data_type = "timelapsecamera"
                    extra_data["daily_report"] = True
                case "RC":
                    extra_data["manual_trigger"] = True
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

        return recording_dt, extra_data, data_type, task

    def get_post_download_task(self, file_extension: str, first_time: bool = True) -> Optional[str]:
        """
        Determines the post-download task to run based on file extension.

        Args:
            file_extension: The file extension string.
            first_time: Boolean indicating if this is the first time processing.

        Returns:
            A string with the task name, or None if no task is needed.
        """
        task = None
        if file_extension == ".txt" and first_time:
            task = "snyper4G_convert_daily_report"
        elif file_extension.lower() in [".jpeg", ".jpeg", ".jpg"]:
            task = "data_handler_generate_thumbnails"
        return task


def parse_report_file(file: Any) -> Dict[str, List[str]]:
    """
    Parses a daily report text file into a dictionary.

    Args:
        file: The file object to parse.

    Returns:
        A dictionary with keys as field names and values as lists of strings.
    """
    report_dict: Dict[str, List[str]] = {}
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


@app.task(name="snyper4G_convert_daily_report")
def convert_daily_report_task(file_pks: List[int]) -> None:
    """
    Celery task to convert daily report text files to CSV for given file primary keys.

    Args:
        file_pks: List of file primary keys to process.
    """
    from data_handlers.post_upload_task_handler import post_upload_task_handler
    post_upload_task_handler(file_pks, convert_daily_report)


def convert_daily_report(data_file: Any) -> Tuple[Optional[Any], Optional[List[str]]]:
    """
    Converts a daily report text file to CSV and updates the file object.

    Args:
        data_file: The file object to process.

    Returns:
        Tuple of the updated file object and a list of updated fields, or None if not applicable.
    """
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
            def divide(num_1: int, num_2: int) -> float:
                return num_1 / num_2

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
            data_file_path_split[0], data_file_name + ".csv")

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
