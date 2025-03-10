from datetime import datetime, timedelta

from celery import shared_task
from django.db.models import DurationField, ExpressionWrapper, F

from .models import DataFile, Project


@shared_task
def clean_all_files():
    """
    Remove files that are archived and have not been modified in the projects clean time.
    """

    projects_to_clean = Project.objects.filter(archive___isnull=False)
    for project in projects_to_clean:
        clean_time = project.clean_time
        files_to_clean = DataFile.objects.filter(archived=True,
                                                 do_not_remove=False,
                                                 favourite_of__isnull=True,
                                                 deployment_last_image__isnull=True)
        files_to_clean = files_to_clean.annotate(file_age=ExpressionWrapper(
            datetime.now().date() - F('modified_on__date'), output_field=DurationField()))
        files_to_clean = files_to_clean.filter(
            file_age__gt=timedelta(days=clean_time))
        for file in files_to_clean:
            file.clean()
