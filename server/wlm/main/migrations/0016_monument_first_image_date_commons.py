# Generated by Django 4.0.6 on 2022-09-16 11:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0015_alter_monument_index_together'),
    ]

    operations = [
        migrations.AddField(
            model_name='monument',
            name='first_image_date_commons',
            field=models.DateField(blank=True, null=True),
        ),
    ]