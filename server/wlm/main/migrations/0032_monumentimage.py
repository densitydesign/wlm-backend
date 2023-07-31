# Generated by Django 4.0.6 on 2023-07-28 14:51

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0031_appcategory_order_appcategory_priority'),
    ]

    operations = [
        migrations.CreateModel(
            name='MonumentImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image_id', models.CharField(max_length=200, unique=True)),
                ('image_url', models.ImageField(upload_to='images')),
                ('image_date', models.DateTimeField(blank=True, db_index=True, null=True)),
                ('image_title', models.TextField(blank=True, default='')),
                ('image_type', models.CharField(db_index=True, max_length=20)),
                ('data', models.JSONField(default=dict)),
                ('monument', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='images', to='main.monument')),
            ],
            options={
                'index_together': {('monument', 'image_date')},
            },
        ),
    ]
