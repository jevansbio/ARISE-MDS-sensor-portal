import logging
import os
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, List, Optional

from archiving.models import Archive, TarFile
from colorfield.fields import ColorField
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.gis.db import models as gis_models
from django.contrib.gis.geos import Point
from django.contrib.postgres.indexes import GinIndex, OpClass
from django.core.exceptions import (MultipleObjectsReturned,
                                    ObjectDoesNotExist, ValidationError)
from django.db import models
from django.db.models import (BooleanField, Case, Count, DateTimeField,
                              ExpressionWrapper, F, Max, Min, Q, Sum, Value,
                              When)
from django.db.models.functions import Cast, Concat, Upper
from django.urls import reverse
from django.utils import timezone as djtimezone
from django_icon_picker.field import IconField
from encrypted_model_fields.fields import EncryptedCharField
from external_storage_import.models import DataStorageInput
from sizefield.models import FileSizeField
from timezone_field import TimeZoneField
from utils.general import convert_unit, try_remove_file_clean_dirs
from utils.models import BaseModel
from utils.querysets import ApproximateCountQuerySet

from . import validators
from .general_functions import check_dt
from .job_handling_functions import get_job_from_name

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from user_management.models import User


class Site(BaseModel):
    """
    Represents a site with a name and an optional short name.

    If short_name is blank, it defaults to the first 10 characters of name.
    """
    name = models.CharField(max_length=50, help_text="Site name.")
    short_name = models.CharField(
        max_length=10, blank=True, help_text="Site short name.")

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.short_name == "":
            self.short_name = self.name[0:10]
        return super().save(*args, **kwargs)


class DataType(BaseModel):
    """
    Describes a type of data, including its name, color, and optional icon.
    """
    name = models.CharField(max_length=20, help_text="Name of data type.")
    colour = ColorField(default="#FFFFFF",
                        help_text="Colour to use for this data type.")
    symbol = IconField(
        blank=True, help_text="Symbol to use for this data type.")

    def __str__(self):
        return self.name


class Project(BaseModel):
    """
    Represents a project and its metadata, including ownership and relations.
    """
    project_ID = models.CharField(
        max_length=20, unique=True, blank=True, help_text="Unique project identifier.")
    name = models.CharField(max_length=50, help_text="Full project name.")
    objectives = models.CharField(
        max_length=500, blank=True, help_text="Project objectives description.")
    principal_investigator = models.CharField(
        max_length=50, blank=True, help_text="Full name of principal investigator.")
    principal_investigator_email = models.CharField(
        max_length=100, blank=True, help_text="Principal investigator email.")
    contact = models.CharField(
        max_length=50, blank=True, help_text="Name of primary contact.")
    contact_email = models.CharField(
        max_length=100, blank=True, help_text="Contact email.")
    organisation = models.CharField(
        max_length=100, blank=True, help_text="Organisation with which this project is associated.")
    data_storages = models.ManyToManyField(
        DataStorageInput, related_name="linked_projects", blank=True, help_text="External data storages available to this project."
    )
    archive = models.ForeignKey(
        Archive, related_name="linked_projects", null=True, blank=True, on_delete=models.SET_NULL,
        help_text="Data archive for project data."
    )
    automated_tasks = models.ManyToManyField(
        "ProjectJob", related_name="linked_projects", blank=True)

    def is_active(self):
        """
        Returns True if this project has at least one active deployment, else False.
        """
        if self.id:
            return self.deployments.filter(is_active=True).exists()
        return False

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, related_name="owned_projects",
                              on_delete=models.SET_NULL, null=True, db_index=True, help_text="Project owner.")
    managers = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, related_name="managed_projects", db_index=True, help_text="Project managers.")
    viewers = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, related_name="viewable_projects", db_index=True, help_text="Project viewers.")
    annotators = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, related_name="annotatable_projects", db_index=True, help_text="Project annotators.")

    clean_time = models.IntegerField(
        default=90, help_text="Days after last modification before archived file is removed from storage.")

    def __str__(self):
        return self.project_ID

    def get_absolute_url(self):
        """
        Returns the absolute URL for the project detail view.
        """
        return reverse('project-detail', kwargs={'pk': self.pk})

    def save(self, *args, **kwargs):
        """
        Auto-generate project_ID if not provided.
        """
        if self.project_ID == "" or self.project_ID is None:
            self.project_ID = self.name[0:10]
        return super().save(*args, **kwargs)


class DeviceModel(BaseModel):
    """
    Represents a type of device, its manufacturer, and data type.
    """
    name = models.CharField(max_length=50, blank=True, unique=True,
                            help_text="Name of device model. Used to find a data handler if available.")
    manufacturer = models.CharField(max_length=50, blank=True,
                                    help_text="Device model manufacturer.")
    type = models.ForeignKey(DataType, models.PROTECT,
                             related_name="device_models", help_text="Primary data type of device.")
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, related_name="owned_device_models",
                              on_delete=models.SET_NULL, null=True, help_text="User who registered this device model.")
    colour = ColorField(
        blank=True, help_text="Override data type colour. Leave blank to use the default from this data type.")
    symbol = IconField(
        blank=True, help_text="Override data type symbol. Leave blank to use the default from this data type.")

    def __str__(self):
        return self.name


class Device(BaseModel):
    """
    Represents a physical device or sensor.
    """
    device_ID = models.CharField(
        max_length=20, unique=True, help_text="Unique identifier for device, such as a serial number.")
    name = models.CharField(max_length=50, blank=True,
                            help_text="Optional alternative name for device.")
    model = models.ForeignKey(
        DeviceModel, models.PROTECT, related_name="registered_devices", help_text="Device model.")
    type = models.ForeignKey(DataType, models.PROTECT,
                             related_name="devices", null=True, db_index=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, related_name="owned_devices",
                              on_delete=models.SET_NULL, null=True, db_index=True, help_text="Device owner.")
    managers = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, related_name="managed_devices", db_index=True, help_text="Device managers.")
    viewers = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, related_name="viewable_devices", db_index=True, help_text="Device viewers.")
    annotators = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, related_name="annotatable_devices", db_index=True, help_text="Device annotators.")
    autoupdate = models.BooleanField(
        default=False, help_text="Is the device expected to autoupdate?")
    update_time = models.IntegerField(
        default=48, help_text="Hours between expected updates. Notify users after this time.")
    username = models.CharField(
        max_length=100, unique=True, null=True, blank=True, default=None, help_text="Device username for use with external storage.")
    password = EncryptedCharField(max_length=100, blank=True, null=True,
                                  help_text="Device password for use with external storage.")
    input_storage = models.ForeignKey(
        DataStorageInput, null=True, blank=True, related_name="linked_devices", on_delete=models.SET_NULL,
        help_text="External storage for device.")
    extra_data = models.JSONField(
        default=dict, blank=True, help_text="Extra data that doesn't fit in existing fields.")

    def is_active(self):
        """
        Returns True if the device has at least one active deployment.
        """
        if self.id:
            return self.deployments.filter(is_active=True).exists()
        return False

    def __str__(self):
        return self.device_ID

    def get_absolute_url(self):
        return f"/devices/{self.pk}"

    def save(self, *args, **kwargs):
        """
        Assigns the device type from the model if not explicitly set.
        """
        if not self.type:
            self.type = self.model.type
        super().save(*args, **kwargs)

    def clean(self):
        """
        Validates device type matches model type.
        """
        result, message = validators.device_check_type(self.type, self.model)
        if not result:
            raise ValidationError(message)
        super(Device, self).clean()

    def deployment_from_date(self, dt: datetime) -> "Deployment":
        """
        Return the deployment for this device active at the given datetime.

        Args:
            dt (datetime): Datetime to check. If None, returns None.

        Returns:
            Deployment or None: The matching deployment, or None if ambiguous or not found.

        Raises:
            ObjectDoesNotExist: If no matching deployment found.
            MultipleObjectsReturned: If more than one deployment matches.
        """
        logger.info(
            f"Attempt to find deployment for device {self.device_ID} for {dt}")
        if dt is None:
            return None
        all_deploys = self.deployments.all()
        all_tz = all_deploys.values('time_zone', 'pk')
        all_tz = [{'time_zone': x.get(
            'time_zone', settings.TIME_ZONE), 'pk': x['pk']} for x in all_tz]
        all_dt = {x['pk']: check_dt(dt, x['time_zone']) for x in all_tz}
        whens = [When(pk=k, then=Value(v)) for k, v in all_dt.items()]
        all_deploys = all_deploys.annotate(
            dt=Case(*whens, output_field=DateTimeField(), default=Value(None)))
        all_deploys = all_deploys.annotate(deployment_end_indefinite=Case(
            When(deployment_end__isnull=True,
                 then=ExpressionWrapper(F('deployment_start') + timedelta(days=365 * 100), output_field=DateTimeField())),
            default=F('deployment_end')
        ))
        all_deploys = all_deploys.annotate(in_deployment=ExpressionWrapper(
            Q(Q(deployment_start__lte=F('dt')) & Q(
                deployment_end_indefinite__gte=F('dt'))),
            output_field=BooleanField()))
        try:
            correct_deployment = all_deploys.get(in_deployment=True)
            return correct_deployment
        except (ObjectDoesNotExist, MultipleObjectsReturned):
            all_true_deployments = all_deploys.filter(in_deployment=True)
            logger.info(
                f"Error: found {all_true_deployments.count()} deployments")
            return None

    def check_overlap(self, new_start: datetime, new_end: Optional[datetime], deployment_pk: Optional[int]) -> List[str]:
        """
        Check for overlapping deployments in the given date range, excluding a given deployment.

        Args:
            new_start (datetime): Start of new deployment.
            new_end (Optional[datetime]): End of new deployment (None = indefinite).
            deployment_pk (Optional[int]): Deployment to exclude.

        Returns:
            List[str]: Device IDs of overlapping deployments.
        """
        new_start = check_dt(new_start)
        if new_end is None:
            new_end = new_start + timedelta(days=365 * 100)
        else:
            new_end = check_dt(new_end)
        all_deploys = self.deployments.all().exclude(pk=deployment_pk)
        all_deploys = all_deploys.annotate(deployment_end_indefinite=Case(
            When(deployment_end__isnull=True,
                 then=ExpressionWrapper(F('deployment_start') + timedelta(days=365 * 100), output_field=DateTimeField())),
            default=F('deployment_end')
        ))
        all_deploys = all_deploys.annotate(in_deployment=ExpressionWrapper(
            Q(Q(deployment_end_indefinite__gte=new_start)
              & Q(deployment_start__lte=new_end)),
            output_field=BooleanField()))
        overlapping_deploys = all_deploys.filter(in_deployment=True)
        return list(overlapping_deploys.values_list('deployment_device_ID', flat=True))


class Deployment(BaseModel):
    """
    Records a deployment of a device to a site, within a project.
    """
    deployment_device_ID = models.CharField(
        max_length=110, blank=True, editable=False, unique=True,
        help_text="Unique identifier combining 'deployment_ID', 'device_type' and 'device_n'.")
    deployment_ID = models.CharField(
        max_length=80, help_text="An identifier for a deployment.")
    device_type = models.ForeignKey(
        DataType, models.PROTECT, related_name="deployments", null=True, db_index=True, help_text="Primary data type of deployment.")
    device_n = models.IntegerField(default=1,
                                   help_text="Numeric suffix of deployment, allowing for multiple deployments to share the same 'deployment_ID' and 'device_type'.")
    deployment_start = models.DateTimeField(
        default=djtimezone.now, help_text="Start datetime of deployment.")
    deployment_end = models.DateTimeField(
        blank=True, null=True, help_text="End time of deployment. Can be NULL if deployment is ongoing.")
    device = models.ForeignKey(
        Device, on_delete=models.PROTECT, related_name="deployments", db_index=True, help_text="Device of which this is a deployment.")
    site = models.ForeignKey(Site, models.PROTECT, related_name="deployments",
                             help_text="Site at which this deployment is placed.")
    project = models.ManyToManyField(
        Project, related_name="deployments", blank=True, db_index=True, help_text="Projects to which this deployment is attached.")
    latitude = models.DecimalField(
        max_digits=8, decimal_places=6, blank=True, null=True, help_text="Latitude at which this deployment is placed.")
    longitude = models.DecimalField(
        max_digits=8, decimal_places=6, blank=True, null=True, help_text="Longitude at which this deployment is placed.")
    point = gis_models.PointField(
        blank=True, null=True, spatial_index=True, help_text="Spatial point representing this deployment."
    )
    extra_data = models.JSONField(
        default=dict, blank=True, help_text="Extra data that does not fit in other fields.")
    is_active = models.BooleanField(
        default=True, help_text="Is the deployment currently active? Checked every hour.")
    time_zone = TimeZoneField(
        use_pytz=True, default=settings.TIME_ZONE, help_text="Time zone for this deployment.")

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, related_name="owned_deployments",
                              on_delete=models.SET_NULL, null=True, db_index=True, help_text="Owner of deployment.")
    managers = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, related_name="managed_deployments",  db_index=True,
        help_text="Managers of deployment.")
    viewers = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, related_name="viewable_deployments", db_index=True,
        help_text="Annotators of deployment.")
    annotators = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, related_name="annotatable_deployments", db_index=True,
        help_text="Viewers of deployment.")

    combo_project = models.CharField(
        max_length=100, blank=True, null=True, editable=False, help_text="String combining all projects.")
    last_image = models.ForeignKey("DataFile", blank=True, on_delete=models.SET_NULL, null=True, editable=False,
                                   related_name="deployment_last_image", help_text="Last image (if any) linked to this deployment.")
    thumb_url = models.CharField(
        max_length=500, null=True, blank=True, editable=False, help_text="Deployment thumbnail URL.")

    def get_absolute_url(self):
        """
        Returns the URL to this deployment detail.
        """
        return f"/deployments/{self.pk}"

    def __str__(self):
        return self.deployment_device_ID

    def clean(self):
        """
        Validates deployment start/end time and checks for overlapping deployments.
        Raises ValidationError on failure.
        """
        result, message = validators.deployment_start_time_after_end_time(
            self.deployment_start, self.deployment_end)
        if not result:
            raise ValidationError(message)
        result, message = validators.deployment_check_overlap(
            self.deployment_start, self.deployment_end, self.device, self.pk)
        if not result:
            raise ValidationError(message)
        super(Deployment, self).clean()

    def save(self, *args, **kwargs):
        """
        Sets deployment_device_ID, is_active, device_type, point, and combo_project before saving.
        """
        self.deployment_device_ID = f"{self.deployment_ID}_{self.device.type.name}_{self.device_n}"
        self.is_active = self.check_active()
        if self.device_type is None:
            self.device_type = self.device.type
        if self.longitude and self.latitude:
            self.point = Point(float(self.longitude),
                               float(self.latitude), srid=4326)
        elif (self.longitude is None and self.latitude is None) and self.point is not None:
            self.longitude, self.latitude = self.point.coords
        else:
            self.point = None
        if self.id:
            self.combo_project = self.get_combo_project()
        super().save(*args, **kwargs)
        self.get_permissions()

    def get_permissions(self):
        """
        Propagates permissions from device and project to this deployment.
        """
        logger.info(
            f"Set deployment {self} permissions from device and projects")
        all_managers = self.device.managers.all().union(
            get_user_model().objects.filter(pk__in=self.project.all().values_list('managers__pk', flat=True)))
        self.managers.set(all_managers)
        all_annotators = self.device.annotators.all().union(
            get_user_model().objects.filter(pk__in=self.project.all().values_list('annotators__pk', flat=True)))
        self.annotators.set(all_annotators)
        all_viewers = self.device.viewers.all().union(
            get_user_model().objects.filter(pk__in=self.project.all().values_list('viewers__pk', flat=True)))
        self.viewers.set(all_viewers)
        if self.owner:
            self.managers.add(self.owner)
            self.annotators.add(self.owner)
            self.viewers.add(self.owner)

    def get_combo_project(self):
        """
        Returns a single space-separated string of sorted project IDs for this deployment.
        """
        if self.project.all().exists():
            all_proj_id = list(
                self.project.all().values_list("project_ID", flat=True))
            all_proj_id.sort()
            return " ".join(all_proj_id)
        else:
            return ""

    def check_active(self):
        """
        Returns True if the deployment is currently active, otherwise False.
        """
        self.deployment_start = check_dt(self.deployment_start)
        if self.deployment_end:
            self.deployment_end = check_dt(self.deployment_end)
        if self.deployment_start <= djtimezone.now():
            if self.deployment_end is None or self.deployment_end >= djtimezone.now():
                return True
        return False

    def check_dates(self, dt_list: List[datetime]) -> List[bool]:
        """
        Checks if datetimes in dt_list fall within the deployment's period.

        Args:
            dt_list (List[datetime]): List of datetimes to check.

        Returns:
            List[bool]: True for each value in dt_list that is within the deployment, else False.
        """
        result_list = []
        for dt in dt_list:
            dt = check_dt(dt, self.time_zone)
            result_list.append((dt >= self.deployment_start)
                               and ((self.deployment_end is None) or (dt <= self.deployment_end)))
        return result_list

    def set_thumb_url(self):
        """
        Sets thumb_url and last_image based on latest file that has a thumbnail and no human involvement.
        """
        last_file = self.files.filter(
            thumb_url__isnull=False, has_human=False).order_by('recording_dt').last()
        if last_file is not None:
            self.last_image = last_file
            self.thumb_url = last_file.thumb_url
        else:
            self.last_image = None
            self.thumb_url = None


class DataFileQuerySet(ApproximateCountQuerySet):
    """
    Custom QuerySet for DataFile, providing path annotations and statistics.
    """

    def full_paths(self):
        self = self.relative_paths()
        return self.annotate(full_path=Concat(F('local_path'), Value(os.sep), F('relative_path')))

    def relative_paths(self):
        self = self.full_names()
        return self.annotate(relative_path=Concat(F('path'), Value(os.sep), F('full_name')))

    def full_names(self):
        return self.annotate(full_name=Concat(F('file_name'), F('file_format')))

    def file_size_unit(self, unit=""):
        total_file_size = self.aggregate(total_file_size=Sum("file_size"))[
            "total_file_size"]
        converted_file_size = convert_unit(total_file_size, unit)
        return converted_file_size

    def file_count(self):
        return self.aggregate(total_file_size=Cast(Sum("file_size"), models.FloatField())/Cast(Value(1024*1024*1024), models.FloatField()),
                              object_n=Count("pk"),
                              archived_file_n=Sum(Case(When(local_storage=False, archived=True, then=Value(1)), default=Value(0))))

    def min_date(self):
        return self.aggregate(min_date=Min("recording_dt"))["min_date"]

    def max_date(self):
        return self.aggregate(max_date=Max("recording_dt"))["max_date"]

    def device_type(self):
        return self.annotate(device_type=F('deployment__device__type__name'))


class DataFile(BaseModel):
    """
    Represents a data file associated with a deployment.
    """
    deployment = models.ForeignKey(
        Deployment, on_delete=models.CASCADE, related_name="files", db_index=True, help_text="Deployment to which this datafile is linked.")
    file_type = models.ForeignKey(
        DataType, models.PROTECT, related_name="files", null=True, default=None, db_index=True, help_text="Data type of file.")
    file_name = models.CharField(
        max_length=150, unique=True, db_index=True, help_text="File name.")
    file_size = FileSizeField(help_text="Size of file in bytes.")
    file_format = models.CharField(max_length=10, help_text="File extension.")
    upload_dt = models.DateTimeField(
        default=djtimezone.now, help_text="Datetime at which the file was uploaded.")
    recording_dt = models.DateTimeField(
        null=True, db_index=True, help_text="Datetime at which the file was recorded.")
    path = models.CharField(max_length=500, help_text="Relative path.")
    local_path = models.CharField(max_length=500, blank=True,
                                  help_text="Absolute file location on local storage, from which path is relative.")
    extra_data = models.JSONField(
        default=dict, blank=True, help_text="Extra data that does not fit in existing columns.")
    linked_files = models.JSONField(
        default=dict, blank=True, help_text="Linked files, such as alternative representations of this file.")
    thumb_url = models.CharField(
        max_length=500, null=True, blank=True, help_text="Thumbnail URL.")
    local_storage = models.BooleanField(
        default=True, db_index=True, help_text="Is the file available on local storage?")
    archived = models.BooleanField(
        default=False, help_text="Has the file been archived?")
    tar_file = models.ForeignKey(
        TarFile, on_delete=models.SET_NULL, blank=True, null=True, related_name="files",
        help_text="TAR file containing this file.")
    favourite_of = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, related_name="favourites", help_text="Users who have favourited this file.")
    do_not_remove = models.BooleanField(
        default=False, help_text="If True, this file will not be removed during cleaning.")
    original_name = models.CharField(
        max_length=100, blank=True, null=True, help_text="Original name of this file.")
    file_url = models.CharField(
        max_length=500, null=True, blank=True, help_text="URL of this file")
    tag = models.CharField(max_length=250, null=True,
                           blank=True, db_index=True, help_text="Additional identifying tag of this file.")
    has_human = models.BooleanField(
        default=False, db_index=True, help_text="True if this image has been annotated with a human.")

    objects = DataFileQuerySet.as_manager()

    class Meta:
        indexes = [
            GinIndex(
                OpClass(Upper('tag'), name='gin_trgm_ops'),
                name='upper_tag_gin_idx',
            ),
            GinIndex(
                OpClass(Upper('file_name'), name='gin_trgm_ops'),
                name='upper_file_name_gin_idx',
            )
        ]

    def __str__(self):
        return f"{self.file_name}{self.file_format}"

    def get_absolute_url(self):
        return f"/datafiles/{self.pk}"

    def add_favourite(self, user: "User") -> None:
        """
        Add a user to this file's favourites.
        """
        self.favourite_of.add(user)
        self.save()

    def remove_favourite(self, user: "User") -> None:
        """
        Remove a user from this file's favourites.
        """
        self.favourite_of.remove(user)
        self.save()

    def full_path(self):
        """
        Returns the full path to this file on local storage.
        """
        return os.path.join(self.local_path, self.path, f"{self.file_name}{self.file_format}")

    def thumb_path(self):
        """
        Returns the path to the thumbnail version of this file.
        """
        return os.path.join(self.local_path, self.path, self.file_name+"_THUMB.jpg")

    def set_file_url(self):
        """
        Sets the file_url for this file using storage settings.
        """
        if self.local_storage:
            self.file_url = os.path.normpath(
                os.path.join(settings.FILE_STORAGE_URL, self.path,
                             (self.file_name + self.file_format))
            ).replace("\\", "/")
        else:
            self.file_url = None

    def set_linked_files_urls(self):
        """
        Set file URLs for each linked file.
        """
        for key in self.linked_files.keys():
            file_path = self.linked_files[key]["path"]
            rel_file_path = os.path.relpath(
                file_path, settings.FILE_STORAGE_ROOT)
            self.linked_files[key]["url"] = os.path.join(
                settings.FILE_STORAGE_URL, rel_file_path)

    def set_thumb_url(self, has_thumb: bool = True) -> None:
        """
        Set the thumbnail URL for this file.
        """
        if has_thumb:
            self.thumb_url = os.path.normpath(os.path.join(
                settings.FILE_STORAGE_URL, self.path, self.file_name+"_THUMB.jpg"))
        else:
            self.thumb_url = None

    def check_human(self):
        """
        Checks for human observations and updates has_human accordingly.
        """
        old_has_human = self.has_human
        new_has_human = self.observations.filter(
            taxon__taxon_code=settings.HUMAN_TAXON_CODE).exists()
        if old_has_human != new_has_human:
            self.has_human = new_has_human
            self.save()
            self.deployment.set_thumb_url()
            self.deployment.save()

    def clean_file(self, delete_obj: bool = False, force_delete: bool = False) -> bool:
        """
        Clean up this file and its associated resources.

        Args:
            delete_obj (bool): True if the object will be deleted from the database after cleaning.
            force_delete (bool): If True, force deletion/alteration even if file can't be deleted.

        Returns:
            bool: True if the file was successfully cleaned, False otherwise.
        """
        logger.info(
            f"Clean {self.file_name} - Delete object: {delete_obj} - Force delete:{force_delete}")
        if (delete_obj and self.archived) and not force_delete:
            logger.info(
                f"Clean {self.file_name} - Full delete failed - Archived file")
            return False
        if (self.do_not_remove or self.deployment_last_image.exists() or self.favourite_of.exists()) and (not delete_obj or force_delete):
            logger.info(f"Clean {self.file_name} - Failed - Protected file")
            return False
        if self.local_storage:
            logger.info(f"Clean {self.file_name} - Try to remove file")
            success = try_remove_file_clean_dirs(self.full_path())
            if not success and not force_delete:
                logger.error(
                    f"Clean {self.file_name} - Failed - Cannot delete local file")
                return False
            elif success:
                logger.info(
                    f"Clean {self.file_name} - Try to remove file - success")
            logger.info(f"Clean {self.file_name} - Try to remove thumbnail")
            if self.thumb_url is not None and self.thumb_url != "":
                thumb_path = self.thumb_path()
                success = try_remove_file_clean_dirs(thumb_path)
                if success:
                    logger.info(
                        f"Clean {self.file_name} - Try to remove thumbnail - success")
                else:
                    logger.info(
                        f"Clean {self.file_name} - Try to remove thumbnail - failed")
            for key, value in self.linked_files.items():
                extra_version_path = value["path"]
                logger.info(f"Clean {self.file_name} - Try to remove {key}")
                success = try_remove_file_clean_dirs(extra_version_path)
                if success:
                    logger.info(
                        f"Clean {self.file_name} - Try to remove {key} - success")
                else:
                    logger.info(
                        f"Clean {self.file_name} - Try to remove {key} - failed")
        if not delete_obj:
            logger.info(f"Clean {self.file_name} - Altering database")
            self.local_storage = False
            self.local_path = ""
            self.linked_files = {}
            self.set_thumb_url(False)
            self.save()
        return True

    def save(self, *args, **kwargs):
        """
        Assigns file_type from deployment if not set, sets file_url, then saves.
        """
        if self.file_type is None:
            self.file_type = self.deployment.device.type
        self.set_file_url()
        super().save(*args, **kwargs)

    def clean(self):
        """
        Validates that this file is within its deployment's date range.
        Raises ValidationError if invalid.
        """
        result, message = validators.data_file_in_deployment(
            self.recording_dt, self.deployment)
        if not result:
            raise ValidationError(message)
        super(DataFile, self).clean()


class ProjectJob(BaseModel):
    """
    Represents a project-level job configuration.
    """
    job_name = models.CharField(max_length=50, help_text="Name of job")
    celery_job_name = models.CharField(
        max_length=50, help_text="Name of registered celery task.")
    job_args = models.JSONField(
        default=dict, help_text="Additional arguments.")

    def __str__(self):
        return self.job_name

    def get_job_signature(self, file_pks: list) -> dict:
        """
        Generate a job signature for a Celery task.

        Args:
            file_pks (list): List of file primary keys to process.

        Returns:
            dict: Dictionary representing the job signature.
        """
        return get_job_from_name(self.celery_job_name, "datafile", file_pks, self.job_args)
