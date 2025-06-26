
## Creating and Running Custom Jobs

You can define your own reusable and generic jobs by using the utility functions provided in `job_handling_functions.py`. These are designed to simplify registering, managing, and triggering asynchronous Celery tasks.

### Step 1: Register Your Task Using `@register_job`

Use the `@register_job` decorator to register your function as a job. This makes the task discoverable and executable via the job framework.

```python
from data_models.job_handling_functions import register_job
from celery import shared_task

@shared_task(name="my_custom_task")
@register_job(
    name="My Custom Task",
    task_name="my_custom_task",
    task_data_type="datafile",  # or "deployment", etc.
    task_admin_only=False,
    default_args={"some_arg": "default_value"}
)
def my_custom_task(datafile_pks: list[int], some_arg: str = "", **kwargs):
    # Your logic here
    pass
```

### Step 2: Trigger the Job Programmatically

Use `start_job_from_name` to run the task with a list of object primary keys and any arguments your job requires.

```python
from data_models.job_handling_functions import start_job_from_name

success, message, status_code = start_job_from_name(
    job_name="my_custom_task",
    obj_type="datafile",
    obj_pks=[1, 2, 3],
    job_args={"some_arg": "my value"},
    user_pk=5  # optional
)
```

### Optional: Build a Task Signature Only

If you want to build the task without executing it immediately, use `get_job_from_name`:

```python
from data_models.job_handling_functions import get_job_from_name

signature = get_job_from_name(
    job_name="my_custom_task",
    obj_type="datafile",
    obj_pks=[1, 2, 3],
    job_args={"some_arg": "value"},
    user_pk=5
)
signature.apply_async()  # Execute it later
```

This method is implemented by the `ProjectJob` objects to execute automated tasks associated with Projects.

### Default Arguments

The `default_args` dictionary in `@register_job` defines fallback values if a specific argument is not passed during execution. You can use this to ensure tasks have safe defaults.

---

## Example: Modifying DataFiles

Here's a simple example that sets a flag on DataFiles:

```python
@shared_task(name="flag_custom")
@register_job("Flag custom", "flag_custom", "datafile", True, default_args={"custom_flag": True})
def flag_custom(datafile_pks: list[int], custom_flag: bool = False, **kwargs):
    from .models import DataFile
    file_objs = DataFile.objects.filter(pk__in=datafile_pks)
    file_objs.update(my_custom_flag=custom_flag)
```

To run it:

```python
start_job_from_name(
    "flag_custom",
    "datafile",
    [101, 102],
    {"custom_flag": True},
    user_pk=1
)
```

---

## Notes

- `task_name` must be unique across the system.
- Only registered jobs are callable via `start_job_from_name`.
- Admin-only tasks can be restricted by setting `task_admin_only=True`.
- Max items per job can be controlled with the `max_items` parameter.