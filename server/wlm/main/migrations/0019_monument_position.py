# Generated by Django 4.0.6 on 2022-07-31 12:51

import django.contrib.gis.db.models.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0018_municipality_province_municipality_region_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='monument',
            name='position',
            field=django.contrib.gis.db.models.fields.PointField(blank=True, null=True, srid=4326),
        ),
    ]