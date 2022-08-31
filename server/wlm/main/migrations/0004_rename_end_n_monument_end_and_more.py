# Generated by Django 4.0.6 on 2022-08-01 22:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0003_picture_image_title_alter_categorysnapshot_payload'),
    ]

    operations = [
        migrations.RenameField(
            model_name='monument',
            old_name='end_n',
            new_name='end',
        ),
        migrations.RenameField(
            model_name='monument',
            old_name='start_n',
            new_name='start',
        ),
        migrations.AddField(
            model_name='monument',
            name='parent_q_number',
            field=models.CharField(blank=True, default='', max_length=200),
        ),
    ]