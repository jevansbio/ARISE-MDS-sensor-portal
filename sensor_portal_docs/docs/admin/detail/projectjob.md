# ProjectJob

**Description:**  
Represents a project-level job configuration.

### Fields

| Field             | Type          | Description                                  |
|------------------|---------------|----------------------------------------------|
| `created_on`      | DateTimeField | Auto timestamp on object creation.           |
| `modified_on`     | DateTimeField | Auto timestamp on every save.                |
| `job_name`        | CharField     | Name of job.                                 |
| `celery_job_name` | CharField     | Name of registered Celery task.              |
| `job_args`        | JSONField     | Additional arguments.                        |

### Methods

- **`__str__()`**: Returns the job name.
- **`get_job_signature(file_pks)`**: Generate a job signature for a Celery task given a list of file primary keys.
