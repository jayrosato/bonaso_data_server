# Generated by Django 5.2.2 on 2025-07-07 11:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('respondents', '0015_interaction_flagged'),
    ]

    operations = [
        migrations.AddField(
            model_name='interactionsubcategory',
            name='numeric_component',
            field=models.IntegerField(blank=True, default=None, null=True),
        ),
    ]
