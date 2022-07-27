from django.db import models


class Region(models.Model):
    name = models.CharField(max_length=200)
    data = models.JSONField(default=dict)


class Province(models.Model):
    name = models.CharField(max_length=200)
    data = models.JSONField(default=dict)


class Municipality(models.Model):
    name = models.CharField(max_length=200)
    data = models.JSONField(default=dict)


class Monument(models.Model):
    name = models.CharField(max_length=200)
    data = models.JSONField(default=dict)


class MonumentAuthorization(models.Model):
    monument = models.ForeignKey(Monument, models.CASCADE)
    authorized = models.BooleanField()
    event_date = models.DateField()
    data = models.JSONField(default=dict)


class Picture(models.Model):
    monument = models.ForeignKey(Monument, models.CASCADE)
    type = models.CharField(max_length=20)
    image = models.URLField()
    data = models.JSONField(default=dict)
    event_date = models.DateField()


class Snapshot(models.Model):
    data = models.JSONField(default=dict)
    timestamp = models.DateTimeField(auto_now_add=True)

