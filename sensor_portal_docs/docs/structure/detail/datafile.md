# DataFile

**Description:**  
Represents a data file associated with a deployment.

### Fields

| Field             | Type              | Description                                                                |
|------------------|-------------------|----------------------------------------------------------------------------|
| `created_on`      | DateTimeField     | Auto timestamp on object creation.                                         |
| `modified_on`     | DateTimeField     | Auto timestamp on every save.                                              |
| `deployment`      | ForeignKey        | Deployment to which this data file is linked.                              |
| `file_type`       | ForeignKey        | Data type of the file.                                                     |
| `file_name`       | CharField         | File name.                                                                 |
| `file_size`       | FileSizeField     | Size of file in bytes.                                                     |
| `file_format`     | CharField         | File extension.                                                            |
| `upload_dt`       | DateTimeField     | Datetime when the file was uploaded.                                       |
| `recording_dt`    | DateTimeField     | Datetime when the file was recorded.                                       |
| `path`            | CharField         | Relative path.                                                             |
| `local_path`      | CharField         | Absolute path on local storage.                                            |
| `extra_data`      | JSONField         | Extra data that does not fit in existing columns.                          |
| `linked_files`    | JSONField         | Linked files such as alternative representations.                          |
| `thumb_url`       | CharField         | Thumbnail URL.                                                             |
| `local_storage`   | BooleanField      | Whether the file is available on local storage.                            |
| `archived`        | BooleanField      | Whether the file has been archived.                                        |
| `tar_file`        | ForeignKey        | TAR file containing this file.                                             |
| `favourite_of`    | ManyToManyField   | Users who have favourited this file.                                       |
| `do_not_remove`   | BooleanField      | If True, the file will not be removed during cleaning.                     |
| `original_name`   | CharField         | Original name of the file.                                                 |
| `file_url`        | CharField         | URL of this file.                                                          |
| `tag`             | CharField         | Additional identifying tag of this file.                                   |
| `has_human`       | BooleanField      | True if this image has been annotated with a human.                        |

### Methods

- **`__str__()`**: Returns the full file name.
- **`get_absolute_url()`**: Returns the URL to this file.
- **`add_favourite(user)`**: Adds a user to the list of favourites.
- **`remove_favourite(user)`**: Removes a user from the list of favourites.
- **`full_path()`**: Returns the full path to this file.
- **`thumb_path()`**: Returns the thumbnail path.
- **`set_file_url()`**: Sets the URL for this file.
- **`set_linked_files_urls()`**: Sets URLs for linked file representations.
- **`set_thumb_url(has_thumb=True)`**: Sets or clears the thumbnail URL.
- **`check_human()`**: Updates the `has_human` flag based on associated observations.
- **`clean_file(delete_obj=False, force_delete=False)`**: Cleans up file and resources.
- **`save()`**: Assigns `file_type`, sets file URL, and saves.
- **`clean()`**: Validates file against deployment date range.
