# Generated by Django 4.0.6 on 2022-08-31 13:19

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0007_municipality_centroid_province_centroid_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='picture',
            name='monument',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pictures', to='main.monument'),
        ),
        migrations.AlterIndexTogether(
            name='monument',
            index_together={('start', 'first_revision')},
        ),
    ]
