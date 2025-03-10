import importlib
import os
from datetime import datetime
from typing import Callable, Tuple

from .tasks import *


class DataTypeHandler():
    data_types = ["default"]
    device_models = ["default"]
    safe_formats = [""]
    full_name = "No name provided"
    description = "No description provided"
    validity_description = "No validity description provided"
    handling_description = "No handling description provided"

    def format_check(self, file, device_label=None):
        return os.path.splitext(file.name)[1].lower() in self.safe_formats

    def all_file_format_check(self, files, device_label=None):
        for file in files:
            if self.format_check(file, device_label):
                return True
        return False

    def get_valid_files(self, files, device_label=None):
        return [x for x in files if self.format_check(x, device_label)]

    def handle_file(self,
                    file,
                    recording_dt: datetime = None,
                    extra_data: dict = None,
                    data_type: str = None) -> Tuple[datetime, dict, str, str]:

        if extra_data is None:
            extra_data = {}

        file_format = os.path.splitext(file.name)[1]

        return recording_dt, extra_data, data_type, self.get_post_download_task(file_format)

    def get_post_download_task(self, file_extension: str, first_time: bool = True):
        return None


class DataTypeHandlerCollection():

    data_type_handlers = {}

    def __init__(self, root_path="") -> None:
        handler_dir = os.path.join(
            root_path, "data_handlers", "handlers")
        handler_files = [os.path.splitext(x)[0] for x in os.listdir(
            handler_dir) if os.path.splitext(x)[1] == '.py']

        for handler_file in handler_files:
            importlib.import_module(
                f"data_handlers.handlers.{handler_file}")

        all_handlers = DataTypeHandler.__subclasses__()
        for handler in all_handlers:
            for data_type in handler.data_types:
                if not self.data_type_handlers.get(data_type):
                    self.data_type_handlers[data_type] = {}
                for model in handler.device_models:
                    self.data_type_handlers[data_type][model] = handler()

    def set_default_model(self, data_type, device_model):

        if data_type not in self.data_type_handlers.keys():
            return None

        if device_model not in self.data_type_handlers[data_type].keys()\
                or self.data_type_handlers.get(data_type) is None:
            device_model = "default"
        return device_model

    def get_valid_files(self, data_type, device_model, files, device_label=None):

        device_model = self.set_default_model(data_type, device_model)

        if device_model is None:
            return []

        return self.data_type_handlers[data_type][device_model].get_valid_files(files, device_label)

    def check_valid_files(self, data_type, device_model, files, device_label=None):
        device_model = self.set_default_model(data_type, device_model)

        if device_model is None:
            return False

        return self.data_type_handlers[data_type][device_model].all_file_format_check(files, device_label)

    def check_handlers(self, data_type, device_model):

        if self.data_type_handlers.get(data_type) is None:
            return False

        device_model = self.set_default_model(data_type, device_model)

        return self.data_type_handlers[data_type].get(device_model)

    def get_handler(self, data_type, device_model) -> DataTypeHandler:
        device_model = self.set_default_model(data_type, device_model)
        if device_model is None:
            return None
        print(f"Got data handler {data_type} {device_model}")
        return self.data_type_handlers[data_type][device_model]

    def get_file_handler(self, data_type, device_model) -> Callable:

        device_model = self.set_default_model(data_type, device_model)

        if device_model is None:
            return None
        print(f"Got data handler {data_type} {device_model}")
        return self.data_type_handlers[data_type][device_model].handle_file
