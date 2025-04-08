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
        rep = super().to_representation(instance)
        rep["taxon_extra_data"] = rep.pop("extra_data")
        return rep


class EvenShorterTaxonSerialier(serializers.ModelSerializer):
    class Meta:
        model = Taxon
        fields = ["id", "species_name", "species_common_name", "taxon_source"]


class ObservationSerializer(OwnerMixIn, CreatedModifiedMixIn, CheckFormMixIn, serializers.ModelSerializer):
    taxon_obj = ShortTaxonSerializer(source='taxon', read_only=True)
    taxon = serializers.PrimaryKeyRelatedField(
        queryset=Taxon.objects.all(),
        required=False
    )
    species_name = SlugRelatedGetOrCreateField(
        many=False,
        source="taxon",
        slug_field="species_name",
        queryset=Taxon.objects.all(),
        allow_null=True,
        required=False,
        read_only=False
    )
    data_files = serializers.SerializerMethodField()

    def get_data_files(self, obj):
        return [{
            'id': df.id,
            'file_name': df.file_name,
            'deployment': {
                'name': df.deployment.deployment_device_ID if df.deployment else None,
                'device': {
                    'name': df.deployment.device.name if df.deployment and df.deployment.device else None
                }
            } if df.deployment else None
        } for df in obj.data_files.all()]

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep.pop("species_name")
        
        taxon = instance.taxon
        rep['taxon'] = {
            'id': taxon.id,
            'species_name': taxon.species_name,
            'species_common_name': taxon.species_common_name
        } if taxon else None
            
        return rep

    def to_internal_value(self, data):
        if 'taxon' in data and isinstance(data['taxon'], dict):
            taxon_data = data['taxon']
            if 'id' in taxon_data:
                data['taxon'] = taxon_data['id']
            elif 'species_name' in taxon_data:
                data['species_name'] = taxon_data['species_name']
        return super().to_internal_value(data)

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
