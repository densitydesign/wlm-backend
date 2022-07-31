# Generated by Django 4.0.6 on 2022-07-31 09:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0002_alter_monument_code'),
    ]

    operations = [
        migrations.AddField(
            model_name='monument',
            name='end_n',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='monument',
            name='start_n',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='monument',
            name='wlm_n',
            field=models.CharField(blank='', default='', max_length=200),
        ),
    ]
