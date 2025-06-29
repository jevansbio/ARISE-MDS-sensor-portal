from sensor_portal.celery import app


@app.task()
def check_external_storage_input_task(storage_pk: int, remove_bad: bool = False):
    """
    Celery task to check the input for a specific DataStorageInput instance.

    Args:
        storage_pk (int): Primary key of the DataStorageInput instance to check.
    """
    from .models import DataStorageInput
    storage = DataStorageInput.objects.get(pk=storage_pk)
    storage.check_input(remove_bad)


@app.task()
def check_external_storage_users_task(storage_pk: int):
    """
    Celery task to set up users for a specific DataStorageInput instance.

    Args:
        storage_pk (int): Primary key of the DataStorageInput instance for user setup.
    """
    from .models import DataStorageInput
    storage = DataStorageInput.objects.get(pk=storage_pk)
    storage.setup_users()


@app.task()
def check_external_storage_all_task(storage_pk: int, remove_bad: bool = False):
    """
    Celery task to perform a full check on a specific DataStorageInput instance.

    Args:
        storage_pk (int): Primary key of the DataStorageInput instance to check.
    """
    from .models import DataStorageInput
    storage = DataStorageInput.objects.get(pk=storage_pk)
    storage.check_users_input(remove_bad=remove_bad)
