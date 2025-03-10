from celery import shared_task


@shared_task(name="data_handler_generate_thumbnails")
def generate_thumbnails(file_names):
    from data_models.models import DataFile, Deployment

    from .functions import generate_thumbnail
    from .post_upload_task_handler import post_upload_task_handler
    post_upload_task_handler(file_names, generate_thumbnail)
    deployment_pk = DataFile.objects.values_list(
        'deployment__pk', flat=True).distinct()
    deployment_objs = Deployment.objects.filter(pk__in=deployment_pk)
    for deployment_obj in deployment_objs:
        deployment_obj.set_thumb_url()

    Deployment.objects.bulk_update(deployment_objs, ["thumb_url"])
