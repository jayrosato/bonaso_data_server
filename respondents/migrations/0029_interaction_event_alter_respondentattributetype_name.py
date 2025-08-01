# Generated by Django 5.2.2 on 2025-07-26 06:52

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0009_rename_event_date_event_start_event_end_and_more'),
        ('respondents', '0028_alter_respondent_id_no'),
    ]

    operations = [
        migrations.AddField(
            model_name='interaction',
            name='event',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='events.event'),
        ),
        migrations.AlterField(
            model_name='respondentattributetype',
            name='name',
            field=models.CharField(choices=[('PLWHIV', 'Person Living with HIV'), ('PWD', 'Person Living with a Disability'), ('KP', 'Key Population'), ('community_leader', 'Community Leader'), ('CHW', 'Community Health Worker'), ('staff', 'Organization Staff')], max_length=25, unique=True),
        ),
    ]
