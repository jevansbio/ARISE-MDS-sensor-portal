from django.utils import timezone as djtimezone
from rest_framework import serializers
from user_management.models import User


class SlugRelatedGetOrCreateField(serializers.SlugRelatedField):
    def to_internal_value(self, data):
        queryset = self.get_queryset()
        try:
            return queryset.get_or_create(**{self.slug_field: data})[0]
        except (TypeError, ValueError):
            self.fail("invalid")


class CheckFormMixIn():
    def __init__(self, *args, **kwargs):
        super(CheckFormMixIn, self).__init__(*args, **kwargs)
        self.form_submission = self.context.get("form")


class InstanceGetMixIn():
    def instance_get(self, attr_name, data):
        if attr_name in data:
            return data[attr_name]
        if self.instance and hasattr(self.instance, attr_name):
            return getattr(self.instance, attr_name)
        return None


class CreatedModifiedMixIn(serializers.ModelSerializer):
    created_on = serializers.DateTimeField(
        default_timezone=djtimezone.utc, read_only=True)
    modified_on = serializers.DateTimeField(
        default_timezone=djtimezone.utc, read_only=True)


class OwnerMixIn(serializers.ModelSerializer):
    owner = serializers.StringRelatedField(read_only=True)

    def to_representation(self, instance):
        initial_rep = super(OwnerMixIn, self).to_representation(instance)
        fields_to_pop = [
            'owner',
        ]
        if self.context.get('request'):
            initial_rep["user_is_owner"] = instance.owner == self.context['request'].user

        [initial_rep.pop(field, '') for field in fields_to_pop]
        return initial_rep


class ManagerMixIn(serializers.ModelSerializer):
    # user_is_manager = serializers.BooleanField(read_only=True, default = False)

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
