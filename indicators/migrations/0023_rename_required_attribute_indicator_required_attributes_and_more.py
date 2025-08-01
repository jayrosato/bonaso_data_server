# Generated by Django 5.2.2 on 2025-07-26 17:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('indicators', '0022_alter_indicator_indicator_type'),
    ]

    operations = [
        migrations.RenameField(
            model_name='indicator',
            old_name='required_attribute',
            new_name='required_attributes',
        ),
        migrations.AlterField(
            model_name='indicator',
            name='status',
            field=models.CharField(choices=[('active', 'Active'), ('deprecated', 'Deprecated'), ('planned', 'Planned')], default='active', max_length=25, verbose_name='Indicator Status'),
        ),
    ]
