from data_models.models import Deployment, Device, Project
from data_models.serializers import DeploymentSerializer, DeviceSerializer, ProjectSerializer
from django.contrib.auth.models import Group
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import User


class UserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    username = serializers.CharField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())]
    )

    password = serializers.CharField(write_only=True)

    def create(self, validated_data):
        user = User.objects.create_user(validated_data['username'], validated_data['email'],
                                        validated_data['password'],
                                        first_name=validated_data['first_name'],
                                        last_name=validated_data['last_name'])
        return user

    class Meta:
        model = User
        fields = ('id', 'username', 'password', 'email',
                  'first_name', 'last_name')


class UserProfileSerializer(serializers.ModelSerializer):

    owned_projects = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field='project_ID')
    managed_projects = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field='project_ID')
    owned_devices = DeviceSerializer(
        many=True, read_only=True)
    managed_devices = DeviceSerializer(
        many=True, read_only=True)
    owned_deployments = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field='deployment_device_ID')
    managed_deployments = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field='deployment_device_ID')

    class Meta:
        model = User
        fields = ('id', 'username', 'email',
                  'first_name', 'last_name',
                  'owned_projects', 'managed_projects',
                  'owned_devices', 'managed_devices',
                  'owned_deployments', 'managed_deployments',
                  )


# class GroupSerializer(serializers.ModelSerializer):

#     user_set = serializers.SlugRelatedField(many=True,
#                                             slug_field="username",
#                                             queryset=User.objects.all(),
#                                             allow_null=True,
#                                             required=False)

#     class Meta:
#         model = Group
#         fields = ['name', 'user_set',]


# class UserGroupMemberSerializer(serializers.ModelSerializer):
#     usergroup = GroupSerializer()

#     class Meta:
#         model = GroupProfile
#         fields = ['usergroup',]

#     def to_representation(self, instance):
#         initial_rep = super(UserGroupMemberSerializer,
#                             self).to_representation(instance)

#         print(initial_rep)

#         # all_members = [x[['user_set']] for x in initial_rep['usergroup']]

#         # return [x for y in all_members for x in y]
#         return initial_rep.get('usergroup').get('user_set')


# class UserGroupProfileSerializer(serializers.ModelSerializer):
#     usergroup = GroupSerializer()
#     project = serializers.SlugRelatedField(
#         many=True, read_only=True, slug_field='projectID')
#     deployment = serializers.SlugRelatedField(
#         many=True, read_only=True, slug_field='deployment_deviceID')
#     device = serializers.SlugRelatedField(
#         many=True, read_only=True, slug_field='deviceID')

#     class Meta:
#         model = GroupProfile
#         fields = ['usergroup', 'project', 'deployment', 'device']

#     def to_representation(self, instance):
#         initial_rep = super(UserGroupProfileSerializer,
#                             self).to_representation(instance)

#         all_fields = list(initial_rep.keys())
#         [initial_rep.pop(field, '')
#          for field in all_fields if initial_rep.get(field) == []]
#         initial_rep.update(initial_rep.pop('usergroup'))
#         return initial_rep


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['username'] = user.username
        return token
