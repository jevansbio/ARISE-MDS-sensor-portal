from data_models.models import DataFile
from django.conf import settings
from django.db import models
from django.db.models import Case, F, Min, Q, Value, When
from django.db.models.signals import m2m_changed, post_save
from django.dispatch import receiver
from utils.models import BaseModel

from .GBIF_functions import (GBIF_get_species, GBIF_taxoncode_from_search,
                             GBIF_to_avibase)
from .tasks import create_taxon_parents

# Create your models here.


class TaxonQuerySet(models.QuerySet):
    def get_taxonomic_level(self, target_level=1):
        annotated_qs = self.annotate(
            parent_taxon_pk=Case(
                When(taxonomic_level=target_level, then=F('pk')),
                When(taxonomic_level__lt=target_level, then=F("parents__pk"))))
        annotated_qs = annotated_qs.filter(
            Q(parent_taxon_pk=target_level) | Q(parent_taxon_pk__isnull=True))
        return annotated_qs


class Taxon(BaseModel):
    species_name = models.CharField(max_length=100, unique=False)
    species_common_name = models.CharField(
        max_length=100, unique=False, blank=True)
    taxon_code = models.CharField(max_length=100, blank=True)

    source_choice = (
        (0, 'custom'),
        (1, 'GBIF'),
    )

    taxonomic_level_choice = (
        (0, 'species'),
        (1, 'genus'),
        (2, 'family'),
        (3, 'order'),
        (4, 'class'),
        (5, 'phylum'),
        (6, 'kingdom'),
    )

    taxon_source = models.IntegerField(choices=source_choice, default=0)
    extra_data = models.JSONField(default=dict, blank=True)
    parents = models.ManyToManyField(
        "self", symmetrical=False, related_name="children", blank=True)
    taxonomic_level = models.IntegerField(
        choices=taxonomic_level_choice, default=0)

    objects = TaxonQuerySet.as_manager()

    # if GBIF ID, on save, from own taxonomic level through to 6, generate parents, attach parents
    # custom handlers to return different taxonomic level. If taxon has lower than desired taxonomic leve, return parent

    def __str__(self):
        return self.species_name

    def get_taxonomic_level(self, level=0):
        print(self.taxonomic_level, level)
        if self.taxonomic_level == level:
            return self
        else:
            try:
                taxon_obj = self.parents.all().get(taxonomic_level=level)
            except Taxon.DoesNotExist:
                taxon_obj = None
            return taxon_obj

    def get_taxon_code(self):
        if self.taxon_code is None or self.taxon_code == "":
            taxon_codes = GBIF_taxoncode_from_search(self.species_name)
            print(taxon_codes)
            if len(taxon_codes) > 0:
                self.taxon_code = taxon_codes[0][0]
                self.taxonomic_level = taxon_codes[0][1]
                self.taxon_source = 1
                species_data = GBIF_get_species(self.taxon_code)
                extra_data = self.extra_data
                if (gbif_vernacular_name := species_data.get("vernacularName")) is not None:
                    print(gbif_vernacular_name)
                    self.species_common_name = gbif_vernacular_name

                if species_data.get('class', '') == 'Aves':
                    avibaseID = GBIF_to_avibase(self.taxon_code)
                    if avibaseID is not None:
                        extra_data.update({"avibaseID": avibaseID})
                self.extra_data = extra_data
        else:
            self.taxon_source = 0

    def save(self, *args, **kwargs):
        self.get_taxon_code()
        # Only check for existing taxa if this is a new taxon being created
        if self.pk is None:
            try:
                existing = Taxon.objects.get(
                    species_name__iexact=self.species_name.lower())
                # If we found an existing taxon, use it instead of creating a new one
                self.pk = existing.pk
                self.id = existing.id
            except Taxon.DoesNotExist:
                pass
        # Never merge taxa - each taxon should be unique
        super().save(*args, **kwargs)


@receiver(post_save, sender=Taxon)
def post_taxon_save(sender, instance, created, **kwargs):
    if instance.taxon_code is not None and instance.taxon_code != "" and instance.taxon_source == 1:
        create_taxon_parents.apply_async([instance.pk])


class ObservationQuerySet(models.QuerySet):
    def get_taxonomic_level(self, target_level=1):
        annotated_qs = self.annotate(
            parent_taxon_pk=Case(
                When(taxon__taxonomic_level=target_level, then=F('taxon__pk')),
                When(taxon__taxonomic_level__lt=target_level,
                     then=F("taxon__parents__pk")),
                When(taxon__taxonomic_level__gt=target_level,
                     then=Value(None))),
            parent_taxon_level=Case(
                When(taxon__taxonomic_level=target_level,
                     then=F('taxon__taxonomic_level')),
                When(taxon__taxonomic_level__lt=target_level,
                     then=F("taxon__parents__taxonomic_level")),
                When(taxon__taxonomic_level__gt=target_level,
                     then=Value(None))
            ),

        )

        annotated_qs = annotated_qs.filter(
            parent_taxon_level=target_level).distinct()

        return annotated_qs


class Observation(BaseModel):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, related_name="observations",
                              on_delete=models.SET_NULL, null=True)
    label = models.CharField(max_length=300, blank=True, editable=False)
    taxon = models.ForeignKey(
        Taxon, on_delete=models.SET_NULL, related_name="observations", null=True)

    data_files = models.ManyToManyField(
        DataFile, related_name="observations")
    obs_dt = models.DateTimeField(null=True, blank=True)
    source = models.CharField(max_length=100, default="human")
    number = models.IntegerField(default=1)
    bounding_box = models.JSONField(default=dict, blank=True)
    extra_data = models.JSONField(default=dict, blank=True)

    sex = models.CharField(max_length=10, blank=True)
    lifestage = models.CharField(max_length=15, blank=True)
    behavior = models.CharField(max_length=50, blank=True)

    validation_requested = models.BooleanField(default=False)
    validation_of = models.ManyToManyField(
        "self", symmetrical=False, related_name="validated_by", blank=True)

    objects = ObservationQuerySet.as_manager()

    def get_taxonomic_level(self, level=0):
        return self.taxon.get_taxonomic_level(level)

    def __str__(self):
        return self.label

    def get_label(self):
        if self.data_files.all().exists():
            return f"{self.taxon.species_name}_{self.data_files.all().first().file_name}"
        else:
            return self.label

    def save(self, *args, **kwargs):
        if self.id:
            if self.label is None or self.label == "":
                self.label = self.get_label()

            if self.obs_dt is None and self.data_files.all().exists():
                min_recording_dt = self.data_files.all().aggregate(
                    min_recording_dt=Min("recording_dt"))
                self.obs_dt = min_recording_dt["min_recording_dt"]

        super().save(*args, **kwargs)


@receiver(m2m_changed, sender=Observation.data_files.through)
def update_observation_data_files(sender, instance, action, reverse, *args, **kwargs):

    if (action == 'post_add' or action == 'post_remove'):
        instance.save()
