# Generated by Django 4.0.6 on 2022-08-05 15:50

import django.contrib.gis.db.models.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0006_alter_municipality_options_alter_province_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='municipality',
            name='centroid',
            field=django.contrib.gis.db.models.fields.PointField(blank=True, null=True, srid=4326),
        ),
        migrations.AddField(
            model_name='province',
            name='centroid',
            field=django.contrib.gis.db.models.fields.PointField(blank=True, null=True, srid=4326),
        ),
        migrations.AddField(
            model_name='region',
            name='centroid',
            field=django.contrib.gis.db.models.fields.PointField(blank=True, null=True, srid=4326),
        ),
    ]
