# Generated by Django 5.2.2 on 2025-06-11 22:21

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('indicators', '0005_indicator_status'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='indicator',
            name='prerequisite',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='indicators.indicator', verbose_name='Prerequisite Indicator'),
        ),
        migrations.AlterField(
            model_name='indicator',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='indicator',
            name='status',
            field=models.CharField(choices=[('Active', 'Active'), ('Deprecated', 'Deprecated'), ('Planned', 'Planned')], default='Active', max_length=25, verbose_name='Indicator Status'),
        ),
        migrations.CreateModel(
            name='IndicatorSubcategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(help_text='To help if you want to track between options in two indicators', max_length=10, verbose_name='Category Code')),
                ('name', models.CharField(max_length=255, verbose_name='Category Name')),
                ('indicator', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subcategories', to='indicators.indicator')),
            ],
        ),
    ]
