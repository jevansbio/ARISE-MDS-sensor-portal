
# TarFile

**Description:**  
Represents a compressed TAR archive containing related data files. Handles cleanup and deletion from local and remote storage.

## Fields

| Field           | Type           | Description                                                  |
|------------------|----------------|--------------------------------------------------------------|
| `name`           | CharField      | Filename of the TAR archive (no extension).                  |
| `archived_dt`    | DateTimeField  | Date and time when this TAR was archived.                    |
| `uploading`      | BooleanField   | Whether the TAR is currently being uploaded.                 |
| `local_storage`  | BooleanField   | True if stored locally.                                      |
| `archived`       | BooleanField   | True if stored on remote archive.                            |
| `path`           | CharField      | File system path to the TAR archive.                         |
| `archive`        | ForeignKey     | Associated archive for this TAR.                             |

## Methods

- **`__str__()`**: Returns the name of the TAR file.
- **`clean_tar(delete_obj=False, force_delete=False)`**: Removes the TAR file from local or remote storage and updates its record.

## Signals

- **`pre_remove_tar`**: Cleans the TAR before deletion; raises error if cleanup fails.
