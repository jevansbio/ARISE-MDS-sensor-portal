from drf_spectacular.utils import (OpenApiExample, OpenApiParameter,
                                   OpenApiTypes, extend_schema,
                                   extend_schema_field,
                                   extend_schema_serializer)
from rest_framework import serializers
from utils.serializers import DummyJSONField, SlugRelatedGetOrCreateField

from .models import Observation, Taxon
from .serializers import ObservationSerializer


@extend_schema_field({"type": ["object"],
                      "readOnly": False,
                      "default": {},
                      "description": "Bounding box of this observation",
                      'examples': [{"x1": 0, "y1": 0, "x2": 1, "y2": 1}],
                      "properties": {"x1": {"type": "number",
                                            "description": "Left coordinate",
                                            "required": True, },
                                     "y1": {"type": "number",
                                            "description": "Bottom coordinate",
                                            "required": True},
                                     "x2": {"type": "number",
                                            "description": "Right coordinate",
                                            "required": True},
                                     "y2": {"type": "number",
                                            "description": "Top coordinate",
                                            "required": True}},
                      "required": False,
                      })
class BBoxField(DummyJSONField):
    pass


@extend_schema_serializer(component_name="ObservationSerializer",
                          )
class DummyObservationSerializer(ObservationSerializer):
    """
    For use in the API schema.
    """
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
    user_is_owner = serializers.BooleanField(
        read_only=True, default=False, required=False)

    taxon_obj = None

    taxonomic_level_name = serializers.CharField(
        read_only=True, default="species", required=False)
    species_common_name = serializers.CharField(read_only=True, required=False)
    taxon_code = serializers.CharField(read_only=True, required=False)
    taxon_source = serializers.IntegerField(
        read_only=True, default=0, required=False)
    taxonomic_level = serializers.IntegerField(
        read_only=True, default=0, required=False)
    taxon_extra_data = serializers.SerializerMethodField(
        read_only=True,  required=False)

    @extend_schema_field({"type": ["object"],
                          "description": "Extra taxon data that the standard fields do not cover.",
                          "additionalProperties": True,
                          "default": {},
                          'examples': [{"comment": "This is a large bird"}]
                          })
    def get_taxon_extra_data(self, object):
        return {}

    annotated_by = serializers.CharField(
        read_only=True, default=None, required=False)

    bounding_box = BBoxField(required=False)

    extra_data = DummyJSONField(
        required=False, help_text="Extra taxon data that the standard fields do not cover.")
