# Generated by Django 4.2 on 2025-02-25 09:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('observation_editor', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='taxon',
            name='linked_taxons',
        ),
        migrations.AddField(
            model_name='taxon',
            name='parents',
            field=models.ManyToManyField(related_name='children', to='observation_editor.taxon'),
        ),
    ]
