# Device

**Description:**  
Represents a physical device or sensor.

### Fields

| Field           | Type            | Description                                                                 |
|------------------|------------------|-----------------------------------------------------------------------------|
| `created_on`     | DateTimeField   | Auto timestamp on object creation.                                          |
| `modified_on`    | DateTimeField   | Auto timestamp on every save.                                               |
| `device_ID`      | CharField       | Unique identifier for device, such as a serial number.                      |
| `name`           | CharField       | Optional alternative name for device.                                       |
| `model`          | ForeignKey      | Device model.                                                               |
| `type`           | ForeignKey      | Device type, usually inherited from model.                                  |
| `owner`          | ForeignKey      | Device owner.                                                               |
| `managers`       | ManyToManyField | Device managers.                                                            |
| `viewers`        | ManyToManyField | Device viewers.                                                             |
| `annotators`     | ManyToManyField | Device annotators.                                                          |
| `autoupdate`     | BooleanField    | Is the device expected to autoupdate?                                       |
| `update_time`    | IntegerField    | Hours between expected updates.                                             |
| `username`       | CharField       | Device username for use with external storage.                              |
| `password`       | EncryptedCharField | Device password for use with external storage.                            |
| `input_storage`  | ForeignKey      | External storage for device.                                                |
| `extra_data`     | JSONField       | Extra data that doesn't fit in existing fields.                             |

### Methods

- **`is_active()`**: Returns `True` if the device has at least one active deployment.
- **`__str__()`**: Returns the device ID.
- **`get_absolute_url()`**: Returns the URL to view this device.
- **`save()`**: Sets the type from the model if not explicitly set.
- **`clean()`**: Validates that the device type matches the model's type.
- **`deployment_from_date(dt)`**: Returns the deployment for this device active at the given datetime.
- **`check_overlap(new_start, new_end, deployment_pk)`**: Checks for overlapping deployments in the given date range, excluding a given deployment.
