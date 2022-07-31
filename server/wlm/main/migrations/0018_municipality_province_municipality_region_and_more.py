# Generated by Django 4.0.6 on 2022-07-31 12:45

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0017_alter_municipality_code_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='municipality',
            name='province',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='main.province'),
        ),
        migrations.AddField(
            model_name='municipality',
            name='region',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='main.region'),
        ),
        migrations.AddField(
            model_name='province',
            name='region',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='main.region'),
        ),
    ]
