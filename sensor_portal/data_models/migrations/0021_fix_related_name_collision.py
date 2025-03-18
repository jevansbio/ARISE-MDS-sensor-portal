# Generated manually
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('external_storage_import', '0003_rename_service_password_datastorageinput_password_and_more'),
        ('data_models', '0020_load_initial_audio_data'),
    ]

    operations = [
        # First add the field if it doesn't exist
        migrations.AddField(
            model_name='deployment',
            name='input_storage',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='linked_deployments', to='external_storage_import.datastorageinput'),
        ),
    ] 