# Generated by Django 4.0.6 on 2022-09-16 15:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0016_monument_first_image_date_commons'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='group',
            field=models.CharField(blank=True, default='', max_length=200),
        ),
    ]
