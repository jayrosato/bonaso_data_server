# Generated by Django 5.2.2 on 2025-07-20 09:48

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('messaging', '0004_messagerecipient_completed_on'),
        ('organizations', '0004_organization_full_name'),
        ('projects', '0014_client_full_name_client_updated_by_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='announcement',
            name='organization',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='organizations.organization'),
        ),
        migrations.AlterField(
            model_name='announcement',
            name='project',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='projects.project'),
        ),
    ]
