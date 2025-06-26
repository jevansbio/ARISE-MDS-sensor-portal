from django.utils import timezone as djtimezone
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from user_management.models import User


@extend_schema_field({"type": ["object"],
                      })
class DummyJSONField(serializers.Field):
    def to_representation(self, value):
        return {}

    def to_internal_value(self, data):
        return {}


class SlugRelatedGetOrCreateField(serializers.SlugRelatedField):
    """
    A SlugRelatedField that retrieves or creates an object based on the slug field.

    """

    def to_internal_value(self, data):
        queryset = self.get_queryset()
        try:
            return queryset.get_or_create(**{self.slug_field: data})[0]
        except (TypeError, ValueError):
            self.fail("invalid")


class CheckFormMixIn():
    """
    A mixin to check if the data was submitted through a form.
    It retrieves the form submission from the context and makes it available
    as `self.form_submission` in the serializer.
    """

    def __init__(self, *args, **kwargs):
        super(CheckFormMixIn, self).__init__(*args, **kwargs)
        self.form_submission = self.context.get("form")


class InstanceGetMixIn():
    """
    A mixin to retrieve an attribute from the instance or data.
    If the attribute is not found in the data, it checks if the instance has the attribute.
    If the attribute is found in the instance, it returns that value; otherwise, it returns None.
    """

    def instance_get(self, attr_name: str, data: dict) -> any:
        if attr_name in data:
            return data[attr_name]
        if self.instance and hasattr(self.instance, attr_name):
            return getattr(self.instance, attr_name)
        return None


class CreatedModifiedMixIn(serializers.ModelSerializer):
    """
    A mixin to add created_on and modified_on fields to a serializer.
    """
    created_on = serializers.DateTimeField(
        default_timezone=djtimezone.utc, read_only=True, required=False)
    modified_on = serializers.DateTimeField(
        default_timezone=djtimezone.utc, read_only=True, required=False)


class OwnerMixIn(serializers.ModelSerializer):
    """
    A mixin to add owner information to a serializer.
    It includes a read-only field for the owner and a boolean field to indicate if the user is the owner.
    The `to_representation` method customizes the output to include the owner and user_is_owner fields.
    The owner field is removed from the final representation.
    """
    owner = serializers.StringRelatedField(read_only=True)

    def to_representation(self, instance):
        initial_rep = super(OwnerMixIn, self).to_representation(instance)
        fields_to_pop = [
            'owner',
        ]

        if self.context.get('request'):
            initial_rep["user_is_owner"] = self.context['request'].user.is_superuser or (
                instance.owner == self.context['request'].user)

        [initial_rep.pop(field, '') for field in fields_to_pop]
        return initial_rep


class ManagerMixIn(serializers.ModelSerializer):
    """
    A mixin to add management-related fields to a serializer.
    It includes fields for managers, annotators, and viewers, allowing them to be set by slug or primary key.
    The `to_representation` method customizes the output to include user permissions and conditionally
    removes management-related fields based on the user's permissions.
    The `update` method ensures that the instance is saved after updating the management-related fields.

    """

    managers = serializers.SlugRelatedField(many=True,
                                            slug_field="username",
                                            queryset=User.objects.all(),
                                            allow_null=True,
                                            required=False,
                                            read_only=False)

    managers_ID = serializers.PrimaryKeyRelatedField(source="managers", many=True, queryset=User.objects.all(),
                                                     required=False)

    annotators = serializers.SlugRelatedField(many=True,
                                              slug_field="username",
                                              queryset=User.objects.all(),
                                              allow_null=True,
                                              required=False,
                                              read_only=False)

    annotators_ID = serializers.PrimaryKeyRelatedField(source="annotators", many=True, queryset=User.objects.all(),
                                                       required=False)

    viewers = serializers.SlugRelatedField(many=True,
                                           slug_field="username",
                                           queryset=User.objects.all(),
                                           allow_null=True,
                                           required=False,
                                           read_only=False)

    viewers_ID = serializers.PrimaryKeyRelatedField(source="viewers", many=True, queryset=User.objects.all(),
                                                    required=False)

    # viewers = UserGroupMemberSerializer(
    #     many=True, read_only=False, source='usergroup')
    # annotators = UserGroupMemberSerializer(
    #     many=True, read_only=False, source='usergroup')

    def to_representation(self, instance):
        initial_rep = super(ManagerMixIn, self).to_representation(instance)
        fields_to_pop = [
            'managers',
            'annotators'
            'viewers',
        ]
        if self.context.get('request'):
            initial_rep['user_is_manager'] = self.context['request'].user.has_perm(
                self.management_perm, obj=instance)

            if not initial_rep['user_is_manager']:
                [initial_rep.pop(field, '') for field in fields_to_pop]

        else:
            [initial_rep.pop(field, '') for field in fields_to_pop]

        return initial_rep

    def update(self, instance, validated_data):
        instance = super(ManagerMixIn, self).update(
            instance, validated_data)

        instance.save()
        return instance

    # def add_users_to_group(usernames, group):
    #     if usernames:
    #         group.user_set.clear()
    #         users_to_add = User.objects.all().filter(
    #             username__in=usernames)
    #         for user in users_to_add:
    #             group.user_set.add(user)
    #         group.save()
