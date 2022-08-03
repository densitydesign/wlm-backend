# Generated by Django 4.0.6 on 2022-08-03 16:02

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0005_monument_relevant_images'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='municipality',
            options={'ordering': ['name']},
        ),
        migrations.AlterModelOptions(
            name='province',
            options={'ordering': ['name']},
        ),
        migrations.AlterModelOptions(
            name='region',
            options={'ordering': ['name']},
        ),
        migrations.AlterField(
            model_name='monument',
            name='label',
            field=models.TextField(),
        ),
        migrations.AlterField(
            model_name='municipality',
            name='province',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='municipalities', to='main.province'),
        ),
        migrations.AlterField(
            model_name='municipality',
            name='region',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='municipalities', to='main.region'),
        ),
        migrations.AlterField(
            model_name='province',
            name='region',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='provinces', to='main.region'),
        ),
        migrations.DeleteModel(
            name='MonumentAuthorization',
        ),
    ]
