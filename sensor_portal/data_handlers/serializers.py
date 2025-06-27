from rest_framework import serializers


class DataHandlerSerializer(serializers.Serializer):
    """
    Serializer for data handler objects in the sensor portal.
    Captures supported data types, device models, and various descriptions
    relevant to data handling and post-processing.
    """
    id = serializers.IntegerField(
        read_only=True,
        help_text="Unique identifier for the data handler."
    )
    data_types = serializers.ListField(
        child=serializers.CharField(max_length=100),
        allow_empty=True,
        help_text="List of supported data types for this handler."
    )
    device_models = serializers.ListField(
        child=serializers.CharField(max_length=100),
        allow_empty=True,
        help_text="List of compatible device models for this handler."
    )
    safe_formats = serializers.ListField(
        child=serializers.CharField(max_length=10),
        allow_empty=True,
        help_text="List of safe output data formats."
    )
    full_name = serializers.CharField(
        max_length=100,
        help_text="Full name of the data handler."
    )
    description = serializers.CharField(
        max_length=100,
        help_text="Short description of the data handler."
    )
    validity_description = serializers.CharField(
        max_length=500,
        help_text="Description of data validity checks performed."
    )
    handling_description = serializers.CharField(
        max_length=500,
        help_text="Description of how the data is handled."
    )
    post_handling_description = serializers.CharField(
        max_length=500,
        help_text="Description of post-handling steps taken after processing."
    )
