from django.contrib import admin

# Register your models here.
from utils.admin import GenericAdmin, AddOwnerAdmin
from .models import DataStorageInput
from .forms import DataStorageInputForm


@admin.register(DataStorageInput)
class ExternalStorageInputAdmin(AddOwnerAdmin):
    form = DataStorageInputForm
