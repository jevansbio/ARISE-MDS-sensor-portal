import os
import traceback
from datetime import datetime, time, timedelta, timezone
from threading import local
from unittest import TextTestRunner

from bridgekeeper import perms
from django.conf import settings
from django.contrib.auth.models import Group
from django.contrib.gis.db import models as gis_models
from django.contrib.gis.geos import Point
from django.core.exceptions import (
    MultipleObjectsReturned,
    ObjectDoesNotExist,
    ValidationError,
)
from django.db import models
from django.db.models import (
    BooleanField,
    Case,
    DateTimeField,
    ExpressionWrapper,
    F,
    JSONField,
    Q,
    Sum,
    Value,
    When,
)
from django.db.models.signals import m2m_changed, post_delete, post_save, pre_delete
from django.dispatch import receiver
from django.urls import reverse
from django.utils import timezone as djtimezone
from sizefield.models import FileSizeField
from timezone_field import TimeZoneField
from .general_functions import check_dt

from . import validators


class Basemodel(models.Model):
    created_on = models.DateTimeField(auto_now_add=True)
    modified_on = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    def model_name(self):
        return self._meta.model_name

    def save(self, *args, **kwargs):
        self.clean()
        return super().save(*args, **kwargs)


class Site(Basemodel):
    name = models.CharField(max_length=50)
    short_name = models.CharField(max_length=10, blank=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.short_name == "":
            self.short_name = self.name[0:10]
        return super().save(*args, **kwargs)


class DataType(Basemodel):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class Project(Basemodel):
    # Metadata
    project_ID = models.CharField(max_length=10, unique=True, blank=True)
    name = models.CharField(max_length=50)

    objectives = models.CharField(max_length=500, blank=True)
    principal_investigator = models.CharField(max_length=50, blank=True)
    principal_investigator_email = models.CharField(max_length=100, blank=True)
    contact = models.CharField(max_length=50, blank=True)
    contact_email = models.CharField(max_length=100, blank=True)
    organisation = models.CharField(max_length=100, blank=True)

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

    # Archiving
    archive_files = models.BooleanField(default=True)
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


class DeviceModel(Basemodel):
    name = models.CharField(max_length=50, blank=True, unique=True)
    manufacturer = models.CharField(max_length=50, blank=True)
    type = models.ForeignKey(DataType, models.PROTECT,
                             related_name="device_models")
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, related_name="owned_device_models",
                              on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.name


class Device(Basemodel):
    device_ID = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=50, blank=True)
    model = models.ForeignKey(
        DeviceModel, models.PROTECT, related_name="registered_devices")

    type = models.ForeignKey(DataType, models.PROTECT,
                             related_name="devices", null=True)

    # User ownership
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, related_name="owned_devices",
                              on_delete=models.SET_NULL, null=True)
    managers = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, related_name="managed_devices")
    viewers = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, related_name="viewable_devices")
    annotators = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, related_name="annotatable_devices")

    autoupdate = models.BooleanField(default=False)
    update_time = models.IntegerField(default=48)

    username = models.CharField(
        max_length=100, unique=True, null=True, blank=True, default=None)
    authentication = models.CharField(max_length=100, blank=True, null=True)
    extra_data = models.JSONField(default=dict, blank=True)

    def is_active(self):
        if self.id:
            return self.deployments.filter(is_active=True).exists()
        else:
            return False

    def __str__(self):
        return self.device_ID

    def get_absolute_url(self):
        return f"/api/device/{self.pk}"

    def save(self, *args, **kwargs):
        if not self.type:
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

        print(deployment_pk)
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
        print(all_deploys.values('deployment_end', 'deployment_end_indefinite'))
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


class Deployment(Basemodel):
    deployment_device_ID = models.CharField(
        max_length=100, blank=True, editable=False, unique=True)
    deployment_ID = models.CharField(max_length=50)
    device_type = models.ForeignKey(
        DataType, models.PROTECT, related_name="deployments", null=True)
    device_n = models.IntegerField(default=1)

    deployment_start = models.DateTimeField(default=djtimezone.now)
    deployment_end = models.DateTimeField(blank=True, null=True)

    device = models.ForeignKey(
        Device, on_delete=models.PROTECT, related_name="deployments")
    site = models.ForeignKey(Site, models.PROTECT, related_name="deployments")
    project = models.ManyToManyField(
        Project, related_name="deployments", blank=True)

    latitude = models.DecimalField(
        max_digits=8, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(
        max_digits=8, decimal_places=6, blank=True, null=True)
    point = gis_models.PointField(
        blank=True,
        null=True,
        spatial_index=True
    )

    extra_data = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)

    time_zone = TimeZoneField(use_pytz=True, default=settings.TIME_ZONE)

    # User ownership
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, related_name="owned_deployments",
                              on_delete=models.SET_NULL, null=True)
    managers = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, related_name="managed_deployments")
    viewers = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, related_name="viewable_deployments")
    annotators = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, related_name="annotatable_deployments")

    combo_project = models.CharField(
        max_length=100, blank=True, null=True, editable=False)
    last_image = models.ForeignKey("DataFile", blank=True, on_delete=models.SET_NULL, null=True, editable=False,
                                   related_name="deployment_last_image")
    last_file = models.ForeignKey("DataFile", blank=True, on_delete=models.SET_NULL, null=True, editable=False,
                                  related_name="deployment_last_file")
    last_imageURL = models.CharField(
        max_length=500, null=True, blank=True, editable=False)

    def get_absolute_url(self):
        return reverse('deployment-detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.deployment_device_ID

    def clean(self):
        result, message = validators.deployment_check_type(
            self.device_type, self.device)
        if not result:
            raise ValidationError(message)
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

    def get_combo_project(self):
        if self.project.all().exists:
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
            print(dt)
            result_list.append((dt >= self.deployment_start) and (
                (self.deployment_end is None) or (dt <= self.deployment_end)))

        return result_list

    def set_last_file(self, newfile=None):
        try:
            if self.files.exists():
                file_object = self.files.all().latest('recording_dt')
            elif newfile is not None:
                if self.last_file is None:
                    file_object = newfile
            else:
                file_object = None
            if file_object is not None:
                self.last_file = file_object
                self.set_last_image()
                self.save()

        except:
            print(traceback.format_exc())
            pass

    def set_last_image(self):
        if self.last_file:
            # check for thumbnail first
            if self.last_file.file_format.lower() in [".jpg", ".jpeg"]:
                self.last_image = self.last_file
                self.last_imageURL = self.last_file.file_url


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
    print(global_project)
    print(instance.project.all())
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


class DataFile(Basemodel):
    deployment = models.ForeignKey(
        Deployment, on_delete=models.CASCADE, related_name="files")

    file_type = models.ForeignKey(
        DataType, models.PROTECT, related_name="files", null=True, default=None)
    file_name = models.CharField(max_length=50, unique=True)
    file_size = FileSizeField()
    file_format = models.CharField(max_length=10)

    upload_dt = models.DateTimeField(default=djtimezone.now)
    recording_dt = models.DateTimeField(null=True, db_index=True)
    path = models.CharField(max_length=500)
    local_path = models.CharField(max_length=500, blank=True)

    extra_data = models.JSONField(default=dict, blank=True)
    extra_versions = models.JSONField(default=dict, blank=True)
    thumb_path = models.JSONField(default=None, blank=True, null=True)

    local_storage = models.BooleanField(default=True)
    archived = models.BooleanField(default=False)
    # tarfile = models.ForeignKey(TarFile, on_delete=models.SET_NULL, blank=True, null=True, related_name="Files")
    favourite_of = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, related_name="favourites")

    do_not_remove = models.BooleanField(default=False)
    original_name = models.CharField(max_length=100, blank=True, null=True)
    file_url = models.CharField(max_length=500, null=True, blank=True)
    tag = models.CharField(max_length=250, null=True, blank=True)

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

    def set_file_url(self):
        if self.local_storage:

            self.file_url = os.path.normpath(
                os.path.join(settings.FILE_STORAGE_URL,
                             self.path,
                             (self.file_name + self.file_format))
            ).replace("\\", "/")
            # if not self.thumbpath:
            # last_images = self.DeployLastIm.all()
            # if lastim.exists() and self.deployment:
            #    self.deployment.GetLastImageURL()
            #    self.deployment.save()
        else:
            self.file_url = None

    def clean_file(self, delete_obj=False):
        print(f"clean {delete_obj}")
        if (
                self.do_not_remove or self.deployment_last_image.exists or self.deployment_last_file.exists) and not delete_obj:
            return
        if self.local_storage:
            try:
                os.remove(self.full_path())
                os.removedirs(os.path.join(self.local_path, self.path))
            except OSError:
                pass

        try:
            thumb_path = self.thumb_path["filepath"]
            os.remove(thumb_path)
            os.removedirs(os.path.split(thumb_path)[0])
        except TypeError:
            pass
        except OSError:
            pass

        for v in self.extra_versions.values():
            try:
                extra_version_path = v["filepath"]
                os.remove(extra_version_path)
                os.removedirs(extra_version_path)
            except TypeError:
                pass
            except OSError:
                pass

        if not delete_obj:
            self.local_storage = False
            self.local_path = ""
            self.extra_versions = {}
            self.thumb_path = None
            self.save()

    def save(self, *args, **kwargs):
        if self.file_type is None:
            self.file_type = self.deployment.device.type
        self.set_file_url()
        super().save(*args, **kwargs)

    def clean(self):
        result, message = validators.data_file_in_deployment(
            self.recording_dt, self.deployment)
        if not result:
            raise ValidationError(message)
        super(DataFile, self).clean()


@receiver(post_save, sender=DataFile)
def post_save_file(sender, instance, created, **kwargs):
    # if created:
    # print("Refresh file cache")
    # RefreshFileCache()

    # cache.delete_many(["allowed_files_{0}".format(x) for x in User.objects.all().values_list("username",flat=True)])
    instance.deployment.set_last_file(instance)
    # if instance.format.lower() in [".jpg",".jpeg",".png",".dat"]:
    #    instance.deployment.SetLastImage(instance)


@receiver(pre_delete, sender=DataFile)
def pre_remove_file(sender, instance, **kwargs):
    # deletes the attached file form data storage
    instance.clean_file(True)


@receiver(post_delete, sender=DataFile)
def post_remove_file(sender, instance, **kwargs):
    instance.deployment.set_last_file()
