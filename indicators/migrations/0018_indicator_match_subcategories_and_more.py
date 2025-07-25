# Generated by Django 5.2.2 on 2025-07-14 09:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('indicators', '0017_indicatorsubcategory_deprecated'),
    ]

    operations = [
        migrations.AddField(
            model_name='indicator',
            name='match_subcategories',
            field=models.BooleanField(blank=True, default=False, null=True),
        ),
        migrations.AlterField(
            model_name='indicator',
            name='indicator_type',
            field=models.CharField(choices=[('Respondent', 'Respondent'), ('Event_No', 'Number of Events'), ('Org_Event_No', 'Number of Organizations at Event'), ('Count', 'Count')], default='Respondent', max_length=25, verbose_name='Indicator Type'),
        ),
    ]
