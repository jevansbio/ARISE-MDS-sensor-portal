# Generated by Django 4.2 on 2025-01-27 11:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data_models', '0013_device_input_storage_project_data_storages'),
    ]

    operations = [
        migrations.AlterField(
            model_name='datafile',
            name='file_name',
            field=models.CharField(max_length=100, unique=True),
        ),
    ]
