# Generated by Django 5.2.2 on 2025-07-13 10:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('indicators', '0016_alter_indicator_allow_repeat'),
    ]

    operations = [
        migrations.AddField(
            model_name='indicatorsubcategory',
            name='deprecated',
            field=models.BooleanField(blank=True, default=False, null=True),
        ),
    ]
