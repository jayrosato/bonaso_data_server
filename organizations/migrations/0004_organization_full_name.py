# Generated by Django 5.2.2 on 2025-06-20 19:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('organizations', '0003_organization_updated_by_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='organization',
            name='full_name',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Full/Extended Organization Name'),
        ),
    ]
