from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('data_models', '0027_add_missing_fields_safe'),
    ]

    operations = [
        migrations.AddField(
            model_name='datafile',
            name='quality_check_dt',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='datafile',
            name='quality_check_status',
            field=models.CharField(
                choices=[
                    ('pending', 'Pending'),
                    ('in_progress', 'In Progress'),
                    ('completed', 'Completed'),
                    ('failed', 'Failed')
                ],
                default='pending',
                max_length=20
            ),
        ),
        migrations.AddField(
            model_name='datafile',
            name='quality_issues',
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name='datafile',
            name='quality_score',
            field=models.FloatField(blank=True, null=True),
        ),
    ] 