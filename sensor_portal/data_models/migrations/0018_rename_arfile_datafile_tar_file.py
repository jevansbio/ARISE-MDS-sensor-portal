# Generated by Django 4.2 on 2025-02-10 14:46

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('data_models', '0017_remove_project_archive_files_datafile_arfile_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='datafile',
            old_name='arfile',
            new_name='tar_file',
        ),
    ]
