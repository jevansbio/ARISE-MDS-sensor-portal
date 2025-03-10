from django.contrib import admin
from utils.admin import AddOwnerAdmin, GenericAdmin

from .forms import ArchiveForm
from .models import Archive, TarFile


@admin.register(Archive)
class ArchiveAdmin(AddOwnerAdmin):
    form = ArchiveForm


@admin.register(TarFile)
class TarFileAdmin(GenericAdmin):
    readonly_fields = ['archive']
