# Generated by Django 4.0 on 2024-11-06 10:37

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('data_models', '0002_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='deployment',
            old_name='deploymentEnd',
            new_name='deployment_end',
        ),
        migrations.RenameField(
            model_name='deployment',
            old_name='deploymentStart',
            new_name='deployment_start',
        ),
    ]
