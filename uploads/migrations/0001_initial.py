# Generated by Django 5.2.2 on 2025-06-20 19:32

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('organizations', '0004_organization_full_name'),
        ('projects', '0013_project_updated_by_projectindicator_added_by_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='NarrativeReport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('file', models.FileField(upload_to='narrative_reports/')),
                ('title', models.CharField(max_length=255, verbose_name='Upload Title')),
                ('description', models.TextField(blank=True, verbose_name='Description of Upload')),
                ('organization', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='organizations.organization')),
                ('project', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='projects.project')),
                ('uploaded_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='file_uploaded_by', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
