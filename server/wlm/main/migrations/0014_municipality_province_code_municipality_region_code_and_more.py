# Generated by Django 4.0.6 on 2022-07-31 12:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0013_remove_region_data_municipality_code_province_code_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='municipality',
            name='province_code',
            field=models.CharField(default=1, max_length=200),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='municipality',
            name='region_code',
            field=models.CharField(default=1, max_length=200),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='province',
            name='region_code',
            field=models.CharField(default=1, max_length=200),
            preserve_default=False,
        ),
    ]