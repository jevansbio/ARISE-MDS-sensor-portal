import logging

from django.conf import settings
from django.db.models.signals import (m2m_changed, post_delete, post_save,
                                      pre_delete)
from django.dispatch import receiver
from user_management.models import User
from utils.perm_functions import cascade_permissions

from .models import DataFile, DataType, Deployment, Device, Project

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Project)
@receiver(post_save, sender=Device)
def post_save_permission_cascade(sender, instance: Device | Project, created, **kwargs):
    """
    Post save signal for projects and devices, ensuring that they cascade their permissions
    and that their attached deployments update their permissions.
    """
    cascade_permissions(instance)
    for deployment in instance.deployments.all():
        try:
            deployment.save()
        except Exception as e:
            logger.error(e)


@receiver(post_save, sender=Deployment)
def post_save_deploy(sender, instance: Deployment, created, **kwargs):
    """
    Post save signal for Deployment model to ensure that the global project
    is always associated with the deployment instance.
    Also cascade the permissions

    """

    global_project, added = Project.objects.get_or_create(
        project_ID=settings.GLOBAL_PROJECT_ID)

    if global_project not in instance.project.all():
        instance.project.add(global_project)


@receiver(m2m_changed, sender=Deployment.project.through)
def update_combo_project(sender, instance, action, reverse, *args, **kwargs):
    """
    Signal to update the deployment's project when the many-to-many
    relationship changes. This ensures that the combination project field is updated.

    """
    if (action == 'post_add' or action == 'post_remove') and not reverse:
        instance.save()


# @receiver(m2m_changed, sender=Project.managers.through)
# @receiver(m2m_changed, sender=Project.annotators.through)
# @receiver(m2m_changed, sender=Project.viewers.through)
# def update_project_permissions(sender, instance, action, reverse, *args, **kwargs):
#     print(sender, instance, action)
#     if (action == 'post_add' or action == 'post_remove') and not reverse:
#         cascade_permissions(instance)
#         for deployment in sender.deployments.all():
#             deployment.save()


# DataFile signals


@receiver(post_save, sender=DataFile)
def post_save_file(sender, instance: DataFile, created, **kwargs):
    """
    Post save signal for DataFile model to update the deployment's thumbnail URL.
    """
    if instance.deployment.thumb_url is not None and instance.deployment.thumb_url != "":
        instance.deployment.set_thumb_url()
        instance.deployment.save()


@receiver(pre_delete, sender=DataFile)
def pre_remove_file(sender, instance: DataFile, **kwargs):
    """
    Pre delete signal for DataFile model to clean up the attached file before deletion.

    """
    # deletes the attached file from data storage
    success = instance.clean_file(True)
    if not success:
        raise (
            Exception(f'Unable to delete datafile object {instance.file_name}'))


@receiver(post_delete, sender=DataFile)
def post_remove_file(sender, instance: DataFile, **kwargs):
    """
    Post delete signal for DataFile model to update the deployment's thumbnail URL after a file is deleted.
    """
    if instance.deployment.thumb_url is not None and instance.deployment.thumb_url != "":
        instance.deployment.set_thumb_url()
        instance.deployment.save()
