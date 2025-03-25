# Generated manually
from django.db import migrations, models
import django.db.models.deletion
from django.contrib.postgres.operations import UnaccentExtension
from django.utils import timezone
import encrypted_model_fields.fields

class Migration(migrations.Migration):

    dependencies = [
        ('archiving', '0001_initial'),
        ('external_storage_import', '0003_rename_service_password_datastorageinput_password_and_more'),
        ('data_models', '0022_deployment_input_storage'),  # Changed dependency from 0023 to 0022
    ]

    operations = [
        # Just update the model state with fields in their current names
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                # First the ForeignKey field that was already added in 0022 but may need state update
                migrations.AddField(
                    model_name='deployment',
                    name='input_storage',
                    field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='linked_deployments', to='external_storage_import.datastorageinput'),
                ),
                # Then the JSON fields that might be renamed in the database
                migrations.AddField(
                    model_name='device',
                    name='extra_data',
                    field=models.JSONField(blank=True, default=dict),
                ),
                migrations.AddField(
                    model_name='deployment',
                    name='extra_data',
                    field=models.JSONField(blank=True, default=dict),
                ),
                migrations.AddField(
                    model_name='datafile',
                    name='extra_data',
                    field=models.JSONField(blank=True, default=dict),
                ),
                migrations.AddField(
                    model_name='datafile',
                    name='linked_files',
                    field=models.JSONField(blank=True, default=dict),
                ),
                # Boolean fields that might already exist
                migrations.AddField(
                    model_name='datafile',
                    name='do_not_remove',
                    field=models.BooleanField(default=False),
                ),
                migrations.AddField(
                    model_name='datafile',
                    name='local_storage',
                    field=models.BooleanField(default=True),
                ),
                
                # Add fields that are actually in the model with their current names
                migrations.AddField(
                    model_name='deployment',
                    name='deployment_start',
                    field=models.DateTimeField(default=timezone.now),
                ),
                migrations.AddField(
                    model_name='deployment',
                    name='deployment_end',
                    field=models.DateTimeField(blank=True, null=True),
                ),
                migrations.AddField(
                    model_name='deployment',
                    name='deployment_device_ID',
                    field=models.CharField(blank=True, editable=False, max_length=100, unique=True),
                ),
                migrations.AddField(
                    model_name='deployment',
                    name='deployment_ID',
                    field=models.CharField(max_length=50),
                ),
                migrations.AddField(
                    model_name='device',
                    name='device_ID',
                    field=models.CharField(max_length=20, unique=True),
                ),
                migrations.AddField(
                    model_name='project',
                    name='project_ID',
                    field=models.CharField(blank=True, max_length=10, unique=True),
                ),
                migrations.AddField(
                    model_name='deployment',
                    name='latitude',
                    field=models.DecimalField(blank=True, decimal_places=6, max_digits=8, null=True),
                ),
                migrations.AddField(
                    model_name='deployment',
                    name='longitude',
                    field=models.DecimalField(blank=True, decimal_places=6, max_digits=8, null=True),
                ),
                migrations.AddField(
                    model_name='datafile',
                    name='upload_dt',
                    field=models.DateTimeField(default=timezone.now),
                ),
                # Relationship fields
                migrations.AddField(
                    model_name='datafile',
                    name='tar_file',
                    field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='files', to='archiving.tarfile'),
                ),
                migrations.AddField(
                    model_name='project',
                    name='archive',
                    field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='linked_projects', to='archiving.archive'),
                ),
                migrations.AddField(
                    model_name='project',
                    name='data_storages',
                    field=models.ManyToManyField(blank=True, related_name='linked_projects', to='external_storage_import.datastorageinput'),
                ),
                # Make sure thumb_url fields have the right properties
                migrations.AlterField(
                    model_name='datafile',
                    name='thumb_url',
                    field=models.CharField(blank=True, max_length=500, null=True),
                ),
                migrations.AlterField(
                    model_name='deployment',
                    name='thumb_url',
                    field=models.CharField(blank=True, max_length=500, null=True),
                ),
                migrations.AlterField(
                    model_name='site',
                    name='short_name',
                    field=models.CharField(blank=True, max_length=10),
                ),
                
                # Fields from 0023 that weren't in 0024
                migrations.AddField(
                    model_name='deployment',
                    name='battery_level',
                    field=models.FloatField(blank=True, null=True),
                ),
                migrations.AddField(
                    model_name='deployment',
                    name='comment',
                    field=models.TextField(blank=True, null=True),
                ),
                migrations.AddField(
                    model_name='deployment',
                    name='coordinate_uncertainty',
                    field=models.CharField(blank=True, max_length=100, null=True),
                ),
                migrations.AddField(
                    model_name='deployment',
                    name='country',
                    field=models.CharField(blank=True, max_length=100, null=True),
                ),
                migrations.AddField(
                    model_name='deployment',
                    name='gps_device',
                    field=models.CharField(blank=True, max_length=100, null=True),
                ),
                migrations.AddField(
                    model_name='deployment',
                    name='habitat',
                    field=models.CharField(blank=True, max_length=100, null=True),
                ),
                migrations.AddField(
                    model_name='deployment',
                    name='mic_direction',
                    field=models.CharField(blank=True, max_length=100, null=True),
                ),
                migrations.AddField(
                    model_name='deployment',
                    name='mic_height',
                    field=models.FloatField(blank=True, null=True),
                ),
                migrations.AddField(
                    model_name='deployment',
                    name='password',
                    field=encrypted_model_fields.fields.EncryptedCharField(blank=True, null=True),
                ),
                migrations.AddField(
                    model_name='deployment',
                    name='protocol_checklist',
                    field=models.CharField(blank=True, max_length=255, null=True),
                ),
                migrations.AddField(
                    model_name='deployment',
                    name='score',
                    field=models.FloatField(blank=True, null=True),
                ),
                migrations.AddField(
                    model_name='deployment',
                    name='site_name',
                    field=models.CharField(blank=True, max_length=100, null=True),
                ),
                migrations.AddField(
                    model_name='deployment',
                    name='user_email',
                    field=models.EmailField(blank=True, max_length=254, null=True),
                ),
                migrations.AddField(
                    model_name='device',
                    name='battery_level',
                    field=models.FloatField(blank=True, null=True),
                ),
                migrations.AddField(
                    model_name='device',
                    name='comment',
                    field=models.TextField(blank=True, null=True),
                ),
                migrations.AddField(
                    model_name='device',
                    name='coordinate_uncertainty',
                    field=models.CharField(blank=True, max_length=100, null=True),
                ),
                migrations.AddField(
                    model_name='device',
                    name='country',
                    field=models.CharField(blank=True, max_length=100, null=True),
                ),
                migrations.AddField(
                    model_name='device',
                    name='end_date',
                    field=models.DateTimeField(blank=True, null=True),
                ),
                migrations.AddField(
                    model_name='device',
                    name='gps_device',
                    field=models.CharField(blank=True, max_length=100, null=True),
                ),
                migrations.AddField(
                    model_name='device',
                    name='habitat',
                    field=models.CharField(blank=True, max_length=100, null=True),
                ),
                migrations.AddField(
                    model_name='device',
                    name='mic_direction',
                    field=models.CharField(blank=True, max_length=100, null=True),
                ),
                migrations.AddField(
                    model_name='device',
                    name='mic_height',
                    field=models.FloatField(blank=True, null=True),
                ),
                migrations.AddField(
                    model_name='device',
                    name='protocol_checklist',
                    field=models.CharField(blank=True, max_length=255, null=True),
                ),
                migrations.AddField(
                    model_name='device',
                    name='score',
                    field=models.FloatField(blank=True, null=True),
                ),
                migrations.AddField(
                    model_name='device',
                    name='site_name',
                    field=models.CharField(blank=True, max_length=100, null=True),
                ),
                migrations.AddField(
                    model_name='device',
                    name='start_date',
                    field=models.DateTimeField(blank=True, null=True),
                ),
                migrations.AddField(
                    model_name='device',
                    name='user_email',
                    field=models.EmailField(blank=True, max_length=254, null=True),
                ),
                migrations.AddField(
                    model_name='datafile',
                    name='config',
                    field=models.CharField(blank=True, max_length=100, null=True),
                ),
                migrations.AddField(
                    model_name='datafile',
                    name='file_length',
                    field=models.CharField(blank=True, max_length=50, null=True),
                ),
                migrations.AddField(
                    model_name='datafile',
                    name='sample_rate',
                    field=models.IntegerField(blank=True, null=True),
                ),
            ]
        ),
    ] 