# Generated by Django 4.0.6 on 2023-08-17 10:55

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0038_alter_contest_end_date_alter_contest_start_date'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='monument',
            options={'ordering': ['label']},
        ),
    ]