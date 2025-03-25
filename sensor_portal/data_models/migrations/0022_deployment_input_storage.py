# Generated manually
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('external_storage_import', '0003_rename_service_password_datastorageinput_password_and_more'),
        ('data_models', '0021_fix_related_name_collision'),
    ]

    operations = [
        # Field already exists in the database, so this is a no-op migration
        # It just helps Django recognize the field in its state
    ] 