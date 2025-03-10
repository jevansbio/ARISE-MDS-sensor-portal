from .models import DataFile
from django.db.models import Count, Sum
from datetime import datetime
import pandas as pd
import numpy as np
import os


def get_all_file_metric_dicts(data_files, get_report_metrics=True):

    all_file_metric_dict = {}

    # Database metrics
    db_file_dict = get_database_file_metrics(data_files)
    if db_file_dict is not None:
        db_file_metric_dict = create_metric_dicts(
            db_file_dict, 'recording_dt__date', 'Date', ["bar", "scatter"])
        all_file_metric_dict.update(db_file_metric_dict)

    if get_report_metrics:
        # Report file metrics
        report_file_metric_dict = report_file_metrics(data_files)
        all_file_metric_dict.update(report_file_metric_dict)

    return all_file_metric_dict


def get_database_file_metrics(data_files):
    # do aggregation of files per day

    file_dict = data_files.values('recording_dt__date').annotate(
        files_per_day__number_of_files=Count('id'),
        file_volume_per_day__bytes=Sum('file_size')).values(
            'recording_dt__date',
            'files_per_day__number_of_files',
            'file_volume_per_day__bytes')

    file_dict = list(file_dict)

    if len(file_dict) == 0:
        return None

    file_dict = {k: [current_dict[k]
                     for current_dict in file_dict] for k in file_dict[0]}

    return file_dict


def create_metric_dicts(file_dict, x_key, x_label, plot_type):

    print(x_key, file_dict)

    x_values = [str(x) if type(x) is datetime or type(x) is pd.Timestamp else x
                for x in file_dict[x_key]]

    metrics = [x for x in file_dict.keys() if x != x_key]

    all_metrics_dict = {}

    for metric in metrics:
        split_metric = metric.split('__')
        if len(split_metric) > 1:
            metric_name, y_label = split_metric
            if y_label == "":
                continue
        else:
            metric_name = metric
            y_label = metric

        y_values = file_dict[metric]
        metric_dict = {"name": metric_name, "x_label": x_label, "y_label": y_label,
                       "x_values": x_values, "y_values": y_values, "plot_type": plot_type}
        all_metrics_dict[metric_name] = metric_dict

    return all_metrics_dict


def report_file_metrics(data_files):
    data_files = data_files.filter(
        file_type__name="report", local_storage=True, file_format=".csv")

    if not data_files.exists():
        return {}

    file_path_dicts = list(data_files.values(
        "local_path", "path", "file_name", "file_format"))

    # read the csv
    all_df_list = []
    for file_path_dict in file_path_dicts:
        file_path = os.path.join(file_path_dict["local_path"], file_path_dict["path"],
                                 file_path_dict["file_name"]+file_path_dict["file_format"])
        df = pd.read_csv(file_path)
        df.columns = df.columns.str.lower()
        all_df_list.append(df)

    full_df = pd.concat(all_df_list)

    print(full_df.dtypes)

    # try and find datetime
    full_df = full_df.apply(lambda col: pd.to_datetime(col, errors='ignore')
                            if col.dtypes == object and 'date' in col.name
                            else col,
                            axis=0)

    full_df = full_df.convert_dtypes()

    date_time_cols = full_df.select_dtypes(include=[np.datetime64])

    # for now just assume the first time column is the correct
    date_time_keys = list(date_time_cols.columns.values)

    if len(date_time_keys) == 0:
        return {}

    date_time_key = date_time_keys[0]
    if len(date_time_keys) > 1:
        full_df.drop(date_time_keys[1:])

    full_df_numeric = full_df.select_dtypes(include=[np.datetime64, np.number])

    file_dict = full_df_numeric.to_dict(orient="list")

    print(file_dict)

    metric_dict = create_metric_dicts(
        file_dict, date_time_key, "Date", ["scatter"])
    return metric_dict
