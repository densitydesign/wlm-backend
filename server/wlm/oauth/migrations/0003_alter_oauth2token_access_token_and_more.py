# Generated by Django 4.0.6 on 2023-07-02 22:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('oauth', '0002_alter_oauth2token_access_token_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='oauth2token',
            name='access_token',
            field=models.TextField(max_length=500),
        ),
        migrations.AlterField(
            model_name='oauth2token',
            name='refresh_token',
            field=models.TextField(max_length=500),
        ),
    ]