# DataType

**Description:**  
Describes a type of data, including its name, color, and optional icon.

### Fields

| Field         | Type          | Description                                  |
|---------------|---------------|----------------------------------------------|
| `created_on`  | DateTimeField | Auto timestamp on object creation.           |
| `modified_on` | DateTimeField | Auto timestamp on every save.                |
| `name`        | CharField     | Name of data type.                           |
| `colour`      | ColorField    | Colour to use for this data type.            |
| `symbol`      | IconField     | Symbol to use for this data type.            |

### Methods

- **`__str__()`**: Returns the name of the data type.
