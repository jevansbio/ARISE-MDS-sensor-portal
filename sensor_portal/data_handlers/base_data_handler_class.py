import importlib
import logging
import os
from datetime import datetime
from typing import Callable, Tuple

from .tasks import *

logger = logging.getLogger(__name__)


class DataTypeHandler():
    """
    Base class for handling different data types and device models.
    Provides interfaces for file format checking, file handling, and post-download tasks.
    """

    data_types = ["default"]
    device_models = ["default"]
    safe_formats = [""]
    full_name = "No name provided"
    description = "No description provided"
    validity_description = "No validity description provided"
    handling_description = "No handling description provided"
    post_handling_description = "No post handling description provided"

    def format_check(self, file, device_label=None):
        """
        Check if the file's extension is in the list of safe formats.

        Args:
            file: File-like object with a 'name' attribute.
            device_label (optional): Device label, not used by default.

        Returns:
            bool: True if file format is safe, False otherwise.
        """
        return os.path.splitext(file.name)[1].lower() in self.safe_formats

    def all_file_format_check(self, files, device_label=None):
        """
        Check if any file in a list matches a safe file format.

        Args:
            files (list): List of file-like objects.
            device_label (optional): Device label, not used by default.

        Returns:
            bool: True if any file matches a safe format, False otherwise.
        """
        for file in files:
            if self.format_check(file, device_label):
                return True
        return False

    def get_valid_files(self, files, device_label=None):
        """
        Return a list of files that match the safe formats.

        Args:
            files (list): List of file-like objects.
            device_label (optional): Device label, not used by default.

        Returns:
            list: List of valid files.
        """
        return [x for x in files if self.format_check(x, device_label)]

    def handle_file(self,
                    file,
                    recording_dt: datetime = None,
                    extra_data: dict = None,
                    data_type: str = None) -> Tuple[datetime, dict, str, str]:
        """
        Handle a file after download, performing any post-processing or validation.

        Args:
            file: File-like object with a 'name' attribute.
            recording_dt (datetime, optional): Recording datetime.
            extra_data (dict, optional): Additional data.
            data_type (str, optional): The type of data.

        Returns:
            tuple: (recording_dt, extra_data, data_type, post_download_task)
        """
        if extra_data is None:
            extra_data = {}

        file_format = os.path.splitext(file.name)[1]

        return recording_dt, extra_data, data_type, self.get_post_download_task(file_format)

    def get_post_download_task(self, file_extension: str, first_time: bool = True):
        """
        Get a post-download task for the given file extension.

        Args:
            file_extension (str): The file's extension.
            first_time (bool, optional): Whether this is the first time handling the file.

        Returns:
            Any: Task to perform after download. Defaults to None.
        """
        return None


class DataTypeHandlerCollection():
    """
    Collection class for managing multiple DataTypeHandler subclasses.
    Handles dynamic importing and retrieval of handlers based on data type and device model.
    """

    data_type_handlers = {}
    data_handler_list = []

    def __init__(self, root_path="") -> None:
        """
        Initialize the collection by importing all handler modules and instantiating their classes.

        Args:
            root_path (str, optional): Root path to the handlers directory.
        """
        handler_dir = os.path.join(
            root_path, "data_handlers", "handlers")
        handler_files = [os.path.splitext(x)[0] for x in os.listdir(
            handler_dir) if os.path.splitext(x)[1] == '.py']

        for handler_file in handler_files:
            importlib.import_module(
                f"data_handlers.handlers.{handler_file}")

        all_handlers = DataTypeHandler.__subclasses__()
        for idx, handler in enumerate(all_handlers):
            handler_instance = handler()
            handler_instance.id = idx
            self.data_handler_list.append(handler_instance)
            for data_type in handler.data_types:
                if not self.data_type_handlers.get(data_type):
                    self.data_type_handlers[data_type] = {}
                for model in handler.device_models:
                    self.data_type_handlers[data_type][model] = handler_instance

    def set_default_model(self, data_type, device_model):
        """
        Ensure the device model exists for the given data type, defaulting to 'default' if not found.

        Args:
            data_type (str): The data type.
            device_model (str): The device model.

        Returns:
            str or None: The resolved device model, or None if not available.
        """
        if data_type not in self.data_type_handlers.keys():
            return None

        if device_model not in self.data_type_handlers[data_type].keys()\
                or self.data_type_handlers.get(data_type) is None:
            device_model = "default"
        return device_model

    def get_valid_files(self, data_type, device_model, files, device_label=None):
        """
        Get files valid for a specified data type and device model.

        Args:
            data_type (str): The data type.
            device_model (str): The device model.
            files (list): List of file-like objects.
            device_label (optional): Device label, not used by default.

        Returns:
            list: List of valid files.
        """
        device_model = self.set_default_model(data_type, device_model)

        if device_model is None:
            return []

        return self.data_type_handlers[data_type][device_model].get_valid_files(files, device_label)

    def check_valid_files(self, data_type, device_model, files, device_label=None):
        """
        Check if any files are valid for a given data type and device model.

        Args:
            data_type (str): The data type.
            device_model (str): The device model.
            files (list): List of file-like objects.
            device_label (optional): Device label, not used by default.

        Returns:
            bool: True if any valid files exist, False otherwise.
        """
        device_model = self.set_default_model(data_type, device_model)

        if device_model is None:
            return False

        return self.data_type_handlers[data_type][device_model].all_file_format_check(files, device_label)

    def check_handlers(self, data_type, device_model):
        """
        Check if a handler exists for the given data type and device model.

        Args:
            data_type (str): The data type.
            device_model (str): The device model.

        Returns:
            DataTypeHandler or False: The handler instance if found, otherwise False.
        """
        if self.data_type_handlers.get(data_type) is None:
            return False

        device_model = self.set_default_model(data_type, device_model)

        return self.data_type_handlers[data_type].get(device_model)

    def get_handler(self, data_type, device_model) -> DataTypeHandler:
        """
        Retrieve the DataTypeHandler instance for the given data type and device model.

        Args:
            data_type (str): The data type.
            device_model (str): The device model.

        Returns:
            DataTypeHandler or None: The handler instance, or None if not found.
        """
        device_model = self.set_default_model(data_type, device_model)
        if device_model is None:
            return None
        logger.info(f"Got data handler {data_type} {device_model}")
        return self.data_type_handlers[data_type].get(device_model)

    def get_file_handler(self, data_type, device_model) -> Callable:
        """
        Retrieve the file handling function for the given data type and device model.

        Args:
            data_type (str): The data type.
            device_model (str): The device model.

        Returns:
            Callable or None: The file handler function, or None if not found.
        """
        device_model = self.set_default_model(data_type, device_model)

        if device_model is None:
            return None
        logger.info(f"Got data handler {data_type} {device_model}")

        return self.data_type_handlers[data_type][device_model].handle_file
