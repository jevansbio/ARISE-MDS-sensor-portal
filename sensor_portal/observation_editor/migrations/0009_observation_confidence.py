# Generated by Django 4.2 on 2025-03-17 12:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('observation_editor', '0008_alter_observation_source'),
    ]

    operations = [
        migrations.AddField(
            model_name='observation',
            name='confidence',
            field=models.FloatField(default=None, null=True),
        ),
    ]
