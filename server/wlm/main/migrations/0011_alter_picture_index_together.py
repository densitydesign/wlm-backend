# Generated by Django 4.0.6 on 2022-08-31 13:40

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0010_alter_monument_index_together_and_more'),
    ]

    operations = [
        migrations.AlterIndexTogether(
            name='picture',
            index_together={('monument', 'image_date')},
        ),
    ]
