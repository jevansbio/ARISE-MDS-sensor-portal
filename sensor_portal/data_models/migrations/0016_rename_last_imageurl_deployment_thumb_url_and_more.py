# Generated by Django 4.2 on 2025-02-10 09:53

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('data_models', '0015_rename_extra_versions_datafile_linked_files_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='deployment',
            old_name='last_imageURL',
            new_name='thumb_url',
        ),
        migrations.RemoveField(
            model_name='deployment',
            name='last_file',
        ),
    ]
