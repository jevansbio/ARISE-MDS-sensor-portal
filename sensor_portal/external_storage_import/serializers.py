from rest_framework import serializers
from utils.serializers import CreatedModifiedMixIn, OwnerMixIn

from .models import DataStorageInput


class DataStorageInputSerializer(OwnerMixIn, CreatedModifiedMixIn, serializers.ModelSerializer):
    """
    Serializer for DataStorageInput model.
    Handles serialization and deserialization of DataStorageInput objects, including
    custom field visibility based on user permissions.
    """
    username = serializers.CharField(
        required=False,
        help_text="Optional username for accessing the external data storage."
    )
    password = serializers.CharField(
        required=False,
        write_only=True,
        help_text="Optional password for accessing the external data storage. Write-only for security."
    )

    class Meta:
        """
        Meta information for DataStorageInputSerializer.
        """
        model = DataStorageInput
        exclude = []

    def __init__(self, *args, **kwargs):
        """
        Initializes the serializer and sets the required management permission.
        """
        self.management_perm = 'data_models.change_datastorageinput'
        super().__init__(*args, **kwargs)

    def to_representation(self, instance):
        """
        Customize the representation of the DataStorageInput instance.
        Removes sensitive fields (username, address) from the output unless the user has management permissions.
        """
        initial_rep = super().to_representation(instance)
        fields_to_pop = [
            "username",
            "address"
        ]

        if self.context.get('request'):
            user_is_manager = self.context['request'].user.has_perm(
                self.management_perm, obj=instance)
        else:
            user_is_manager = False
        if not user_is_manager:
            [initial_rep.pop(field, '') for field in fields_to_pop]

        return initial_rep
