# Generated by Django 4.0.6 on 2022-07-31 09:47

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0007_alter_categorysnapshot_updated'),
    ]

    operations = [
        migrations.AddField(
            model_name='monument',
            name='municipality',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='main.municipality'),
        ),
    ]