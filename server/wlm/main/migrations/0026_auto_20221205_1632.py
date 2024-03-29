# Generated by Django 4.0.6 on 2022-12-05 15:32
from django.db import migrations
from main.helpers import monument_prop


def update_approved_by(apps, schema_editor):
    Monument = apps.get_model("main", "Monument")
    for monument in Monument.objects.all():
        approved_by = monument_prop(monument.data, "approvedBy_n", "")
        if approved_by:
            print(f"Updating {monument.q_number} with approved_by: {approved_by}")
            monument.approved_by = approved_by
            monument.save()
        else:
            print(f"Skipping {monument.q_number} because it has no approved_by in actual data")


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0025_monument_approved_by"),
    ]

    operations = [
        migrations.RunPython(update_approved_by),
    ]
