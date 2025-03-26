# Generated manually to fix schema issues
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('data_models', '0026_auto_20250325_0945'),
    ]

    operations = [
        # Device fields
        migrations.AddField(
            model_name='device',
            name='start_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='device',
            name='end_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='device',
            name='battery_level',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='device',
            name='autoupdate',
            field=models.BooleanField(blank=True, default=False, null=True),
        ),
        migrations.AddField(
            model_name='device',
            name='update_time',
            field=models.IntegerField(blank=True, default=48, null=True),
        ),
        migrations.AddField(
            model_name='device',
            name='coordinate_uncertainty',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='device',
            name='gps_device',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='device',
            name='mic_height',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='device',
            name='mic_direction',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='device',
            name='habitat',
            field=models.CharField(blank=True, max_length=100, null=True),
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
            name='comment',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='device',
            name='user_email',
            field=models.EmailField(blank=True, max_length=254, null=True),
        ),
        migrations.AddField(
            model_name='device',
            name='username',
            field=models.CharField(blank=True, default=None, max_length=100, null=True, unique=True),
        ),
        migrations.AddField(
            model_name='device',
            name='extra_data',
            field=models.JSONField(blank=True, default=dict, null=True),
        ),
        
        # Deployment fields
        migrations.AddField(
            model_name='deployment',
            name='battery_level',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='deployment',
            name='autoupdate',
            field=models.BooleanField(blank=True, default=False, null=True),
        ),
        migrations.AddField(
            model_name='deployment',
            name='update_time',
            field=models.IntegerField(blank=True, default=48, null=True),
        ),
        migrations.AddField(
            model_name='deployment',
            name='coordinate_uncertainty',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='deployment',
            name='gps_device',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='deployment',
            name='mic_height',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='deployment',
            name='mic_direction',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='deployment',
            name='habitat',
            field=models.CharField(blank=True, max_length=100, null=True),
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
            name='comment',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='deployment',
            name='user_email',
            field=models.EmailField(blank=True, max_length=254, null=True),
        ),
        migrations.AddField(
            model_name='deployment',
            name='country',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='deployment',
            name='site_name',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='deployment',
            name='username',
            field=models.CharField(blank=True, default=None, max_length=100, null=True, unique=True),
        ),
        migrations.AddField(
            model_name='deployment',
            name='extra_data',
            field=models.JSONField(blank=True, default=dict, null=True),
        ),
    ]
