# Generated by Django 4.0.6 on 2022-08-31 14:16

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0013_monument_first_image_date'),
    ]

    operations = [
        migrations.AlterIndexTogether(
            name='monument',
            index_together={('id', 'start', 'first_revision'), ('id', 'start', 'first_revision', 'first_image_date')},
        ),
    ]
