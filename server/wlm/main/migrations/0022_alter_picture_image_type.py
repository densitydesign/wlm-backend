# Generated by Django 4.0.6 on 2022-10-18 22:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0021_municipalitylookup'),
    ]

    operations = [
        migrations.AlterField(
            model_name='picture',
            name='image_type',
            field=models.CharField(db_index=True, max_length=20),
        ),
    ]
