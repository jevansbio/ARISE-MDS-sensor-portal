from django.conf import settings
from django.contrib import admin
from utils.admin import AddOwnerAdmin, GenericAdmin
from utils.paginators import LargeTablePaginator
from utils.perm_functions import cascade_permissions

from .forms import DeviceForm
from .models import (DataFile, DataType, Deployment, Device, DeviceModel,
                     Project, ProjectJob, Site)

# Register your models here.


@admin.register(DataType)
class GenericAdmin(GenericAdmin):
    paginator = LargeTablePaginator


@admin.register(Site)
class SiteAdmin(GenericAdmin):
    list_display = ['short_name', 'name']
    search_fields = ['name', 'short_name']


@admin.register(Device)
class DeviceAdmin(AddOwnerAdmin):
    form = DeviceForm
    list_display = ['device_ID', 'type']
    search_fields = ['device_ID']
    list_filter = ['type']
    filter_horizontal = ['managers', 'annotators', 'viewers']

    def get_field_queryset(self, db, db_field, request):
        """
        If the ModelAdmin specifies ordering, the queryset should respect that
        ordering.  Otherwise don't specify the queryset, let the field decide
        (returns None in that case).
        """
        if db_field.name in ["managers", "annotators", "viewers"]:

            return db_field.remote_field.model._default_manager.filter(
                deviceuser__isnull=True,
                is_active=True
            ).order_by("username")

    #  admin form hack to make sure device user is assigned to managers
    def save_related(self, request, form, formsets, change):
        """
        Overrides the save_related method to perform additional actions 
        after saving related objects. Specifically, it ensures that the 
        `device_user` associated with the form instance is saved if it exists.
        Args:
            request (HttpRequest): The current HTTP request object.
            form (ModelForm): The form instance being processed.
            formsets (list): A list of formsets related to the form instance.
            change (bool): A flag indicating whether the object is being changed 
            (True) or added (False).
        Returns:
            None
        """

        super(AddOwnerAdmin, self).save_related(
            request, form, formsets, change)

        if form.instance.device_user:
            form.instance.device_user.save()

        cascade_permissions(form.instance)


@admin.register(DeviceModel)
class DeviceModelAdmin(AddOwnerAdmin):
    list_display = ['name', 'manufacturer', 'type']
    search_fields = ['name', 'manufacturer']
    list_filter = ['type']


@admin.register(Project)
class ProjectAdmin(AddOwnerAdmin):
    list_display = ['project_ID', 'name']
    search_fields = ['project_ID', 'name']
    filter_horizontal = ['managers', 'annotators', 'viewers']

    def get_field_queryset(self, db, db_field, request):
        """
        If the ModelAdmin specifies ordering, the queryset should respect that
        ordering.  Otherwise don't specify the queryset, let the field decide
        (returns None in that case).
        """
        if db_field.name in ["managers", "annotators", "viewers"]:

            return db_field.remote_field.model._default_manager.filter(
                deviceuser__isnull=True,
                is_active=True
            ).order_by("username")

        super().get_field_queryset(db, db_field, request)

    def save_related(self, request, form, formsets, change):
        """
        Overrides the save_related method to perform additional actions 
        after saving related objects. 
        Args:
            request (HttpRequest): The current HTTP request object.
            form (ModelForm): The form instance being processed.
            formsets (list): A list of formsets related to the form instance.
            change (bool): A flag indicating whether the object is being changed 
            (True) or added (False).
        Returns:
            None
        """

        super(AddOwnerAdmin, self).save_related(
            request, form, formsets, change)

        cascade_permissions(form.instance)


@admin.register(Deployment)
class DeployAdmin(AddOwnerAdmin):
    list_display = ['deployment_device_ID', 'device_type',
                    'is_active', 'modified_on', 'combo_project']
    search_fields = ['deployment_device_ID']
    list_filter = ['is_active', 'device_type']
    readonly_fields = GenericAdmin.readonly_fields + \
        AddOwnerAdmin.readonly_fields + ['deployment_device_ID',
                                         'combo_project', 'device_type', 'is_active', 'thumb_url',
                                         'managers', 'annotators', 'viewers']
    autocomplete_fields = ('device', 'project')

    filter_horizontal = ['managers', 'annotators', 'viewers']

    #  admin form hack to make sure global project is added
    def save_related(self, request, form, formsets, change):
        """
        Overrides the default save_related method to perform additional actions 
        after saving related objects. Specifically, it ensures that the global 
        project, defined by the GLOBAL_PROJECT_ID setting, is associated with 
        the instance being saved.
        Args:
            request (HttpRequest): The current HTTP request object.
            form (ModelForm): The form instance used to edit the model.
            formsets (list): A list of formsets related to the model.
            change (bool): A flag indicating whether the instance is being changed 
            (True) or added (False).
        Behavior:
            - Calls the parent class's save_related method to handle default behavior.
            - Retrieves or creates the global project based on the GLOBAL_PROJECT_ID setting.
            - Ensures the global project is added to the instance's project relationship 
              if it is not already associated.
        """

        super(AddOwnerAdmin, self).save_related(
            request, form, formsets, change)
        global_project, exists = Project.objects.get_or_create(
            project_ID=settings.GLOBAL_PROJECT_ID)
        if global_project not in form.instance.project.all():
            form.instance.project.add(global_project)


@admin.register(DataFile)
class FileAdmin(GenericAdmin):
    list_display = ['file_name', 'file_type', 'deployment',
                    'archived', 'local_storage', 'created_on']
    search_fields = ['file_name']
    list_filter = ['archived', 'local_storage', 'file_type']
    readonly_fields = GenericAdmin.readonly_fields + \
        ["upload_dt", "original_name", "local_path", "path", "file_url", "thumb_url"]


@admin.register(ProjectJob)
class JobAdmin(GenericAdmin):
    list_display = ["job_name", "celery_job_name"]
    search_fields = ["job_name", "celery_job_name"]
