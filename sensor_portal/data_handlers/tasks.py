from typing import List

from sensor_portal.celery import app


@app.task(name="data_handler_generate_thumbnails")
def generate_thumbnails(file_pks: List[int]) -> None:
    """
    Celery task to generate thumbnails for a list of DataFile primary keys.

    This task triggers the thumbnail generation function for each file,
    updates the deployment's thumbnail URL for affected deployments, and
    performs a bulk update to save the new thumbnail URLs.

    Args:
        file_pks (List[int]): List of primary keys for DataFile objects.
    """
    from data_models.models import DataFile, Deployment

    from .functions import generate_thumbnail
    from .post_upload_task_handler import post_upload_task_handler
    post_upload_task_handler(file_pks, generate_thumbnail)

    deployment_pk = DataFile.objects.filter(pk__in=file_pks).values_list(
        'deployment__pk', flat=True).distinct()
    deployment_objs = Deployment.objects.filter(pk__in=deployment_pk)
    for deployment_obj in deployment_objs:
        deployment_obj.set_thumb_url()

    Deployment.objects.bulk_update(deployment_objs, ["thumb_url"])
