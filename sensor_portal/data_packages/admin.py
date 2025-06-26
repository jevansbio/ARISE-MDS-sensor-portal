from django.contrib import admin
from utils.admin import AddOwnerAdmin

from .models import DataPackage

# Register your models here.


@admin.register(DataPackage)
class DataPackageAdmin(AddOwnerAdmin):
    model = DataPackage
    raw_id_fields = ["data_files"]
    readonly_fields = ["file_url"]
    list_display = ["created_on", "name", "owner", "status", "includes_files"]
