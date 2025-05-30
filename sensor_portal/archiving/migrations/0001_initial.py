# Generated by Django 4.2 on 2025-02-10 13:15

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import encrypted_model_fields.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Archive',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('modified_on', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=200)),
                ('username', models.CharField(max_length=50, unique=True)),
                ('password', encrypted_model_fields.fields.EncryptedCharField()),
                ('address', models.CharField(max_length=100, unique=True)),
                ('root_folder', models.CharField(max_length=100, unique=True)),
                ('owner', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='owned_archives', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='TarFile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('modified_on', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=200)),
                ('archived_dt', models.DateTimeField()),
                ('uploading', models.BooleanField(default=False)),
                ('local_storage', models.BooleanField(default=True)),
                ('archived', models.BooleanField(default=False)),
                ('path', models.CharField(max_length=500)),
                ('comboproject', models.CharField(blank=True, editable=False, max_length=100, null=True)),
                ('archive', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='tar_files', to='archiving.archive')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
