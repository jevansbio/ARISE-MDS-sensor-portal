from django.db import models
from django.contrib.auth.models import AbstractUser, Group
from rest_framework.authtoken.models import Token
from django.dispatch import receiver
from django.db.models.signals import post_save, pre_save, m2m_changed
from django.db.models import Q, BooleanField, ExpressionWrapper
from data_models.models import Project, Deployment, Device
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.hashers import make_password
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    is_active = models.BooleanField(
        _('active'),
        default=False,
        help_text=_(
            'Designates whether this user should be treated as active. '
            'Unselect this instead of deleting accounts.'
        ),
    )
    pass


class DeviceUser(User):
    device = models.OneToOneField(
        Device, related_name="device_user", on_delete=models.CASCADE, null=True)

    class Meta:
        verbose_name = "DeviceUser"
        verbose_name_plural = "DeviceUsers"

    pass


@receiver(post_save, sender=DeviceUser)
def check_device_user_is_manager(sender, instance, created, **kwargs):
    if not instance.device.managers.all().filter(pk=instance.pk).exists():
        instance.device.managers.add(instance)


@receiver(post_save, sender=Device)
def post_save_device(sender, instance, created, **kwargs):
    add_device_user = False
    if created:
        add_device_user = True
    else:
        try:
            device_user = instance.device_user
        except ObjectDoesNotExist:
            add_device_user = True

    if add_device_user:
        user_name = f"{instance.device_ID}_user"
        if (instance.username is not None) and (instance.username != ":"):
            user_name = instance.username
        device_user = DeviceUser(username=user_name,
                                 device=instance,
                                 is_active=True)
        # if (instance.password is not None) and (instance.password != ""):
        #     device_user.password = instance.password
        if instance.owner:
            device_user.email = instance.owner.email
        device_user.save()

    # always make sure device user as a manager
    instance.managers.add(device_user)


@receiver(pre_save, sender=DeviceUser)
@receiver(pre_save, sender=User)
def pre_user_save(sender, instance, **kwargs):
    if isinstance(instance, DeviceUser):
        instance.is_active = True
    elif instance.is_superuser:
        instance.is_active = True


@receiver(post_save, sender=DeviceUser)
@receiver(post_save, sender=User)
def create_user_token(sender, instance, created, **kwargs):
    if created:
        newtoken = Token(user=instance)
        # if isinstance(instance, DeviceUser):
        #     if (instance.device.password is not None) & (instance.device.password != ""):
        #         newtoken.key = instance.device.password
        newtoken.save()

    # if isinstance(instance, DeviceUser):
    #     if ((instance.password is None) | (instance.password == "")):
    #         User.objects.filter(pk=instance.pk).update(
    #             password=make_password(instance.auth_token.key))

# def create_user_group(group_name):
#     try:
#         usergroup = Group.objects.get(name=group_name)
#     except ObjectDoesNotExist:
#         usergroup = Group(name=group_name)
#         usergroup.save()
#     return usergroup

# Users now linked directly to the relevant objects
# class GroupProfile(models.Model):
#     usergroup = models.OneToOneField(
#         Group, on_delete=models.CASCADE, related_name='profile')
#     project = models.ManyToManyField(Project, related_name="usergroup")
#     deployment = models.ManyToManyField(Deployment, related_name="usergroup")
#     device = models.ManyToManyField(Device, related_name="usergroup")

#     def __str__(self):
#         return (self.usergroup.name + " profile")


# @receiver(post_save, sender=Group)
# def create_user_group_profile(sender, instance, created, **kwargs):
#     if not getattr(instance, 'from_admin_site', False):
#         if created:
#             GroupProfile.objects.create(usergroup=instance)


# @receiver(post_save, sender=Group)
# def save_user_group_profile(sender, instance, **kwargs):
#     if not getattr(instance, 'from_admin_site', False):
#         instance.profile.save()
