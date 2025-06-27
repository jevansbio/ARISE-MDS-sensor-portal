# Deployment

**Description:**  
Records a deployment of a device to a site, within a project.

### Fields

| Field                  | Type              | Description                                                                 |
|------------------------|-------------------|-----------------------------------------------------------------------------|
| `created_on`           | DateTimeField     | Auto timestamp on object creation.                                          |
| `modified_on`          | DateTimeField     | Auto timestamp on every save.                                               |
| `deployment_device_ID` | CharField         | Unique identifier combining `deployment_ID`, `device_type`, and `device_n`. |
| `deployment_ID`        | CharField         | An identifier for a deployment.                                             |
| `device_type`          | ForeignKey        | Primary data type of deployment.                                            |
| `device_n`             | IntegerField      | Numeric suffix for disambiguating deployments with the same ID/type.        |
| `deployment_start`     | DateTimeField     | Start datetime of deployment.                                               |
| `deployment_end`       | DateTimeField     | End datetime of deployment. Can be NULL for ongoing deployments.            |
| `device`               | ForeignKey        | Device used in this deployment.                                             |
| `site`                 | ForeignKey        | Site where the deployment takes place.                                      |
| `project`              | ManyToManyField   | Projects to which this deployment is attached.                              |
| `latitude`             | DecimalField      | Latitude of deployment.                                                     |
| `longitude`            | DecimalField      | Longitude of deployment.                                                    |
| `point`                | PointField        | Spatial point representing this deployment.                                 |
| `extra_data`           | JSONField         | Extra data that doesn't fit in other fields.                                |
| `is_active`            | BooleanField      | Whether the deployment is currently active.                                 |
| `time_zone`            | TimeZoneField     | Time zone for this deployment.                                              |
| `owner`                | ForeignKey        | Owner of deployment.                                                        |
| `managers`             | ManyToManyField   | Managers of deployment.                                                     |
| `viewers`              | ManyToManyField   | Viewers of deployment.                                                      |
| `annotators`           | ManyToManyField   | Annotators of deployment.                                                   |
| `combo_project`        | CharField         | Combined project identifiers string.                                        |
| `last_image`           | ForeignKey        | Last image (if any) linked to this deployment.                              |
| `thumb_url`            | CharField         | Deployment thumbnail URL.                                                   |

### Methods

- **`get_absolute_url()`**: Returns the URL to this deployment's detail page.
- **`__str__()`**: Returns the `deployment_device_ID`.
- **`clean()`**: Validates deployment start/end time and checks for overlapping deployments.
- **`save()`**: Sets fields such as `deployment_device_ID`, `is_active`, `point`, and `combo_project`.
- **`get_permissions()`**: Propagates permissions from the device and project.
- **`get_combo_project()`**: Returns a space-separated string of sorted project IDs.
- **`check_active()`**: Returns `True` if the deployment is currently active.
- **`check_dates(dt_list)`**: Returns a list indicating whether each datetime falls within the deployment range.
- **`set_thumb_url()`**: Sets the thumbnail URL and last image for the deployment.
