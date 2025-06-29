
# Archive

**Description:**  
Represents a remote archive storage system used for storing TAR files of collected data.

## Fields

| Field         | Type               | Description                                                  |
|---------------|--------------------|--------------------------------------------------------------|
| `name`        | CharField          | Human-readable name for the archive.                         |
| `username`    | CharField          | SSH login username.                                          |
| `password`    | EncryptedCharField | Encrypted SSH login password.                                |
| `address`     | CharField          | Network address of the archive server.                       |
| `owner`       | ForeignKey         | User who owns this archive.                                  |
| `root_folder` | CharField          | Root folder path on the archive server.                      |

## Methods

- **`__str__()`**: Returns the archive name.
- **`init_ssh_client()`**: Initializes an SSH client for this archive.
- **`check_projects()`**: Invokes logic to check and sync archive projects.
- **`check_upload()`**: Invokes logic to validate and upload files.
