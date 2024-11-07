# Generated by Django 4.0 on 2024-11-05 13:06

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('data_models', '0001_initial'),
        ('user_management', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='annotators',
            field=models.ManyToManyField(blank=True, related_name='annotatable_projects', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='project',
            name='managers',
            field=models.ManyToManyField(blank=True, related_name='managed_projects', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='project',
            name='owner',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='owned_projects', to='user_management.user'),
        ),
        migrations.AddField(
            model_name='project',
            name='viewers',
            field=models.ManyToManyField(blank=True, related_name='viewable_projects', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='devicemodel',
            name='owner',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='owned_device_models', to='user_management.user'),
        ),
        migrations.AddField(
            model_name='devicemodel',
            name='type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='device_models', to='data_models.datatype'),
        ),
        migrations.AddField(
            model_name='device',
            name='annotators',
            field=models.ManyToManyField(blank=True, related_name='annotatable_devices', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='device',
            name='managers',
            field=models.ManyToManyField(blank=True, related_name='managed_devices', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='device',
            name='model',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='registered_devices', to='data_models.devicemodel'),
        ),
        migrations.AddField(
            model_name='device',
            name='owner',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='owned_devices', to='user_management.user'),
        ),
        migrations.AddField(
            model_name='device',
            name='type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='devices', to='data_models.datatype'),
        ),
        migrations.AddField(
            model_name='device',
            name='viewers',
            field=models.ManyToManyField(blank=True, related_name='viewable_devices', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='deployment',
            name='annotators',
            field=models.ManyToManyField(blank=True, related_name='annotatable_deployments', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='deployment',
            name='device',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='deployments', to='data_models.device'),
        ),
        migrations.AddField(
            model_name='deployment',
            name='device_type',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='deployments', to='data_models.datatype'),
        ),
        migrations.AddField(
            model_name='deployment',
            name='last_file',
            field=models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='deployment_last_file', to='data_models.datafile'),
        ),
        migrations.AddField(
            model_name='deployment',
            name='last_image',
            field=models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='deployment_last_image', to='data_models.datafile'),
        ),
        migrations.AddField(
            model_name='deployment',
            name='managers',
            field=models.ManyToManyField(blank=True, related_name='managed_deployments', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='deployment',
            name='owner',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='owned_deployments', to='user_management.user'),
        ),
        migrations.AddField(
            model_name='deployment',
            name='project',
            field=models.ManyToManyField(blank=True, related_name='deployments', to='data_models.Project'),
        ),
        migrations.AddField(
            model_name='deployment',
            name='site',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='deployments', to='data_models.site'),
        ),
        migrations.AddField(
            model_name='deployment',
            name='viewers',
            field=models.ManyToManyField(blank=True, related_name='viewable_deployments', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='datafile',
            name='deployment',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='files', to='data_models.deployment'),
        ),
        migrations.AddField(
            model_name='datafile',
            name='favourite_of',
            field=models.ManyToManyField(blank=True, related_name='favourites', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='datafile',
            name='file_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='files', to='data_models.datatype'),
        ),
    ]
