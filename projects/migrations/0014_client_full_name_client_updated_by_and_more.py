# Generated by Django 5.2.2 on 2025-07-07 06:52

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0013_project_updated_by_projectindicator_added_by_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='client',
            name='full_name',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Client Organization Full Name'),
        ),
        migrations.AddField(
            model_name='client',
            name='updated_by',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='client_updated_by', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='client',
            name='created_by',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='client_created_by', to=settings.AUTH_USER_MODEL),
        ),
    ]
