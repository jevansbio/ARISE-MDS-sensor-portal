
# DataStorageInput

**Description:**  
Represents a remote data storage input used for importing sensor data. Stores access credentials and manages linked user accounts and data files.

## Fields

| Field       | Type              | Description                                                  |
|-------------|-------------------|--------------------------------------------------------------|
| `name`      | CharField         | A unique name for this data storage input.                  |
| `username`  | CharField         | Username for accessing the external storage.                |
| `password`  | EncryptedCharField| Encrypted password for the storage username.                |
| `address`   | CharField         | Network address (IP or hostname) of the storage.            |
| `owner`     | ForeignKey        | User who owns this data storage input.                      |

## Methods

- **`__str__()`**: Returns the name of the storage input.
- **`init_ssh_client()`**: Initializes and returns an SSH client for this storage input.
- **`check_users_input()`**: Sets up users and verifies access for linked devices.
- **`setup_users()`**: Ensures required user accounts exist on the storage system.
- **`check_connection()`**: Attempts to connect and returns connection status and client.
- **`check_input(remove_bad=False)`**: Checks and optionally cleans files on storage.
