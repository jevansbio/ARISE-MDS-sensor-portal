from drf_spectacular.utils import (OpenApiExample, OpenApiParameter,
                                   OpenApiTypes, extend_schema,
                                   extend_schema_field,
                                   extend_schema_serializer)
from rest_framework import serializers
from utils.serializers import (CheckFormMixIn, CreatedModifiedMixIn,
                               DummyJSONField, OwnerMixIn,
                               SlugRelatedGetOrCreateField)
from utils.validators import check_two_keys

from .models import Observation, Taxon


class TaxonSerializer(CreatedModifiedMixIn, serializers.ModelSerializer):
    """
    Serializer for the Taxon model, including all fields.
    Adds a read-only field for the taxonomic level display name.
    """
    taxonomic_level_name = serializers.CharField(
        source="get_taxonomic_level_display", read_only=True)

    class Meta:
        model = Taxon
        exclude = []


class ShortTaxonSerializer(serializers.ModelSerializer):
    """
    A shorter serializer for the Taxon model, excluding certain fields.
    Adds the taxonomic level display, and renames 'extra_data' to 'taxon_extra_data' in output.
    """

    taxonomic_level_name = serializers.CharField(
        source="get_taxonomic_level_display", read_only=True)

    class Meta:
        model = Taxon
        exclude = ["id", "created_on", "modified_on", "parents"]

    def to_representation(self, instance):
        """
        Customize the output representation by renaming 'extra_data' to 'taxon_extra_data'.
        """
        initial_rep = super(ShortTaxonSerializer,
                            self).to_representation(instance)
        initial_rep["taxon_extra_data"] = initial_rep.pop("extra_data")

        return initial_rep


class EvenShorterTaxonSerialier(serializers.ModelSerializer):
    """
    An even more concise serializer for the Taxon model, exposing only a few fields.
    Adds a combined string of species name and common name.
    """
    class Meta:
        model = Taxon
        fields = ["id", "species_name", "species_common_name", "taxon_source"]

    def to_representation(self, instance):
        """
        Adds a 'full_string' field combining species name and common name.
        """
        initial_rep = super(EvenShorterTaxonSerialier,
                            self).to_representation(instance)
        initial_rep["full_string"] = f"{initial_rep.get('species_name')} - {initial_rep.get('species_common_name')}"
        return initial_rep


class ObservationSerializer(OwnerMixIn, CreatedModifiedMixIn, CheckFormMixIn, serializers.ModelSerializer):
    """
    Serializer for the Observation model, providing detailed taxon handling.
    Handles relationships to Taxon and customizes output based on context.
    """
    taxon_obj = ShortTaxonSerializer(
        source='taxon', read_only=True, required=False)
    taxon = serializers.PrimaryKeyRelatedField(
        queryset=Taxon.objects.all(),
        required=False)
    species_name = SlugRelatedGetOrCreateField(many=False,
                                               source="taxon",
                                               slug_field="species_name",
                                               queryset=Taxon.objects.all(),
                                               allow_null=True,
                                               required=False,
                                               read_only=False)

    def to_representation(self, instance):
        """
        Customizes output: handles target taxon levels, annotator display, and merging taxon info.
        """
        initial_rep = super(ObservationSerializer,
                            self).to_representation(instance)
        initial_rep.pop("species_name")
        original_taxon_obj = initial_rep.pop("taxon_obj")
        if (target_taxon_level := self.context.get("target_taxon_level")) is not None:
            target_taxon_level = int(target_taxon_level)

            if original_taxon_obj["taxonomic_level"] == target_taxon_level:
                initial_rep.update(original_taxon_obj)
            else:
                try:
                    new_taxon_obj = Taxon.objects.get(
                        pk=instance.parent_taxon_pk)
                except Taxon.DoesNotExist:
                    new_taxon_obj = None

                if new_taxon_obj is not None:
                    new_taxon_dict = ShortTaxonSerializer(new_taxon_obj).data
                    initial_rep.update(new_taxon_dict)
                else:
                    return None

        else:
            initial_rep.update(original_taxon_obj)

        if instance.owner:
            initial_rep["annotated_by"] = f"{instance.owner.first_name} {instance.owner.last_name}"
        else:
            initial_rep["annotated_by"] = None

        return initial_rep

    def validate(self, data):
        """
        Validates that either 'taxon' or 'species_name' is provided during creation,
        using custom two-key check logic.
        """
        data = super().validate(data)
        if not self.partial:
            result, message, data = check_two_keys(
                'taxon',
                'species_name',
                data,
                Taxon,
                self.form_submission
            )
            if not result:
                raise serializers.ValidationError(message)
        return data

    class Meta:
        model = Observation
        exclude = []
