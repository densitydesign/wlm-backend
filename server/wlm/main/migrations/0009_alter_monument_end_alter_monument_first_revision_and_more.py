# Generated by Django 4.0.6 on 2022-08-31 13:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0008_alter_picture_monument_alter_monument_index_together'),
    ]

    operations = [
        migrations.AlterField(
            model_name='monument',
            name='end',
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
        migrations.AlterField(
            model_name='monument',
            name='first_revision',
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
        migrations.AlterField(
            model_name='monument',
            name='start',
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
    ]
