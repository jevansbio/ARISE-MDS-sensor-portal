import logging

from data_models.models import DataFile
from django.conf import settings
from django.contrib.postgres.indexes import GinIndex, OpClass
from django.db import models
from django.db.models import Case, F, Min, Q, Value, When
from django.db.models.functions import Upper
from django.db.models.signals import m2m_changed, post_delete, post_save
from django.dispatch import receiver
from requests.exceptions import ConnectionError, ConnectTimeout
from utils.models import BaseModel
from utils.querysets import ApproximateCountQuerySet

from .GBIF_functions import (GBIF_get_species, GBIF_taxoncode_from_search,
                             GBIF_to_avibase)
from .tasks import create_taxon_parents

logger = logging.getLogger(__name__)

# Create your models here.

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


class TaxonQuerySet(ApproximateCountQuerySet):
    def get_taxonomic_level(self, target_level=1):
        annotated_qs = self.annotate(
            parent_taxon_pk=Case(
                When(taxonomic_level=target_level, then=F('pk')),
                When(taxonomic_level__lt=target_level, then=F("parents__pk"))))
        annotated_qs = annotated_qs.filter(
            Q(parent_taxon_pk=target_level) | Q(parent_taxon_pk__isnull=True))
        return annotated_qs


class Taxon(BaseModel):
    species_name = models.CharField(
        max_length=100, unique=False, db_index=True,
        help_text="Scientific name of the species, e.g. 'Aquila chrysaetos'.")
    species_common_name = models.CharField(
        max_length=100, unique=False, blank=True, db_index=True, help_text="Common name of the species, e.g. 'Golden Eagle'.")
    taxon_code = models.CharField(max_length=100, blank=True, db_index=True,
                                  help_text="Taxon code from a taxonomic database, e.g. GBIF ID,\
                                      or another common identifier such as 'vehicle'.")

    taxon_source = models.IntegerField(
        choices=source_choice, default=0, help_text="Source of the taxon code. 0 = custom, 1 = GBIF.")
    extra_data = models.JSONField(
        default=dict,  help_text="Extra data about the taxon, e.g. avibaseID, or other relevant information.", blank=True)
    parents = models.ManyToManyField(
        "self", symmetrical=False, related_name="children", blank=True, help_text="Parent taxons of this taxon.")
    taxonomic_level = models.IntegerField(
        choices=taxonomic_level_choice, default=0, help_text="Taxonomic level of the species, e.g. 0 = species, 1 = genus, 2 = family, etc.")

    objects = TaxonQuerySet.as_manager()

    # if GBIF ID, on save, from own taxonomic level through to 6, generate parents, attach parents
    # custom handlers to return different taxonomic level. If taxon has lower than desired taxonomic leve, return parent

    def __str__(self):
        return self.species_name

    def get_taxonomic_level(self, level=0):
        logger.info(self.taxonomic_level, level)
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
            logger.info(taxon_codes)
            if len(taxon_codes) > 0:
                self.taxon_code = taxon_codes[0][0]
                self.taxonomic_level = taxon_codes[0][1]
                self.taxon_source = 1
                species_data = GBIF_get_species(self.taxon_code)
                extra_data = self.extra_data
                if (gbif_vernacular_name := species_data.get("vernacularName")) is not None:
                    logger.info(gbif_vernacular_name)
                    self.species_common_name = gbif_vernacular_name

                if species_data.get('class', '') == 'Aves':
                    avibaseID = GBIF_to_avibase(self.taxon_code)
                    if avibaseID is not None:
                        extra_data.update({"avibaseID": avibaseID})
                self.extra_data = extra_data
        else:
            self.taxon_source = 0

    def save(self, *args, **kwargs):
        try:
            self.get_taxon_code()
        except ConnectionError or ConnectTimeout as e:
            logger.info(e)
            pass

        try:
            existing = Taxon.objects.get(
                species_name__iexact=self.species_name.lower())
            if existing != self:
                if self.pk is not None:
                    # get all existing observations and change them, then delete this instance
                    Observation.objects.filter(
                        taxon=self).update(taxon=existing)
                    self.delete()
                    return
        except Taxon.DoesNotExist:
            pass
        super().save(*args, **kwargs)


@receiver(post_save, sender=Taxon)
def post_taxon_save(sender, instance, created, **kwargs):
    if instance.taxon_code is not None and instance.taxon_code != "" and instance.taxon_source == 1:
        create_taxon_parents.apply_async([instance.pk])


class ObservationQuerySet(ApproximateCountQuerySet):
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
                              on_delete=models.SET_NULL, null=True, db_index=True,
                              help_text="User who created the observation.\
                                  Null if created by AI.")
    label = models.CharField(max_length=300, blank=True, editable=False)
    taxon = models.ForeignKey(
        Taxon, on_delete=models.PROTECT, related_name="observations", null=True, db_index=True, help_text="Taxon of the observed species.")

    data_files = models.ManyToManyField(
        DataFile, related_name="observations", db_index=True, help_text="Data files associated with the observation.")
    obs_dt = models.DateTimeField(
        null=True, blank=True, help_text="Date and time of the observation.")
    source = models.CharField(max_length=100, default="human", db_index=True,
                              help_text="Source of the observation, e.g. 'human' or an AI model name.")
    number = models.IntegerField(
        default=1, help_text="Number of individuals in this observation, for use with whole image annotation.")
    bounding_box = models.JSONField(default=dict, help_text="Bounding box of this observation in the format\
        {'x1':Left coordinate, 'y1':Bottom coordinate, 'x2': Right coordinate, 'y2': Left coordinate}.")
    confidence = models.FloatField(
        default=None, null=True, blank=True, help_text="Confidence of the observation from AI model.")
    extra_data = models.JSONField(
        default=dict, blank=True, help_text="Extra data that the standard fields do not cover")

    sex = models.CharField(max_length=10, blank=True,
                           help_text="Sex of the observed species, if known.")
    lifestage = models.CharField(
        max_length=15, blank=True, help_text="Lifestage of the observed species, if known.")
    behavior = models.CharField(
        max_length=50, blank=True, help_text="Behaviour of the observed species.")

    validation_requested = models.BooleanField(
        default=False, help_text="If True, this observation is requested for validation by a human expert.")
    validation_of = models.ManyToManyField(
        "self", symmetrical=False, related_name="validated_by",
        blank=True,
        help_text="If this observation is a validation of another observation, this field will contain the original observation(s).")

    objects = ObservationQuerySet.as_manager()

    def get_absolute_url(self):
        return f"/datafiles/{self.data_files.all().values_list('pk',flat=True)[0]}"

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

    def check_data_files_human(self):
        for data_file in self.data_files.all():
            data_file.check_human()


@receiver(m2m_changed, sender=Observation.data_files.through)
def update_observation_data_files(sender, instance, action, reverse, *args, **kwargs):

    if (action == 'post_add' or action == 'post_remove'):
        instance.save()


@receiver(post_delete, sender=Observation)
def check_human_delete(sender, instance, **kwargs):
    if instance.taxon.taxon_code == settings.HUMAN_TAXON_CODE:
        instance.check_data_files_human()


@receiver(post_save, sender=Observation)
def check_human_save(sender, instance, created, **kwargs):
    if instance.taxon.taxon_code == settings.HUMAN_TAXON_CODE:
        instance.check_data_files_human()
