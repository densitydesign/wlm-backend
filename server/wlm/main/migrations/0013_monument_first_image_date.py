# Generated by Django 4.0.6 on 2022-08-31 14:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0012_alter_monument_index_together'),
    ]

    operations = [
        migrations.AddField(
            model_name='monument',
            name='first_image_date',
            field=models.DateField(blank=True, null=True),
        ),
    ]
