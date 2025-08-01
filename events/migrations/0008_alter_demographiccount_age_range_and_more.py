# Generated by Django 5.2.2 on 2025-07-25 11:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0007_alter_demographiccount_hiv_status_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='demographiccount',
            name='age_range',
            field=models.CharField(blank=True, choices=[('under_1', 'Less Than One Year Old'), ('1_4', '1-4'), ('5_9', '5-9'), ('10_14', '10-14'), ('15_19', '15-19'), ('20_24', '20–24'), ('25_29', '25–29'), ('30_34', '30–34'), ('35_39', '35–39'), ('40_44', '40-44'), ('45_49', '45–49'), ('50_54', '50-54'), ('55_55', '55-59'), ('60_64', '60-64'), ('65_plus', '65+')], max_length=25, null=True),
        ),
        migrations.AlterField(
            model_name='event',
            name='event_type',
            field=models.CharField(choices=[('Training', 'Training'), ('Activity', 'Activity'), ('Engagement', 'Engagement'), ('Commemoration', 'Commemoration'), ('Activation', 'Activation'), ('Walkathon', 'Walkathon'), ('Counselling_Session', 'Counselling Session'), ('Other', 'Other')], default='Training', max_length=25, verbose_name='Event Type'),
        ),
    ]
