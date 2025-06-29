# Data handlers

A data handler is a generic class for handling data from different sensor models in different ways. These are read on startup and used by the file import functionality.

### Attributes
- data_types: A list of `DataType__name`s that the handler supports e.g. `["wildlifecamera"]`
- device_models: A list of `DeviceType__name`s that the handler supports e.g `["default","BadgerCamera9000"]`
- safe_formats: A list of save file formats that the handler will deal with e.g. `[".jpg"]`
- full_name: Name of the data handler.
- description: HTML general description of the handler.
- validity_description: HTML description of the validity checks the handler makes.
- handling_description:  HTML description of how the files are handled.
- post_handling_description: HTML description of post-upload tasks run on the file.

## Methods to override.

#### handle_file(file, recording_dt=None, extra_data=None, data_type=None)
Handle a file after download, performing any post-processing or validation. The method is expected to return:

- DateTime of when the file was recorded `recording_dt`.

- Dict of `extra_data` including any extra information that might be important that does not fit into the pre-defined database columns.

- String of `data_type__name`, in case the handler overrides the default datatype of the deployment, e.g. a camera that takes both motion detected and timelapse images.

- String of a post-download celery task that will be carried out when the import is complete. This is typically returned by the `get_post_download_task` method.

#### get_post_download_task(file_extension, first_time=True)
Returns the name of a post download celery task.

#### get_valid_files(files, device_label=None)
Return a list of files filtered by custom validity checks.

## Creating a custom data handler

1. **Create a new handler class** in your handlers directory.

```python
from datetime import datetime
from typing import Tuple

from data_handlers.base_data_handler_class import DataTypeHandler

class CustomFileHandler(DataTypeHandler):
    data_types = ["mydatatype"]
    device_models = ["mydevice"]
    safe_formats = [".txt", ".csv"]
    full_name = "My Custom File Handler"
    description = "Handles custom text or CSV files."
    validity_description = "Files must be .txt or .csv."
    handling_description = "Parses text files to extract structured data."
    post_handling_description = "Triggers downstream processing tasks if needed."

    def handle_file(self, file, recording_dt: datetime = None, extra_data: dict = None, data_type: str = None) -> Tuple[datetime, dict, str, str]:
        # Call base handler
        recording_dt, extra_data, data_type, task = super().handle_file(file, recording_dt, extra_data, data_type)

        # Add custom file parsing logic here
        with open(file.path, 'r') as f:
            content = f.read()
            extra_data['line_count'] = content.count('\n')

        return recording_dt, extra_data, data_type, task

    def get_post_download_task(self, file_extension: str, first_time: bool = True):
        # Return a task name for post-download processing
        return "data_handler_run_analysis"
```

2. **Register the handler**

Ensure your handler module is located in the `data_handlers/handlers/` directory.  
The `DataTypeHandlerCollection` class automatically discovers and instantiates all subclasses of `DataTypeHandler`.

3. **Use in processing**

The `DataTypeHandlerCollection` will route files to your custom handler based on `data_type` and `device_model`.

Example:

```python
handler_collection = DataTypeHandlerCollection()
handler = handler_collection.get_handler("mydatatype", "mydevice")
valid_files = handler.get_valid_files(uploaded_files)
```

### Example Reference: `DefaultImageHandler`

The `DefaultImageHandler` class demonstrates subclassing to handle `.jpg`, `.jpeg`, and `.png` image files.  
It overrides:

- `handle_file` to extract EXIF metadata
- `get_post_download_task` to specify the task `"data_handler_generate_thumbnails"`

You can follow a similar structure to implement your own custom logic.

## Using `post_upload_task_handler` as a Wrapper

The `post_upload_task_handler` is a utility function designed to apply a custom task function to a list of `DataFile` instances after upload. It ensures each file is safely locked during processing and restored to its original state afterward.

### Purpose

- To perform post-upload operations (e.g. metadata extraction, file transformation) on a list of files.
- To isolate errors so one file’s failure doesn’t affect the rest.
- To safely toggle the `do_not_remove` flag on each file during processing.

### Signature

```python
post_upload_task_handler(
    file_pks: List[int],
    task_function: Callable[[DataFile], Tuple[DataFile | None, List[str] | None]]
) -> None
```

### How to Use

1. **Define your task function:**

```python
def my_custom_task(data_file: DataFile) -> Tuple[DataFile, List[str]]:
    # perform some logic on the data_file
    data_file.custom_field = "Updated"
    return data_file, ["custom_field"]
```

2. **Call post_upload_task_handler with file PKs and your function::**
```python
file_pks = [1, 2, 3]
post_upload_task_handler(file_pks, my_custom_task)

```


