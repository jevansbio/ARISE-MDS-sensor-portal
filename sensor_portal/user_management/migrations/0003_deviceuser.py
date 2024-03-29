# Generated by Django 4.0 on 2024-03-15 09:10

import django.contrib.auth.models
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('user_management', '0002_groupprofile_deployment_groupprofile_device'),
    ]

    operations = [
        migrations.CreateModel(
            name='DeviceUser',
            fields=[
                ('user_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='user_management.user')),
            ],
            options={
                'verbose_name': 'DeviceUser',
                'verbose_name_plural': 'DeviceUsers',
            },
            bases=('user_management.user',),
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
    ]
