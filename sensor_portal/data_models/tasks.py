import logging
from datetime import datetime, timedelta
from typing import List

from bridgekeeper import perms
from celery import shared_task
from data_models.job_handling_functions import register_job
from django.contrib.sites.models import Site
from django.db.models import (BooleanField, DurationField, ExpressionWrapper,
                              F, IntegerField, Max, Q)
from django.db.models.functions import ExtractHour
from django.utils import timezone
from user_management.models import User
from utils.email import send_email_to_user

from sensor_portal.celery import app

from .models import DataFile, Deployment, Device, Project

logger = logging.getLogger(__name__)


@app.task(name="end_deployments")
@register_job("End deployments", "end_deployments", "deployment", True, default_args={})
def end_deployments(deployment_pks: List[int], no_delete: bool = False, **kwargs):
    """
    Mark the specified deployments as ended.

    Args:
        deployment_pks (List[int]): List of primary keys for Deployment objects to update.
        no_delete (bool, optional): Unused in this function. Defaults to False.
        **kwargs: Additional keyword arguments (unused).

    This function sets the 'deployment_end' field to the current time and marks the deployments as inactive.
    """
    deployment_objs = Deployment.objects.filter(
        pk__in=deployment_pks, deployment_end=None)
    logger.info(deployment_objs.count())
    deployment_objs.update(deployment_end=timezone.now(), is_active=False)


@app.task(name="set_tag")
@register_job("Set tag", "set_tag", "datafile", True, default_args={"new_tag": ""})
def set_tag_task(datafile_pks: List[int], new_tag: str = "", **kwargs):
    """
    Set a tag on specified DataFile objects.

    Args:
        datafile_pks (List[int]): List of primary keys for DataFile objects to update.
        new_tag (str): Value to set for the 'tag' field. Defaults to an empty string.
        **kwargs: Additional keyword arguments (unused).

    Updates each DataFile's 'do_not_remove' attribute to the provided value.
    """
    file_objs = DataFile.objects.filter(pk__in=datafile_pks)
    logger.info(file_objs.count())
    file_objs.update(tag=new_tag)


@app.task(name="flag_no_delete")
@register_job("Change no delete flag", "flag_no_delete", "datafile", True, default_args={"no_delete": True})
def flag_no_delete(datafile_pks: List[int], no_delete: bool = False, **kwargs):
    """
    Set or unset the 'do_not_remove' flag for specified DataFile objects.

    Args:
        datafile_pks (List[int]): List of primary keys for DataFile objects to update.
        no_delete (bool, optional): Value to set for the 'do_not_remove' flag. Defaults to False.
        **kwargs: Additional keyword arguments (unused).

    Updates each DataFile's 'do_not_remove' attribute to the provided value.
    """
    file_objs = DataFile.objects.filter(pk__in=datafile_pks)
    logger.info(file_objs.count())
    file_objs.update(do_not_remove=no_delete)


@app.task(name="flag_humans")
@register_job("Change human flag", "flag_humans", "datafile", True, default_args={"has_human": False})
def flag_humans(datafile_pks: List[int], has_human: bool = False, **kwargs):
    """
    Set or unset the 'has_human' flag for specified DataFile objects.

    Args:
        datafile_pks (List[int]): List of primary keys for DataFile objects to update.
        has_human (bool, optional): Value to set for the 'has_human' flag. Defaults to False.
        **kwargs: Additional keyword arguments (unused).

    Updates each DataFile's 'has_human' attribute to the provided value.
    """
    file_objs = DataFile.objects.filter(pk__in=datafile_pks)
    logger.info(file_objs.count())
    file_objs.update(has_human=has_human)


@app.task()
def clean_all_files():
    """
    Remove files from local storage that are archived and have not been modified within the project's clean time.

    This task iterates through all projects with an archive, identifies eligible files based on modification date
    and various flags, and removes them using the DataFile.clean_file() method.
    """
    projects_to_clean = Project.objects.filter(archive__isnull=False)
    logger.info(f"Found {projects_to_clean.count()} projects to clean.")
    for project in projects_to_clean:
        clean_time = project.clean_time
        logger.info(
            f"Cleaning project: {project.name} with clean time: {clean_time} days.")
        files_to_clean = DataFile.objects.filter(
            local_storage=True,
            archived=True,
            do_not_remove=False,
            favourite_of__isnull=True,
            deployment_last_image__isnull=True
        )

        files_to_clean = files_to_clean.annotate(file_age=ExpressionWrapper(
            timezone.now().date() - F('modified_on__date'), output_field=DurationField()))
        files_to_clean = files_to_clean.filter(
            file_age__gt=timedelta(days=clean_time))
        logger.info(
            f"Found {files_to_clean.count()} files to clean for project: {project.name}.")
        for file in files_to_clean:
            try:
                logger.info(f"Cleaning file: {file.file_name} (ID: {file.pk})")
                file.clean_file()
            except Exception as e:
                logger.info(
                    f"Error cleaning file {file.file_name} (ID: {file.pk}): {e}")


@app.task()
def check_deployment_active():
    """
    Update the active status of deployments based on their start and end times.

    - Activates deployments that should be active (start time has passed, end time not yet reached).
    - Deactivates deployments that should be inactive (start time not yet reached, or end time passed).

    This task ensures the 'is_active' status and 'modified_on' timestamp are up-to-date.
    """
    # Get all deployments that are inactive that should be active
    make_active = Deployment.objects.filter(
        is_active=False,
        deployment_start__lte=timezone.now(),
    ).filter(Q(deployment_end__isnull=True) | Q(deployment_end__gte=timezone.now()))

    make_active.update(is_active=True, modified_on=timezone.now())

    # Get all deployments that are active that should be inactive
    make_inactive = Deployment.objects.filter(
        is_active=True,
    ).filter(Q(deployment_start__gte=timezone.now()) | Q(deployment_end__lte=timezone.now()))

    make_inactive.update(is_active=False, modified_on=timezone.now())


@app.task()
def check_device_status():
    """
    Check whether devices have transmitted data within their allotted update interval and notify managers if not.

    For each device with active deployments and autoupdate enabled, this task checks the age of the most recent data file.
    If a device has not transmitted within its expected update period, managers responsible for the device receive an email notification.
    """
    logger.info("Checking device status...")

    auto_devices = Device.objects.filter(
        deployments__is_active=True,
        autoupdate=True,
    )

    logger.info(f"Checking device status for {auto_devices.count()}")

    bad_devices_pks = []
    bad_devices_values = []
    for device in auto_devices:
        logger.info(f"Device {device.device_ID} checking...")
        # get the last file time for each device
        last_file_time = device.deployments.filter(is_active=True).aggregate(
            Max('files__recording_dt')).get('files__recording_dt__max')
        if last_file_time is None:
            logger.info(f"Device {device.device_ID} has no files.")
            bad_devices_pks.append(device.pk)
            bad_devices_values.append({
                'device_ID': device.device_ID,
                'name': device.name,
                'file_hours': None
            })
            continue
        # calculate the age of the last file
        file_age = timezone.now() - last_file_time
        # check if the file age is greater than the update time
        if file_age > timedelta(hours=device.update_time):
            logger.info(
                f"Device {device.device_ID} has not transmitted in the allotted time: {file_age.total_seconds() / 3600} hours.")
            # add the device to the list of bad devices
            bad_devices_pks.append(device.pk)
            bad_devices_values.append({
                'pk': device.pk,
                'device_ID': device.device_ID,
                'name': device.name,
                'file_hours': file_age.total_seconds() / 3600  # convert to hours
            })

    bad_devices = Device.objects.filter(pk__in=bad_devices_pks)
    logger.info(f"Found {len(bad_devices_pks)}  bad devices.")
    # get all unique managers
    all_bad_device_users = User.objects.filter(
        deviceuser__isnull=True, is_active=True).filter(
        Q(managed_projects__deployments__device__in=bad_devices) |
        Q(managed_devices__in=bad_devices)
    ).distinct()

    for user in all_bad_device_users:
        logger.info(f"Getting bad devices for {user.username}")
        # for each manager, get their bad devices
        users_bad_devices = perms['data_models.change_device'].filter(
            user, bad_devices).distinct()
        logger.info(f"Got bad devices for {user.username}")
        if not users_bad_devices.exists():
            continue
        # get PKs
        user_bad_device_pks = users_bad_devices.values_list('pk', flat=True)
        device_list = [
            f'{x.get("device_ID")} - {x.get("name")} - {x.get("file_hours")}' for x in bad_devices_values if x.get('pk') in user_bad_device_pks]
        device_list_string = " \n".join(device_list)
        logger.info(f"Got bad device info for {user.username}")

        # send them an email
        email_body = f"""
        Dear {user.first_name} {user.last_name},\n
        \n
        The following devices which you manage have not transmitted in their allotted time: \n
        {device_list_string}
        """

        send_email_to_user(
            user,
            subject=f"{Site.objects.get_current().name} - {users_bad_devices.count()} devices have not transmitted in allotted time",
            body=email_body
        )
