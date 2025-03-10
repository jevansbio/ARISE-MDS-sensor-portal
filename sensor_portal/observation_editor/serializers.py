from rest_framework import serializers
from utils.serializers import (CheckFormMixIn, CreatedModifiedMixIn,
                               OwnerMixIn, SlugRelatedGetOrCreateField)
from utils.validators import check_two_keys

from .models import Observation, Taxon


class TaxonSerializer(CreatedModifiedMixIn, serializers.ModelSerializer):
    class Meta:
        model = Taxon
        exclude = []


class ShortTaxonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Taxon
        exclude = ["id", "created_on", "modified_on", "parents"]

    def to_representation(self, instance):
        initial_rep = super(ShortTaxonSerializer,
                            self).to_representation(instance)
        initial_rep["taxon_extra_data"] = initial_rep.pop("extra_data")

        return initial_rep


class EvenShorterTaxonSerialier(serializers.ModelSerializer):
    class Meta:
        model = Taxon
        fields = ["id", "species_name", "species_common_name", "taxon_source"]


class ObservationSerializer(OwnerMixIn, CreatedModifiedMixIn, CheckFormMixIn, serializers.ModelSerializer):
    taxon_obj = ShortTaxonSerializer(source='taxon', read_only=True)
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
        return initial_rep

    def validate(self, data):
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
