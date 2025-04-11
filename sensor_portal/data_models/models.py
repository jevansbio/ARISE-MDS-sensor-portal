import os
import traceback
from datetime import datetime, time, timedelta, timezone
from threading import local
from unittest import TextTestRunner

from archiving.models import Archive, TarFile
from bridgekeeper import perms
from django.conf import settings
from django.contrib.auth.models import Group
from django.contrib.gis.db import models as gis_models
from django.contrib.gis.geos import Point
from django.core.exceptions import (MultipleObjectsReturned,
                                    ObjectDoesNotExist, ValidationError)
from django.db import models
from django.db.models import (BooleanField, Case, DateTimeField,
                              ExpressionWrapper, F, Max, Min, Q, Sum, Value,
                              When)
from django.db.models.signals import (m2m_changed, post_delete, post_save,
                                      pre_delete)
from django.dispatch import receiver
from django.urls import reverse
from django.utils import timezone as djtimezone
from encrypted_model_fields.fields import EncryptedCharField
from external_storage_import.models import DataStorageInput
from sizefield.models import FileSizeField
from timezone_field import TimeZoneField
from utils.general import convert_unit
from utils.models import BaseModel

from . import validators
from .general_functions import check_dt


class Site(BaseModel):
    name = models.CharField(max_length=50)
    short_name = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.short_name == "":
            self.short_name = self.name[0:10]
        return super().save(*args, **kwargs)


class DataType(BaseModel):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class Project(BaseModel):
    # Metadata
    project_ID = models.CharField(max_length=50, unique=True, blank=True)
    name = models.CharField(max_length=50)

    objectives = models.CharField(max_length=500, blank=True)
    principal_investigator = models.CharField(max_length=50, blank=True)
    principal_investigator_email = models.CharField(max_length=100, blank=True)
    contact = models.CharField(max_length=50, blank=True)
    contact_email = models.CharField(max_length=100, blank=True)
    organisation = models.CharField(max_length=100, blank=True)
    data_storages = models.ManyToManyField(
        DataStorageInput, related_name="linked_projects", blank=True)
    archive = models.ForeignKey(
        Archive, related_name="linked_projects", null=True, on_delete=models.SET_NULL)

    def is_active(self):
        if self.id:
            return self.deployments.filter(is_active=True).exists()
        else:
            return False

    # User ownership
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, related_name="owned_projects",
                              on_delete=models.SET_NULL, null=True)
    managers = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, related_name="managed_projects")
    viewers = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, related_name="viewable_projects")
    annotators = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, related_name="annotatable_projects")

    clean_time = models.IntegerField(default=90)

    def __str__(self):
        return self.project_ID

    def get_absolute_url(self):
        return reverse('project-detail', kwargs={'pk': self.pk})

    def save(self, *args, **kwargs):
        if self.project_ID == "" or self.project_ID is None:
            self.project_ID = self.name[0:10]
        return super().save(*args, **kwargs)

# @receiver(post_save, sender=Project)
# def post_save_project(sender, instance, created, **kwargs):
#     if created:
#         if instance.short_name == "":
#             instance.short_name = instance.name[:10]
#             instance.save()

        # viewer_groupname = f"{instance.projectID}_project_viewers"
        # viewer_usergroup = create_user_group(viewer_groupname)
        # viewer_usergroup_profile = viewer_usergroup.profile
        # viewer_usergroup_profile.project.add(instance)
        # viewer_usergroup_profile.save()

        # annotator_groupname = f"{instance.projectID}_project_annotators"
        # annotator_usergroup = create_user_group(annotator_groupname)
        # annotator_usergroup_profile = annotator_usergroup.profile
        # annotator_usergroup_profile.project.add(instance)
        # annotator_usergroup_profile.save()


class DeviceModel(BaseModel):
    name = models.CharField(max_length=50, blank=True, unique=True)
    manufacturer = models.CharField(max_length=50, blank=True)
    type = models.ForeignKey(DataType, models.PROTECT,
                             related_name="device_models")
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, related_name="owned_device_models",
                              on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.name


class Device(BaseModel):
    device_ID = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=50, blank=True)
    model = models.ForeignKey(
        DeviceModel, models.PROTECT, related_name="registered_devices")

    type = models.ForeignKey(DataType, models.PROTECT,
                             related_name="devices", null=True)

    # Device status and configuration fields
    device_status = models.CharField(max_length=50, blank=True, null=True)
    configuration = models.CharField(max_length=20, blank=True, null=True)
    sim_card_icc = models.CharField(max_length=50, blank=True, null=True)
    sim_card_batch = models.CharField(max_length=50, blank=True, null=True)
    sd_card_size = models.FloatField(help_text="Size in GB", blank=True, null=True)

    # User ownership
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, related_name="owned_devices",
                              on_delete=models.SET_NULL, null=True)
    managers = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, related_name="managed_devices")
    viewers = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, related_name="viewable_devices")
    annotators = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, related_name="annotatable_devices")
    
    # Device status fields
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    battery_level = models.FloatField(null=True, blank=True)

    # Making autoupdate optional to match the database schema
    autoupdate = models.BooleanField(default=False, null=True, blank=True)
    update_time = models.IntegerField(default=48, null=True, blank=True)

    username = models.CharField(
        max_length=100, unique=True, null=True, blank=True, default=None)
    
    input_storage = models.ForeignKey(
        DataStorageInput, null=True, blank=True, related_name="linked_devices", on_delete=models.SET_NULL)

    extra_data = models.JSONField(default=dict, blank=True, null=True)

    def is_active(self):
        if self.id:
            return self.deployments.filter(is_active=True).exists()
        else:
            return False

    def __str__(self):
        return self.device_ID

    def get_absolute_url(self):
        return f"/api/device/{self.pk}"

    def get_folder_size(self, unit="MB"):
        """
        Calculate the total size of all DataFile objects associated with this device.
        Filstørrelse antas å være lagret i MB som standard.
        Du kan spesifisere en annen enhet ved å sende 'KB' eller 'GB'.
        """
        agg = DataFile.objects.filter(deployment__device=self).aggregate(total_size=Sum('file_size'))
        total_size = agg['total_size'] or 0

        if unit.upper() == "KB":
            return total_size * 1024
        elif unit.upper() == "GB":
            return total_size / 1024
        return total_size

    def get_last_upload(self):
        """Get the datetime of the most recent file upload for this device"""
        all_files = DataFile.objects.filter(deployment__device=self)
        if all_files.exists():
            return all_files.aggregate(last_upload=models.Max('upload_dt'))['last_upload']
        return None
    
    def save(self, *args, **kwargs):
        if self.model and not self.type:
            self.type = self.model.type
        super().save(*args, **kwargs)

    def clean(self):
        result, message = validators.device_check_type(
            self.type, self.model)
        print(result, message)
        if not result:
            raise ValidationError(message)
        super(Device, self).clean()

    def deployment_from_date(self, dt):

        # print(dt)
        all_deploys = self.deployments.all()

        all_tz = all_deploys.values('time_zone', 'pk')

        all_tz = [{'time_zone': x.get(
            'time_zone', settings.TIME_ZONE), 'pk': x['pk']} for x in all_tz]

        all_dt = {x['pk']: check_dt(dt, x['time_zone']) for x in all_tz}

        whens = [When(pk=k, then=Value(v)) for k, v in all_dt.items()]

        all_deploys = all_deploys.annotate(
            dt=Case(*whens, output_field=DateTimeField(), default=Value(None)))

        # For deployments that have not ended - end date is shifted 100 years

        all_deploys = all_deploys.annotate(deployment_end_indefinite=Case(
            When(deployment_end__isnull=True,
                 then=ExpressionWrapper(
                     F('deployment_start') + timedelta(days=365 * 100),
                     output_field=DateTimeField()
                 )
                 ),
            default=F('deployment_end')
        )
        )

        # Annotate by whether the datetime lies in the deployment range

        all_deploys = all_deploys.annotate(in_deployment=ExpressionWrapper(
            Q(Q(deployment_start__lte=F('dt')) & Q(
                deployment_end_indefinite__gte=F('dt'))),
            output_field=BooleanField()
        )
        )

        try:
            correct_deployment = all_deploys.get(in_deployment=True)
            return correct_deployment
        except (ObjectDoesNotExist, MultipleObjectsReturned):
            # Check for complete failure or ambiguity
            all_true_deployments = all_deploys.filter(in_deployment=True)
            print(f"Error: found {all_true_deployments.count()} deployments")
            return None

    def check_overlap(self, new_start, new_end, deployment_pk):

        new_start = check_dt(new_start)
        if new_end is None:
            new_end = new_start + timedelta(days=365 * 100)
        else:
            new_end = check_dt(new_end)

        # print(deployment_pk)
        all_deploys = self.deployments.all().exclude(pk=deployment_pk)
        all_deploys = all_deploys.annotate(deployment_end_indefinite=Case(
            When(deployment_end__isnull=True,
                 then=ExpressionWrapper(
                     F('deployment_start') + timedelta(days=365 * 100),
                     output_field=DateTimeField()
                 )
                 ),
            default=F('deployment_end')
        )
        )
        # print(all_deploys.values('deployment_end', 'deployment_end_indefinite'))
        all_deploys = all_deploys.annotate(in_deployment=ExpressionWrapper(
            Q(Q(deployment_end_indefinite__gte=new_start)
              & Q(deployment_start__lte=new_end)),
            output_field=BooleanField()
        )
        )

        overlapping_deploys = all_deploys.filter(in_deployment=True)
        return list(overlapping_deploys.values_list('deployment_device_ID', flat=True))


# @receiver(post_save, sender=Device)
# def post_save_device(sender, instance, created, **kwargs):
#     if created:
#         viewer_groupname = f"{instance.projectID}_device_viewers"
#         viewer_usergroup = create_user_group(viewer_groupname)
#         viewer_usergroup_profile = viewer_usergroup.profile
#         viewer_usergroup_profile.project.add(instance)
#         viewer_usergroup_profile.save()

#         annotator_groupname = f"{instance.projectID}_device_annotators"
#         annotator_usergroup = create_user_group(annotator_groupname)
#         annotator_usergroup_profile = annotator_usergroup.profile
#         annotator_usergroup_profile.project.add(instance)
#         annotator_usergroup_profile.save()


class Deployment(BaseModel):
    deployment_device_ID = models.CharField(
        max_length=100, blank=True, editable=False, unique=True, null=True)
    deployment_ID = models.CharField(max_length=50)
    device_type = models.ForeignKey(
        DataType, models.PROTECT, related_name="deployments", null=True, blank=True)
    device_n = models.IntegerField(default=1)

    deployment_start = models.DateTimeField(default=djtimezone.now, blank=True, null=True)
    deployment_end = models.DateTimeField(blank=True, null=True)
    device = models.ForeignKey(Device, on_delete=models.PROTECT, related_name="deployments", null=True, blank=True)

    site = models.ForeignKey(Site, models.PROTECT, related_name="deployments", null=True, blank=True)
    project = models.ManyToManyField(
        Project, related_name="deployments", blank=True, null=True)

    latitude = models.DecimalField(
        max_digits=8, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(
        max_digits=8, decimal_places=6, blank=True, null=True)
    point = gis_models.PointField(
        blank=True,
        null=True,
        spatial_index=True
    )
    
    # Geo-related fields from form
    coordinate_uncertainty = models.CharField(max_length=100, blank=True, null=True)
    gps_device = models.CharField(max_length=100, blank=True, null=True)
    mic_height = models.FloatField(null=True, blank=True)
    mic_direction = models.CharField(max_length=100, blank=True, null=True)
    habitat = models.CharField(max_length=100, blank=True, null=True)
    protocol_checklist = models.CharField(max_length=255, blank=True, null=True)
    score = models.FloatField(null=True, blank=True)
    comment = models.TextField(blank=True, null=True)
    user_email = models.EmailField(blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    site_name = models.CharField(max_length=100, blank=True, null=True)
    
    # Device status fields for latest status in this deployment
    battery_level = models.FloatField(null=True, blank=True)

    # Making autoupdate optional to match the database schema
    # This field won't be queried if it doesn't exist in the database
    # Set both null and default to make it completely optional
    autoupdate = models.BooleanField(default=False, null=True, blank=True)
    update_time = models.IntegerField(default=48, null=True, blank=True)

    username = models.CharField(
        max_length=100, unique=True, null=True, blank=True, default=None)
    input_storage = models.ForeignKey(
        DataStorageInput, null=True, blank=True, related_name="linked_deployments", on_delete=models.SET_NULL)

    extra_data = models.JSONField(default=dict, blank=True, null=True)
    is_active = models.BooleanField(default=True, blank=True, null=True)

    time_zone = TimeZoneField(use_pytz=True, default=settings.TIME_ZONE, null=True, blank=True)

    # User ownership
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, related_name="owned_deployments",
                              on_delete=models.SET_NULL, null=True)
    managers = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, related_name="managed_deployments", null=True)
    viewers = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, related_name="viewable_deployments", null=True)
    annotators = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, related_name="annotatable_deployments", null=True)

    combo_project = models.CharField(
        max_length=100, blank=True, null=True, editable=False)
    last_image = models.ForeignKey("DataFile", blank=True, on_delete=models.SET_NULL, null=True, editable=False,
                                   related_name="deployment_last_image")

    thumb_url = models.CharField(
        max_length=500, null=True, blank=True, editable=False)

    def get_absolute_url(self):
        return reverse('deployment-detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.deployment_device_ID
    
    def clean(self):
        # Check that deployment_start is before deployment_end
        result, message = validators.deployment_start_time_after_end_time(
            self.deployment_start, self.deployment_end
        )
        if not result:
            raise ValidationError(message)
        
        # Only perform the overlap check if a device is attached.
        if self.device is not None:
            result, message = validators.deployment_check_overlap(
                self.deployment_start, self.deployment_end, self.device, self.pk
            )
            if not result:
                raise ValidationError(message)
        
        super(Deployment, self).clean()

    def save(self, *args, **kwargs):
        # Bruk en fallback-streng dersom self.device er None,
        # eller dersom self.device.type er None.
        if self.device is not None and self.device.type is not None:
            device_type_name = self.device.type.name
        else:
            device_type_name = "NoDevice"

        # Bygg deployment_device_ID med fallback-verdien
        self.deployment_device_ID = f"{self.deployment_ID}_{device_type_name}_{self.device_n}"

        self.is_active = self.check_active()

        # Hvis self.device er satt, men self.device_type ikke er satt, sett det
        if self.device is not None and self.device_type is None:
            self.device_type = self.device.type

        if self.longitude and self.latitude:
            self.point = Point(
                float(self.longitude),
                float(self.latitude),
                srid=4326
            )
        elif (self.longitude is None and self.latitude is None) and self.point is not None:
            self.longitude, self.latitude = self.point.coords
        else:
            self.point = None

        if self.id:
            self.combo_project = self.get_combo_project()

        super().save(*args, **kwargs)

    def get_combo_project(self):
        if self.project.all().exists():
            all_proj_id = list(
                self.project.all().values_list("project_ID", flat=True))
            all_proj_id.sort()
            return " ".join(all_proj_id)
        else:
            return ""

    def check_active(self):
        self.deployment_start = check_dt(self.deployment_start)
        if self.deployment_end:
            self.deployment_end = check_dt(self.deployment_end)
        if self.deployment_start <= djtimezone.now():
            if self.deployment_end is None or self.deployment_end >= djtimezone.now():
                return True

        return False

    def check_dates(self, dt_list):

        result_list = []

        for dt in dt_list:
            # if no TZ, localise to the device's timezone
            dt = check_dt(dt, self.time_zone)
            # print(dt)
            result_list.append((dt >= self.deployment_start) and (
                (self.deployment_end is None) or (dt <= self.deployment_end)))

        return result_list

    def set_thumb_url(self):

        last_file = self.files.filter(thumb_url__isnull=False).order_by(
            'recording_dt').last()
        if last_file is not None:
            self.last_image = last_file
            self.thumb_url = last_file.thumb_url
        else:
            self.last_image = None
            self.thumb_url = None

    def get_folder_size(self, unit="MB"):
        """Calculate the total size of all files in this deployment"""
        return self.files.file_size(unit) if self.files.exists() else 0
        
    def get_last_upload(self):
        """Get the datetime of the most recent file upload for this deployment"""
        if self.files.exists():
            return self.files.aggregate(last_upload=models.Max('upload_dt'))['last_upload']
        return None


@receiver(post_save, sender=Deployment)
def post_save_deploy(sender, instance, created, **kwargs):
    # if created:
    #     print("doing created stuff")
    #     viewer_groupname = f"{instance.projectID}_deployment_viewers"
    #     viewer_usergroup = create_user_group(viewer_groupname)
    #     viewer_usergroup_profile = viewer_usergroup.profile
    #     viewer_usergroup_profile.project.add(instance)
    #     viewer_usergroup_profile.save()

    #     annotator_groupname = f"{instance.projectID}_deployment_annotators"
    #     annotator_usergroup = create_user_group(annotator_groupname)
    #     annotator_usergroup_profile = annotator_usergroup.profile
    #     annotator_usergroup_profile.project.add(instance)
    #     annotator_usergroup_profile.save()

    global_project, added = Project.objects.get_or_create(
        name=settings.GLOBAL_PROJECT_ID)
    # print(global_project)
    # print(instance.project.all())
    if global_project not in instance.project.all():
        instance.project.add(global_project)
        print("add global project")
        # RefreshDeploymentCache()
        # print("Clear deployment cache")
        # cache.delete_many(["allowed_deployments_{0}".format(x) for x in User.objects.all().values_list("username",flat=True)])


@receiver(m2m_changed, sender=Deployment.project.through)
def update_project(sender, instance, action, reverse, *args, **kwargs):

    if (action == 'post_add' or action == 'post_remove') and not reverse:
        instance.save()


# @receiver(post_delete, sender=Device)
# @receiver(post_delete, sender=Deployment)
# @receiver(post_delete, sender=Project)
# def clear_user_groups(sender, instance, **kwargs):
#     all_groups = Group.objects.all()
#     all_groups = all_groups.annotate(
#         all_is_null=ExpressionWrapper(
#             (Q(Q(profile__project=None) & Q(profile__device=None)
#              & Q(profile__deployment=None))),
#             output_field=BooleanField()
#         )
#     )
#     all_groups.filter(all_is_null=True).delete()

class DataFileQuerySet(models.QuerySet):
    def full_paths(self):
        file_path_components = self.values(
            "local_path", "path", "file_name", "file_format")
        all_full_paths = [os.path.join(
            x["local_path"], x["path"], x["file_name"]+x["file_format"]) for x in file_path_components]
        return all_full_paths

    def relative_paths(self):
        file_path_components = self.values(
            "path", "file_name", "file_format")
        all_relative_paths = [os.path.join(
            x["path"], x["file_name"]+x["file_format"]) for x in file_path_components]
        return all_relative_paths

    def full_names(self):
        file_name_components = self.values(
            "file_name", "file_format")
        all_names = [x["file_name"]+x["file_format"]
                     for x in file_name_components]
        return all_names

    def file_size(self, unit=""):
        total_file_size = self.aggregate(total_file_size=Sum("file_size"))[
            "total_file_size"]
        converted_file_size = convert_unit(total_file_size, unit)
        return converted_file_size

    def min_date(self):
        return self.aggregate(min_date=Min("recording_dt"))["min_date"]

    def max_date(self):
        return self.aggregate(max_date=Max("recording_dt"))["max_date"]

    def device_type(self):
        return self.annotate(device_type=F('deployment__device__type__name'))


class DataFile(BaseModel):
    deployment = models.ForeignKey(
        Deployment, on_delete=models.CASCADE, related_name="files")

    file_type = models.ForeignKey(
        DataType, models.PROTECT, related_name="files", null=True, default=None)
    file_name = models.CharField(max_length=100, unique=True)
    file_size = FileSizeField()
    file_format = models.CharField(max_length=10)

    # Audio file specific fields
    config = models.CharField(max_length=100, blank=True, null=True)
    sample_rate = models.IntegerField(null=True, blank=True)
    file_length = models.CharField(max_length=50, blank=True, null=True)

    # Audio quality check fields
    quality_score = models.FloatField(null=True, blank=True)
    quality_issues = models.JSONField(default=list, blank=True)
    quality_check_dt = models.DateTimeField(null=True, blank=True)
    quality_check_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('in_progress', 'In Progress'),
            ('completed', 'Completed'),
            ('failed', 'Failed')
        ],
        default='pending'
    )

    upload_dt = models.DateTimeField(default=djtimezone.now)
    recording_dt = models.DateTimeField(null=True, db_index=True)
    path = models.CharField(max_length=500)
    local_path = models.CharField(max_length=500, blank=True)

    extra_data = models.JSONField(default=dict, blank=True, null=True)
    linked_files = models.JSONField(default=dict, blank=True, null=True)

    thumb_url = models.CharField(max_length=500, null=True, blank=True)

    local_storage = models.BooleanField(default=True)
    archived = models.BooleanField(default=False)
    tar_file = models.ForeignKey(
        TarFile, on_delete=models.SET_NULL, blank=True, null=True, related_name="files")
    favourite_of = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, related_name="favourites")

    do_not_remove = models.BooleanField(default=False)
    original_name = models.CharField(max_length=100, blank=True, null=True)
    file_url = models.CharField(max_length=500, null=True, blank=True)
    tag = models.CharField(max_length=250, null=True, blank=True)

    objects = DataFileQuerySet.as_manager()

    def __str__(self):
        return f"{self.file_name}{self.file_format}"

    def get_absolute_url(self):
        return reverse('datafile-detail', kwargs={'pk': self.pk})

    def add_favourite(self, user):
        self.favourite_of.add(user)
        self.save()

    def remove_favourite(self, user):
        self.favourite_of.remove(user)
        self.save()

    def full_path(self):
        return os.path.join(self.local_path, self.path, f"{self.file_name}{self.file_format}")

    def thumb_path(self):
        return os.path.join(
            self.local_path, self.path, self.file_name+"_THUMB.jpg")

    def set_file_url(self):
        if self.local_storage:
            # is some of this normpath and replace stuff really needed?
            self.file_url = os.path.normpath(
                os.path.join(settings.FILE_STORAGE_URL,
                             self.path,
                             (self.file_name + self.file_format))
            ).replace("\\", "/")
        else:
            self.file_url = None

    def set_thumb_url(self, has_thumb=True):
        if has_thumb:
            self.thumb_url = os.path.normpath(os.path.join(settings.FILE_STORAGE_URL,
                                                           self.path, self.file_name+"_THUMB.jpg"))
        else:
            self.thumb_url = None

    def clean_file(self, delete_obj=False):
        try:
            if os.path.exists(self.full_path()):
                os.remove(self.full_path())
            if self.linked_files is not None:  # Add this check to handle None
                for file_type, file_dict in self.linked_files.values():
                    if os.path.exists(file_dict["fullpath"]):
                        os.remove(file_dict["fullpath"])
            if delete_obj:
                self.delete()
        except Exception as e:
            print(e)

    def save(self, *args, **kwargs):
        if self.file_type is None:
            self.file_type = self.deployment.device.type
        self.set_file_url()
        super().save(*args, **kwargs)

    def clean(self):
        result, message = validators.deployment_start_time_after_end_time(
            self.deployment_start, self.deployment_end
        )
        if not result:
            raise ValidationError(message)
        
        if self.device is not None:
            result, message = validators.deployment_check_overlap(
                self.deployment_start, self.deployment_end, self.device, self.pk
            )
            if not result:
                raise ValidationError(message)
        
        super(Deployment, self).clean()
        
@receiver(post_save, sender=DataFile)
def post_save_file(sender, instance, created, **kwargs):
    instance.deployment.set_thumb_url()
    instance.deployment.save()


@receiver(pre_delete, sender=DataFile)
def pre_remove_file(sender, instance, **kwargs):
    # deletes the attached file form data storage
    instance.clean_file(True)


@receiver(post_delete, sender=DataFile)
def post_remove_file(sender, instance, **kwargs):
    instance.deployment.set_thumb_url()
    instance.deployment.save()
