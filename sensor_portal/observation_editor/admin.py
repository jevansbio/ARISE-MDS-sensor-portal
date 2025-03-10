from django.contrib import admin
from utils.admin import AddOwnerAdmin, GenericAdmin

from .models import Observation, Taxon

# Register your models here.


@admin.register(Taxon)
class TaxonAdmin(GenericAdmin):
    model = Taxon
    raw_id_fields = ["parents"]
    list_display = ["species_name", "species_common_name", "created_on"]


@admin.register(Observation)
class ObservationAdmin(AddOwnerAdmin):
    model = Observation
    raw_id_fields = ["data_files", "taxon"]
