# Site

**Description:**  
Represents a site with a name and an optional short name. If `short_name` is blank, it defaults to the first 10 characters of `name`.

### Fields

| Field         | Type          | Description                              |
|---------------|---------------|------------------------------------------|
| `created_on`  | DateTimeField | Auto timestamp on object creation.       |
| `modified_on` | DateTimeField | Auto timestamp on every save.            |
| `name`        | CharField     | Site name.                               |
| `short_name`  | CharField     | Site short name.                         |

### Methods

- **`__str__()`**: Returns the site name.
- **`save()`**: Sets `short_name` from `name` if it is blank before saving.
