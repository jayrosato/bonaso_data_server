# Generated by Django 5.2.2 on 2025-06-09 13:52

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Organization',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='Organization Name')),
                ('office_address', models.CharField(blank=True, max_length=255, null=True, verbose_name='Office Address')),
                ('office_email', models.EmailField(blank=True, max_length=254, null=True, verbose_name='Office Email Address')),
                ('office_phone', models.CharField(blank=True, max_length=255, null=True, verbose_name='Office Phone Number')),
                ('executive_director', models.CharField(blank=True, max_length=255, null=True, verbose_name='Name of Executive Director')),
                ('ed_email', models.EmailField(blank=True, max_length=254, null=True, verbose_name='Exeuctive Director Email Address')),
                ('ed_phone', models.CharField(blank=True, max_length=255, null=True, verbose_name='Exeuctive Director Phone Number')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('parent_organization', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='organizations.organization', verbose_name='Parent Organization')),
            ],
        ),
    ]
