from data_models.models import Deployment, Device, Project
from data_models.serializers import (DeploymentSerializer, DeviceSerializer,
                                     ProjectSerializer)
from django.contrib.auth.password_validation import (
    CommonPasswordValidator, MinimumLengthValidator, NumericPasswordValidator,
    UserAttributeSimilarityValidator)
from drf_recaptcha.fields import ReCaptchaV3Field
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import User


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for the User model, used for displaying basic user information.
    """
    email = serializers.EmailField(
        required=True,
        # validators=[UniqueValidator(queryset=User.objects.all())]
    )
    username = serializers.CharField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())]
    )

    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    recaptcha = ReCaptchaV3Field(
        action="register",
        required_score=0.8,
    )

    def create(self, validated_data):
        user = User.objects.create_user(validated_data['username'],
                                        validated_data['email'],
                                        validated_data['password'],
                                        first_name=validated_data['first_name'],
                                        last_name=validated_data['last_name'],
                                        bio=validated_data['bio'],
                                        organisation=validated_data['organisation'])
        return user

    def validate(self, data):
        if data.get('password') != data.get('confirm_password'):
            raise serializers.ValidationError("Passwords don't match.")

        data = super().validate(data)
        return data

    class Meta:
        model = User
        fields = ('id', 'username', 'password', 'bio', 'confirm_password', 'email',
                  'first_name', 'last_name', 'organisation', 'recaptcha')


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for the User model, used for displaying extensive user information for profile views.
    This serializer includes related fields for projects, devices, and deployments owned, managed, annotatable, and viewable by the user.
    It is used to provide a comprehensive overview of the user's interactions with the system.
    """
    owned_projects = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field='project_ID', help_text="Project ID of projects owned by the user.")
    owned_projects_ID = serializers.PrimaryKeyRelatedField(
        many=True, read_only=True, source='owned_projects', help_text="Database ID of projects owned by the user.")
    managed_projects = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field='project_ID', help_text="Project ID of projects managed by the user.")
    managed_projects_ID = serializers.PrimaryKeyRelatedField(
        many=True, read_only=True, source='managed_projects', help_text="Database ID of projects managed by the user.")
    annotatable_projects = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field='project_ID', help_text="Project ID of projects annotatable by the user.")
    annotatable_projects_ID = serializers.PrimaryKeyRelatedField(
        many=True, read_only=True, source='annotatable_projects', help_text="Database ID of projects annotatable by the user.")
    viewable_projects = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field='project_ID', help_text="Project ID of projects viewable by the user.")
    viewable_projects_ID = serializers.PrimaryKeyRelatedField(
        many=True, read_only=True, source='viewable_projects', help_text="Database ID of projects viewable by the user.")

    owned_devices = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field='device_ID', help_text="Device ID of devices owned by the user.")
    owned_devices_ID = serializers.PrimaryKeyRelatedField(
        many=True, read_only=True, source='owned_devices', help_text="Database ID of devices owned by the user.")
    managed_devices = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field='device_ID', help_text="Device ID of devices managed by the user.")
    managed_devices_ID = serializers.PrimaryKeyRelatedField(
        many=True, read_only=True, source='managed_devices', help_text="Database ID of devices managed by the user.")
    annotatable_devices = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field='device_ID', help_text="Device ID of devices annotatable by the user.")
    annotatable_devices_ID = serializers.PrimaryKeyRelatedField(
        many=True, read_only=True, source='annotatable_devices', help_text="Database ID of devices annotatable by the user.")
    viewable_devices = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field='device_ID', help_text="Device ID of devices viewable by the user.")
    viewable_devices_ID = serializers.PrimaryKeyRelatedField(
        many=True, read_only=True, source='viewable_devices', help_text="Database ID of devices viewable by the user.")

    owned_deployments = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field='deployment_device_ID', help_text="Deployment device ID of deployments owned by the user.")
    owned_deployments_ID = serializers.PrimaryKeyRelatedField(
        many=True, read_only=True, source='owned_deployments', help_text="Database ID of deployments owned by the user.")
    managed_deployments = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field='deployment_device_ID', help_text="Deployment device ID of manageable managed by the user.")
    managed_deployments_ID = serializers.PrimaryKeyRelatedField(
        many=True, read_only=True, source='managed_deployments', help_text="Database ID of deployments manageable by the user.")
    annotatable_deployments = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field='deployment_device_ID', help_text="Deployment device ID of deployments annotatable by the user.")
    annotatable_deployments_ID = serializers.PrimaryKeyRelatedField(
        many=True, read_only=True, source='annotatable_deployments', help_text="Database ID of deployments annotatable by the user.")
    viewable_deployments = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field='deployment_device_ID', help_text="Deployment device ID of deployments viewable by the user.")
    viewable_deployments_ID = serializers.PrimaryKeyRelatedField(
        many=True, read_only=True, source='viewable_deployments', help_text="Database ID of deployments viewable by the user.")

    class Meta:
        model = User
        fields = ('id', 'username', 'email',
                  'first_name', 'last_name',
                  'bio', 'organisation',
                  'owned_projects', 'owned_projects_ID',
                  'managed_projects', 'managed_projects_ID',
                  'annotatable_projects', 'annotatable_projects_ID',
                  'viewable_projects', 'viewable_projects_ID',
                  'owned_devices', 'owned_devices_ID',
                  'managed_devices', 'managed_devices_ID',
                  'annotatable_devices', 'annotatable_devices_ID',
                  'viewable_devices', 'viewable_devices_ID',
                  'owned_deployments', 'owned_deployments_ID',
                  'managed_deployments', 'managed_deployments_ID',
                  'annotatable_deployments', 'annotatable_deployments_ID',
                  'viewable_deployments', 'viewable_deployments_ID'
                  )


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom serializer for obtaining JWT tokens, extending the default TokenObtainPairSerializer to use captcha validation.
    """
    recaptcha = ReCaptchaV3Field(
        action="login",
        required_score=0.6,
    )

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['username'] = user.username
        token['id'] = user.pk
        return token
