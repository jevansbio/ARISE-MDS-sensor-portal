# DeviceModel

**Description:**  
Represents a type of device, its manufacturer, and data type.

### Fields

| Field         | Type          | Description                                                                 |
|---------------|---------------|-----------------------------------------------------------------------------|
| `created_on`  | DateTimeField | Auto timestamp on object creation.                                          |
| `modified_on` | DateTimeField | Auto timestamp on every save.                                               |
| `name`        | CharField     | Name of device model. Used to find a data handler if available.             |
| `manufacturer`| CharField     | Device model manufacturer.                                                  |
| `type`        | ForeignKey    | Primary data type of device.                                                |
| `owner`       | ForeignKey    | User who registered this device model.                                      |
| `colour`      | ColorField    | Override data type colour. Leave blank to use the default from data type.   |
| `symbol`      | IconField     | Override data type symbol. Leave blank to use the default from data type.   |

### Methods

- **`__str__()`**: Returns the name of the device model.
