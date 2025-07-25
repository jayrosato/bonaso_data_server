# Generated by Django 5.2.2 on 2025-07-01 05:53

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0013_project_updated_by_projectindicator_added_by_and_more'),
        ('users', '0003_alter_user_role'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='client_organization',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='projects.client'),
        ),
        migrations.AlterField(
            model_name='user',
            name='role',
            field=models.CharField(choices=[('view_only', 'View Only'), ('data_collector', 'Data Collector'), ('supervisor', 'Supervisor'), ('meofficer', 'Monitoring and Evaluation Officer'), ('manager', 'Manager'), ('admin', 'Site Administrator'), ('client', 'Client')], default='view_only', help_text='Set user access level and permission. Leave as "Data Collector" if unsure.', max_length=25),
        ),
    ]
