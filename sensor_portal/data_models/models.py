
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
    Attributes:
        name (str): The full name of the site. Maximum length is 50 characters.
        short_name (str): A shorter name for the site. Maximum length is 10 characters.
                         If left blank, it will default to the first 10 characters of `name`.
    Methods:
        __str__(): Returns the string representation of the site, which is its name.
        save(*args, **kwargs): Overrides the save method to automatically set `short_name`
                               to the first 10 characters of `name` if `short_name` is blank.
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
    Represents a data type with associated attributes such as name, colour, and symbol.
    Attributes:
        name (CharField): The name of the data type, limited to 20 characters.
        colour (ColorField): The color associated with the data type, defaults to white (#FFFFFF).
        symbol (IconField): An optional icon representing the data type, can be left blank.
    Methods:
        __str__(): Returns the name of the data type as its string representation.
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
    Represents a project entity with metadata, user ownership, and associated relationships.
    Attributes:
        project_ID (str): Unique identifier for the project. Automatically generated if not provided.
        name (str): Name of the project.
        objectives (str): Description of the project's objectives. Optional.
        principal_investigator (str): Name of the principal investigator. Optional.
        principal_investigator_email (str): Email of the principal investigator. Optional.
        contact (str): Name of the contact person for the project. Optional.
        contact_email (str): Email of the contact person. Optional.
        organisation (str): Organisation associated with the project. Optional.
        data_storages (ManyToManyField): Data storage inputs linked to the project. Optional.
        archive (ForeignKey): Archive associated with the project. Optional.
        automated_tasks (ManyToManyField): Automated tasks linked to the project. Optional.
        owner (ForeignKey): User who owns the project. Optional.
        managers (ManyToManyField): Users who manage the project. Optional.
        viewers (ManyToManyField): Users who can view the project. Optional.
        annotators (ManyToManyField): Users who can annotate the project. Optional.
        clean_time (int): Time in days for cleaning project data. Defaults to 90.
    Methods:
        is_active():
            Checks if the project has active deployments.
            Returns:
                bool: True if active deployments exist, False otherwise.
        __str__():
            Returns the string representation of the project, which is its unique project_ID.
        get_absolute_url():
            Returns the absolute URL for the project detail view.
        save(*args, **kwargs):
            Overrides the save method to automatically generate a project_ID if not provided.
    """

    # Metadata
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
        DataStorageInput, related_name="linked_projects", blank=True, help_text="External data storages (such as FTP server) that are available to users associated with this project.")
    archive = models.ForeignKey(
        Archive, related_name="linked_projects", null=True, blank=True, on_delete=models.SET_NULL,
        help_text="Data archive that data associated with this project will be uploaded to.")

    automated_tasks = models.ManyToManyField(
        "ProjectJob", related_name="linked_projects", blank=True
    )

    def is_active(self):
        """
        Determines whether the current object is active based on its deployments.
        Returns:
            bool: True if the object has an ID and at least one associated deployment 
              marked as active; otherwise, False.
        """

        if self.id:
            return self.deployments.filter(is_active=True).exists()
        else:
            return False

    # User ownership
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, related_name="owned_projects",
                              on_delete=models.SET_NULL, null=True, db_index=True, help_text="Project owner.")
    managers = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, related_name="managed_projects", db_index=True, help_text="Project managers.")
    viewers = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, related_name="viewable_projects", db_index=True, help_text="Project viewers.")
    annotators = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, related_name="annotatable_projects", db_index=True, help_text="Project annotators.")

    clean_time = models.IntegerField(
        default=90, help_text="How long after last modification should an archived file be removed from local storage?")

    def __str__(self):
        return self.project_ID

    def get_absolute_url(self):
        return reverse('project-detail', kwargs={'pk': self.pk})

    def save(self, *args, **kwargs):
        if self.project_ID == "" or self.project_ID is None:
            self.project_ID = self.name[0:10]
        return super().save(*args, **kwargs)


class DeviceModel(BaseModel):
    """
    Represents a device model in the system.
    Attributes:
        name (str): The name of the device model. Must be unique and can be blank.
        manufacturer (str): The manufacturer of the device model. Can be blank.
        type (DataType): A foreign key to the DataType model, representing the type of the device.
        owner (User): A foreign key to the user model, representing the owner of the device model.
                      Can be null and blank. If the owner is deleted, the field is set to null.
        colour (str): The color associated with the device model. Defaults to the color of the type if blank.
        symbol (str): The icon associated with the device model. Defaults to the symbol of the type if blank.
    Methods:
        save(*args, **kwargs): Overrides the save method to set default values for `colour` and `symbol`
                               if they are blank.
        __str__(): Returns the string representation of the device model, which is its name.
    """

    name = models.CharField(max_length=50, blank=True, unique=True,
                            help_text="Name of device model. This will be used to find a data handler if one is available.")
    manufacturer = models.CharField(max_length=50, blank=True,
                                    help_text="Device model manufacturer.")
    type = models.ForeignKey(DataType, models.PROTECT,
                             related_name="device_models", help_text="Primary data type of device.")
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, related_name="owned_device_models",
                              on_delete=models.SET_NULL, null=True, help_text="User who registered this device model with the system.")
    colour = ColorField(
        blank=True, help_text="Override data type colour. Leave blank to use the default from this data type.")
    symbol = IconField(
        blank=True, help_text="Override data type symbol. Leave blank to use the default from this data type.")

    def __str__(self):
        return self.name


class Device(BaseModel):
    """
    Represents a device/sensor in the system.
    Attributes:
        device_ID (CharField): Unique identifier for the device, limited to 20 characters.
        name (CharField): Optional name for the device, limited to 50 characters.
        model (ForeignKey): Reference to the associated DeviceModel, protected on deletion.
        type (ForeignKey): Reference to the associated DataType, protected on deletion, nullable.
        owner (ForeignKey): Reference to the user who owns the device, nullable, set to null on deletion.
        managers (ManyToManyField): Users who manage the device.
        viewers (ManyToManyField): Users who can view the device.
        annotators (ManyToManyField): Users who can annotate the device.
        autoupdate (BooleanField): Indicates whether the device should be expected to auto-update.
        update_time (IntegerField): Time interval for updates, default is 48 hours.
        username (CharField): Optional username for the device, unique, nullable.
        password (EncryptedCharField): Optional encrypted password for the device.
        input_storage (ForeignKey): Reference to the associated DataStorageInput, nullable, set to null on deletion.
        extra_data (JSONField): Additional data for the device, stored as a JSON object.
    Methods:
        is_active():
            Checks if the device has active deployments.
        __str__():
            Returns the string representation of the device (device_ID).
        get_absolute_url():
            Returns the absolute URL for the device on the frontend.
        save(*args, **kwargs):
            Overrides the save method to ensure the device type is set based on the model type.
        clean():
            Validates the device type against the model type using custom validators.
        deployment_from_date(dt):
            Finds the deployment associated with the device for a given datetime.
        check_overlap(new_start, new_end, deployment_pk):
            Checks for overlapping deployments within the specified date range, excluding a given deployment.
    """

    device_ID = models.CharField(
        max_length=20, unique=True, help_text="Unique identifier for device, such as a serial number.")
    name = models.CharField(max_length=50, blank=True,
                            help_text="Optional alternative name for device, potentially a more human readable name.")
    model = models.ForeignKey(
        DeviceModel, models.PROTECT, related_name="registered_devices", help_text="Device model.")

    type = models.ForeignKey(DataType, models.PROTECT,
                             related_name="devices", null=True, db_index=True)

    # User ownership
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, related_name="owned_devices",
                              on_delete=models.SET_NULL, null=True, db_index=True,
                              help_text="Device owner.")
    managers = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, related_name="managed_devices", db_index=True,
        help_text="Device managers.")
    viewers = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, related_name="viewable_devices", db_index=True,
        help_text="Device viewers.")
    annotators = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, related_name="annotatable_devices", db_index=True,
        help_text="Device annotators.")

    autoupdate = models.BooleanField(
        default=False, help_text="Is the device expected to autoupdate?")
    update_time = models.IntegerField(
        default=48, help_text="How often is the device expected to send files? Send users an email after this many hours have elapsed.")

    username = models.CharField(
        max_length=100, unique=True, null=True, blank=True, default=None, help_text="Device username to use with external storage, such as an FTP server.")
    password = EncryptedCharField(max_length=100, blank=True, null=True,
                                  help_text="Device password to use with external storage, such as an FTP server.")
    input_storage = models.ForeignKey(
        DataStorageInput, null=True, blank=True, related_name="linked_devices", on_delete=models.SET_NULL,
        help_text="External storage, such as an FTP server.")

    extra_data = models.JSONField(
        default=dict, blank=True, help_text="Extra data that doesn't fit in existing fields.")

    def is_active(self):
        if self.id:
            return self.deployments.filter(is_active=True).exists()
        else:
            return False

    def __str__(self):
        return self.device_ID

    def get_absolute_url(self):
        return f"/devices/{self.pk}"

    def save(self, *args, **kwargs):
        if not self.type:
            self.type = self.model.type
        super().save(*args, **kwargs)

    def clean(self):
        result, message = validators.device_check_type(
            self.type, self.model)

        if not result:
            raise ValidationError(message)
        super(Device, self).clean()

    def deployment_from_date(self, dt: datetime) -> "Deployment":
        """
        Determines the deployment associated with the device for a given datetime.
        This method attempts to find the deployment that corresponds to the provided
        datetime (`dt`) for the current device instance. It handles deployments with
        indefinite end dates by shifting the end date 100 years into the future.
        Args:
            dt (datetime): The datetime for which the deployment is to be determined.
                   If `None`, the method returns `None`.
        Returns:
            Deployment: The deployment object that matches the given datetime, or `None`
                if no matching deployment is found or if there is ambiguity
                (multiple deployments match the datetime).
        Raises:
            ObjectDoesNotExist: If no deployment matches the given datetime.
            MultipleObjectsReturned: If multiple deployments match the given datetime.
        Notes:
            - Deployments are annotated with a calculated datetime (`dt`) based on the
              provided timezone.
            - Deployments with no end date are treated as having an indefinite end date
              (100 years from the start date).
            - The method uses annotations and filters to determine whether the datetime
              falls within the deployment range.
            - If ambiguity arises (multiple deployments match), the method logs the
              number of matching deployments and returns `None`.
        """

        logger.info(
            f"Attempt to find deployment for device {self.device_ID} for {dt}")

        if dt is None:
            return None

        # logger.info(dt)
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
            logger.info(
                f"Error: found {all_true_deployments.count()} deployments")
            return None

    def check_overlap(self, new_start: datetime, new_end: Optional[datetime], deployment_pk: Optional[int]) -> List[str]:
        """
        Checks for overlapping deployments within the specified date range, excluding a given deployment.

        Args:
            new_start (datetime): The start datetime of the new deployment.
            new_end (Optional[datetime]): The end datetime of the new deployment. If None, it is treated as indefinite.
            deployment_pk (Optional[int]): The primary key of the deployment to exclude from the overlap check.

        Returns:
            List[str]: A list of overlapping deployment device IDs.
        """
        new_start = check_dt(new_start)
        if new_end is None:
            new_end = new_start + timedelta(days=365 * 100)
        else:
            new_end = check_dt(new_end)

        # Retrieve all deployments associated with the device, excluding the one specified by deployment_pk
        all_deploys = self.deployments.all().exclude(pk=deployment_pk)

        # Annotate deployments with an indefinite end date for those that have no end date
        # If deployment_end is null, set deployment_end_indefinite to 100 years after deployment_start
        all_deploys = all_deploys.annotate(deployment_end_indefinite=Case(
            When(deployment_end__isnull=True,
                 then=ExpressionWrapper(
                     F('deployment_start') + timedelta(days=365 * 100),
                     output_field=DateTimeField()
                 )
                 ),
            # Otherwise, use the actual deployment_end value
            default=F('deployment_end')
        )
        )

        # Annotate deployments with a boolean field indicating whether they overlap with the new date range
        # A deployment overlaps if its start date is before or equal to the new end date
        # and its end date (or indefinite end date) is after or equal to the new start date
        all_deploys = all_deploys.annotate(in_deployment=ExpressionWrapper(
            Q(Q(deployment_end_indefinite__gte=new_start)
                & Q(deployment_start__lte=new_end)),
            output_field=BooleanField()
        )
        )

        overlapping_deploys = all_deploys.filter(in_deployment=True)
        return list(overlapping_deploys.values_list('deployment_device_ID', flat=True))


class Deployment(BaseModel):
    """
    Represents a deployment of a device to a specific site within a project.
    Attributes:
        deployment_device_ID (str): Unique identifier for the deployment device, auto-generated.
        deployment_ID (str): Identifier for the deployment.
        device_type (ForeignKey): Reference to the type of device being deployed.
        device_n (int): Number of devices deployed, defaults to 1.
        deployment_start (DateTimeField): Start time of the deployment.
        deployment_end (DateTimeField): End time of the deployment, can be null.
        device (ForeignKey): Reference to the device being deployed.
        site (ForeignKey): Reference to the site where the device is deployed.
        project (ManyToManyField): Projects associated with the deployment.
        latitude (DecimalField): Latitude of the deployment location.
        longitude (DecimalField): Longitude of the deployment location.
        point (PointField): Geospatial point representing the deployment location.
        extra_data (JSONField): Additional data related to the deployment.
        is_active (bool): Indicates whether the deployment is currently active.
        time_zone (TimeZoneField): Time zone of the deployment.
        owner (ForeignKey): User who owns the deployment.
        combo_project (str): Combined project identifiers, auto-generated.
        last_image (ForeignKey): Reference to the last image associated with the deployment.
        thumb_url (str): URL of the thumbnail image for the deployment.
    Methods:
        get_absolute_url():
            Returns the absolute URL for the deployment detail view.
        __str__():
            Returns the string representation of the deployment, which is the deployment_device_ID.
        clean():
            Validates the deployment data, including checking for overlapping deployments and ensuring
            the start time is before the end time.
        save(*args, **kwargs):
            Saves the deployment instance, auto-generating fields like deployment_device_ID, combo_project,
            and point based on latitude and longitude.
        get_combo_project():
            Generates a combined string of project IDs associated with the deployment.
        check_active():
            Checks whether the deployment is currently active based on the start and end times.
        check_dates(dt_list):
            Validates a list of datetime objects against the deployment's start and end times.
        set_thumb_url():
            Sets the thumbnail URL and last image based on associated files with thumbnails.
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

    deployment_start = models.DateTimeField(default=djtimezone.now,
                                            help_text="Start datetime of deployment.")
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
        blank=True,
        null=True,
        spatial_index=True,
        help_text="Spatial point representing this deployment."
    )

    extra_data = models.JSONField(
        default=dict, blank=True, help_text="Extra data that does not fit in other fields.")
    is_active = models.BooleanField(
        default=True, help_text="Is the deployment currently active? Checked every hour.")

    time_zone = TimeZoneField(use_pytz=True, default=settings.TIME_ZONE,
                              help_text="Time zone to which files with time zone naive datetimes will be localised.")

    # User ownership
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
        return (f"/deployments/{self.pk}")

    def __str__(self):
        return self.deployment_device_ID

    def clean(self):
        """
        Validates the deployment data before saving the model instance.
        This method performs the following checks:
        1. Ensures the deployment start time is after the end time using 
           `validators.deployment_start_time_after_end_time`.
        2. Checks for overlapping deployments using 
           `validators.deployment_check_overlap`.
        If any validation fails, a `ValidationError` is raised with the 
        corresponding error message.
        Overrides the `clean` method of the parent class.
        Raises:
            ValidationError: If any of the validation checks fail.
        """

        # result, message = validators.deployment_check_type(
        #     self.device_type, self.device)
        # if not result:
        #     raise ValidationError(message)

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
        Overrides the save method to perform custom operations before saving the model instance.
        This method performs the following tasks:
        - Sets the `deployment_device_ID` based on `deployment_ID`, `device.type.name`, and `device_n`.
        - Updates the `is_active` field by calling the `check_active` method.
        - Ensures the `device_type` is set to the type of the associated device if not already specified.
        - Creates or updates the `point` field as a geographic Point object using `longitude` and `latitude`.
          If both `longitude` and `latitude` are None but `point` is set, it extracts coordinates from `point`.
          If neither `longitude`, `latitude`, nor `point` are provided, sets `point` to None.
        - If the instance has an `id`, updates the `combo_project` field by calling the `get_combo_project` method.
        - Calls the parent class's `save` method to persist the changes.
        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
        Returns:
            None
        """

        self.deployment_device_ID = f"{self.deployment_ID}_{self.device.type.name}_{self.device_n}"

        self.is_active = self.check_active()

        if self.device_type is None:
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
        self.get_permissions()

    def get_permissions(self):
        # Get permissions from device and project

        logger.info(
            f"Set deployment {self} permissions from device and projects")
        all_managers = self.device.managers.all().\
            union(get_user_model().objects.filter(pk__in=self.project.all().values_list(
                'managers__pk', flat=True)))
        self.managers.set(all_managers)
        all_annotators = self.device.annotators.all().\
            union(get_user_model().objects.filter(pk__in=self.project.all().values_list(
                'annotators__pk', flat=True)))
        self.annotators.set(all_annotators)
        all_viewers = self.device.viewers.all().\
            union(get_user_model().objects.filter(pk__in=self.project.all().values_list(
                'viewers__pk', flat=True)))
        self.viewers.set(all_viewers)

        if self.owner:
            self.managers.add(self.owner)
            self.annotators.add(self.owner)
            self.viewers.add(self.owner)

    def get_combo_project(self):
        """
        Retrieves a concatenated string of sorted project IDs associated with the instance.
        This method checks if there are any related projects. If projects exist, it collects 
        their IDs, sorts them in ascending order, and returns them as a single space-separated 
        string. If no projects are associated, it returns an empty string.
        Returns:
            str: A space-separated string of sorted project IDs if projects exist, 
             otherwise an empty string.
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
        Determines whether the current deployment is active based on its start and end times.
        This method checks if the deployment start time has already occurred and, if applicable, 
        whether the deployment end time has not yet passed. If the deployment is currently active, 
        it returns True; otherwise, it returns False.
        Returns:
            bool: True if the deployment is active, False otherwise.
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
        Validates a list of datetime objects against the deployment's start and end times.

        Args:
            dt_list (List[datetime]): A list of datetime objects to validate.

        Returns:
            List[bool]: A list of boolean values indicating whether each datetime in the input list
                        falls within the deployment's start and end times.
                        True if the datetime is within the range, False otherwise.
        """
        result_list = []

        for dt in dt_list:
            # If no timezone is provided, localize to the deployment's timezone
            dt = check_dt(dt, self.time_zone)
            result_list.append((dt >= self.deployment_start) and (
                (self.deployment_end is None) or (dt <= self.deployment_end)))

        return result_list

    def set_thumb_url(self):
        """
        Updates the `thumb_url` and `last_image` attributes based on the latest file 
        that meets specific criteria.
        This method filters the associated files to find the most recent file 
        (ordered by `recording_dt`) that has a non-null `thumb_url` and is marked 
        as not having human involvement (`has_human=False`). If such a file exists, 
        its `thumb_url` is assigned to the `thumb_url` attribute, and the file itself 
        is assigned to the `last_image` attribute. If no such file exists, both 
        attributes are set to `None`.
        Returns:
            None
        """

        last_file = self.files.filter(thumb_url__isnull=False, has_human=False).order_by(
            'recording_dt').last()
        if last_file is not None:
            self.last_image = last_file
            self.thumb_url = last_file.thumb_url
        else:
            self.last_image = None
            self.thumb_url = None


class DataFileQuerySet(ApproximateCountQuerySet):
    """
    A custom QuerySet for handling operations related to data files.
    Methods:
        full_paths():
            Annotates the QuerySet with the full path of each file by concatenating
            the local path, a separator, and the relative path.
        relative_paths():
            Annotates the QuerySet with the relative path of each file by concatenating
            the path, a separator, and the full name.
        full_names():
            Annotates the QuerySet with the full name of each file by concatenating
            the file name and file format.
        file_size_unit(unit=""):
            Aggregates the total file size and converts it to the specified unit.
            Args:
                unit (str): The unit to convert the file size to (e.g., KB, MB, GB).
        file_count():
            Aggregates the total file size in gigabytes, the total number of objects,
            and the count of archived files.
        min_date():
            Retrieves the earliest recording date from the QuerySet.
        max_date():
            Retrieves the latest recording date from the QuerySet.
        device_type():
            Annotates the QuerySet with the device type associated with each file.
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
                              archived_file_n=Sum(Case(When(local_storage=False, archived=True, then=Value(1)),
                                                       default=Value(0))))

    def min_date(self):
        return self.aggregate(min_date=Min("recording_dt"))["min_date"]

    def max_date(self):
        return self.aggregate(max_date=Max("recording_dt"))["max_date"]

    def device_type(self):
        return self.annotate(device_type=F('deployment__device__type__name'))


class DataFile(BaseModel):
    """
    Represents a data file associated with a deployment.
    Attributes:
        deployment (ForeignKey): Reference to the associated Deployment object.
        file_type (ForeignKey): Type of the file, referencing the DataType model.
        file_name (CharField): Name of the file, must be unique.
        file_size (FileSizeField): Size of the file.
        file_format (CharField): Format of the file (e.g., '.jpg', '.png').
        upload_dt (DateTimeField): Date and time when the file was uploaded.
        recording_dt (DateTimeField): Date and time when the file was recorded.
        path (CharField): Path to the file in storage.
        local_path (CharField): Local path to the file, optional.
        extra_data (JSONField): Additional metadata associated with the file.
        linked_files (JSONField): Metadata for linked files.
        thumb_url (CharField): URL for the thumbnail of the file, optional.
        local_storage (BooleanField): Indicates if the file is stored locally.
        archived (BooleanField): Indicates if the file is archived.
        tar_file (ForeignKey): Reference to the associated TarFile object, optional.
        favourite_of (ManyToManyField): Users who have marked the file as a favorite.
        do_not_remove (BooleanField): Flag to prevent removal of the file.
        original_name (CharField): Original name of the file, optional.
        file_url (CharField): URL of the file, optional.
        tag (CharField): Tag associated with the file, optional.
        has_human (BooleanField): Indicates if the file contains human observations.
    Methods:
        __str__(): Returns a string representation of the file.
        get_absolute_url(): Returns the absolute URL for the file detail view.
        add_favourite(user): Adds a user to the list of favorites for the file.
        remove_favourite(user): Removes a user from the list of favorites for the file.
        full_path(): Returns the full path to the file.
        thumb_path(): Returns the path to the thumbnail of the file.
        set_file_url(): Sets the URL for the file based on its storage location.
        set_linked_files_urls(): Sets URLs for linked files based on their paths.
        set_thumb_url(has_thumb): Sets the URL for the thumbnail of the file.
        check_human(): Checks if the file contains human observations and updates related attributes.
        clean_file(delete_obj, force_delete): Cleans up the file and its associated resources.
        save(*args, **kwargs): Overrides the save method to set default attributes and file URL.
        clean(): Validates the file's recording date against its deployment.
    Meta:
        indexes: Defines database indexes for efficient querying.
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
        null=True, db_index=True, help_text="Datetime at which the file was recored.")
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
        return (f"/datafiles/{self.pk}")

    def add_favourite(self, user: "User") -> None:
        """
        Adds a user to the list of favourites for the current object.
        Args:
            user (User): The user instance to be added to the favourites.
        Returns:
            None
        """

        self.favourite_of.add(user)
        self.save()

    def remove_favourite(self, user: "User") -> None:
        """
        Removes a user from the list of favourites for the current object.

        Args:
            user (User): The user instance to be removed from the favourites.

        Returns:
            None
        """
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

    def set_linked_files_urls(self):
        """
        Updates the `linked_files` dictionary by setting the URL for each file.
        This method iterates through the `linked_files` dictionary, calculates
        the relative file path based on the `FILE_STORAGE_ROOT` setting, and
        constructs the file's URL using the `FILE_STORAGE_URL` setting. The
        resulting URL is stored in the `url` key for each file entry.
        Attributes:
            linked_files (dict): A dictionary where each key represents a file
            identifier and the value is another dictionary containing file
            metadata, including the file path and URL.
        Raises:
            KeyError: If the `path` key is missing in any file entry within
            `linked_files`.
        """

        for key in self.linked_files.keys():
            file_path = self.linked_files[key]["path"]
            rel_file_path = os.path.relpath(
                file_path, settings.FILE_STORAGE_ROOT)
            self.linked_files[key]["url"] = os.path.join(
                settings.FILE_STORAGE_URL, rel_file_path)

    def set_thumb_url(self, has_thumb: bool = True) -> None:
        """
        Sets the thumbnail URL for the file based on its storage location.

        Args:
            has_thumb (bool): Indicates whether the file has a thumbnail. Defaults to True.

        Returns:
            None
        """
        if has_thumb:
            self.thumb_url = os.path.normpath(os.path.join(settings.FILE_STORAGE_URL,
                                                           self.path, self.file_name+"_THUMB.jpg"))
        else:
            self.thumb_url = None

    def check_human(self):
        """
        Checks if human observations are present and updates the `has_human` attribute accordingly.
        This method compares the current state of the `has_human` attribute with the presence of 
        observations related to humans (determined by the `HUMAN_TAXON_CODE` setting). If there is 
        a change in the state, it updates the `has_human` attribute, saves the instance, updates 
        the deployment's thumbnail URL, and saves the deployment.
        Steps:
        1. Retrieve the current state of `has_human`.
        2. Check if there are observations with the human taxon code.
        3. Compare the old and new states of `has_human`.
        4. If the state has changed:
           - Update `has_human`.
           - Save the instance.
           - Update the deployment's thumbnail URL.
           - Save the deployment.
        Returns:
            None
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
        Cleans up the file and its associated resources.

        Args:
            delete_obj (bool): True if the object is going to be deleted from the database after cleaning.
            force_delete (bool): If True, forces deletion/alteration of the database object even if the file cannot be deleted.

        Returns:
            bool: True if the file was successfully cleaned, False otherwise.
        """
        logger.info(
            f"Clean {self.file_name} - Delete object: {delete_obj} - Force delete:{force_delete}")

        if (delete_obj and self.archived) and not force_delete:
            logger.info(
                f"Clean {self.file_name} - Full delete failed - Archived file")

            return False

        if (self.do_not_remove or
            self.deployment_last_image.exists() or
                self.favourite_of.exists()) and (not delete_obj or force_delete):
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
        Overrides the save method to perform additional operations before saving the model instance.
        If the `file_type` attribute is not set, it assigns the `file_type` based on the associated 
        deployment's device type. Additionally, it sets the file URL by calling the `set_file_url` method.
        Args:
            *args: Variable length argument list passed to the parent save method.
            **kwargs: Arbitrary keyword arguments passed to the parent save method.
        Calls:
            - `set_file_url`: A method to set the file URL for the instance.
            - `super().save(*args, **kwargs)`: Saves the instance using the parent class's save method.
        """

        if self.file_type is None:
            self.file_type = self.deployment.device.type
        self.set_file_url()
        super().save(*args, **kwargs)

    def clean(self):
        """
        Validates the integrity of the DataFile instance before saving.
        This method checks whether the data file is correctly associated with a deployment
        and ensures that the recording date and deployment are valid. If the validation fails,
        a ValidationError is raised with an appropriate error message.
        Overrides:
            The `clean` method of the parent class to include custom validation logic.
        Raises:
            ValidationError: If the data file is not valid within the context of the deployment.
        """

        result, message = validators.data_file_in_deployment(
            self.recording_dt, self.deployment)
        if not result:
            raise ValidationError(message)
        super(DataFile, self).clean()


class ProjectJob(BaseModel):
    """
    Represents a project-level job configuration in the system.
    Attributes:
        job_name (str): The name of the job.
        celery_job_name (str): The name of the corresponding Celery task.
        job_args (dict): A dictionary of arguments to be passed to the job. Defaults to an empty dictionary.
    Methods:
        __str__():
            Returns the string representation of the job, which is the job name.
        get_job_signature(file_pks):
            Generates the job signature for the Celery task associated with this project-level job.
            Args:
                file_pks (list): A list of primary keys of files that the job will operate on.
            Returns:
                A Celery job signature object configured with the job name, type, file primary keys, and arguments.
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

        This method creates a job signature for a project-level task that operates 
        on file-level data. It assumes the task is triggered by files being imported.

        Args:
            file_pks (list): A list of primary keys representing the files to be processed.

        Returns:
            dict: A dictionary representing the job signature, including the job name, 
                    target model ("datafile"), file primary keys, and additional job arguments.
        """
        # project level jobs always assumed to work on the file level, as they are fired by files being imported
        return get_job_from_name(self.celery_job_name, "datafile", file_pks, self.job_args)
