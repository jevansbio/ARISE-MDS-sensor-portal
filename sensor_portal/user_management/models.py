from data_models.models import Deployment, Device, Project
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import AbstractUser, Group
from django.contrib.sites.models import Site
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models import BooleanField, ExpressionWrapper, Q
from django.db.models.signals import m2m_changed, post_save, pre_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from rest_framework.authtoken.models import Token


class User(AbstractUser):
    """
    Custom user model that extends Django's AbstractUser to include additional fields
    such as organisation and bio, and to manage device users.   
    """
    is_active = models.BooleanField(
        _('active'),
        default=False,
        help_text=_(
            'Designates whether this user should be treated as active. '
            'Unselect this instead of deleting accounts.'
        ),
    )
    organisation = models.CharField(
        max_length=100, blank=True, help_text="User organisation.")
    bio = models.CharField(max_length=200, blank=True,
                           help_text="User self description.")


class DeviceUser(User):
    """
    DeviceUser model that extends the User model to represent a user associated with a specific device.
    """
    device = models.OneToOneField(
        Device, related_name="device_user", on_delete=models.CASCADE, null=True, help_text="Device linked to this device user.")
    organisation = None
    bio = None

    class Meta:
        verbose_name = "DeviceUser"
        verbose_name_plural = "DeviceUsers"

    pass
