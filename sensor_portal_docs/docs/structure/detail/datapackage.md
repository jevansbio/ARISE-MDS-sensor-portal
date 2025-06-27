# DataPackage

**Description:**  
Model representing a data package, containing files and metadata for download or processing.

### Fields

| Field             | Type            | Description                                                       |
|------------------|------------------|-------------------------------------------------------------------|
| `created_on`      | DateTimeField   | Auto timestamp on object creation.                                |
| `modified_on`     | DateTimeField   | Auto timestamp on every save.                                     |
| `name`            | CharField       | The name of the data package.                                     |
| `data_files`      | ManyToManyField | The data files included in this package.                          |
| `owner`           | ForeignKey      | The user who owns this data package.                              |
| `status`          | IntegerField    | The current status of the data package.                           |
| `metadata_type`   | IntegerField    | The type of metadata associated with this package.                |
| `includes_files`  | BooleanField    | Whether the package includes files.                               |
| `file_url`        | CharField       | URL to download the zipped data package.                          |

### Methods

- **`__str__()`**: Returns the name of the data package.
- **`set_file_url()`**: Sets the `file_url` if the package is marked as ready.
- **`make_zip()`**: Creates a ZIP archive of the data files and updates status.
- **`save()`**: Overrides save to update `file_url` before saving.
- **`clean_data_package()`**: Removes the ZIP file from storage if ready or failed.

### Signals

- **`pre_delete`**: Cleans up the ZIP archive before the data package is deleted.
