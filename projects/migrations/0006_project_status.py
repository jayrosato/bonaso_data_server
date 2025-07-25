# Generated by Django 5.2.2 on 2025-06-11 09:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0005_alter_project_description_alter_project_organization_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='status',
            field=models.CharField(choices=[('Planned', 'Planned'), ('Active', 'Active'), ('Completed', 'Completed'), ('On_hold', 'On Hold')], default='Planned', max_length=25, verbose_name='Project Status'),
        ),
    ]
