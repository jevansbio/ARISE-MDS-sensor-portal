# Generated by Django 4.0 on 2024-03-15 09:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data_models', '0004_rename_do_not_delete_datafile_do_not_remove_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='device',
            name='authentication',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]