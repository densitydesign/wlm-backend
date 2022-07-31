from django.contrib.gis.db import models


class Category(models.Model):
    label = models.CharField(max_length=200)
    q_number = models.CharField(max_length=200)

    def __str__(self):
        return self.label

class Region(models.Model):
    name = models.CharField(max_length=200)
    code = models.IntegerField(primary_key=True)
    poly = models.MultiPolygonField(blank=True, null=True)

    def __str__(self):
        return self.name


class Province(models.Model):
    name = models.CharField(max_length=200)
    code = models.IntegerField(primary_key=True)
    region_code = models.IntegerField()
    poly = models.MultiPolygonField(blank=True, null=True)

    region = models.ForeignKey(Region, models.SET_NULL, blank=True,  null=True)

    def __str__(self):
        return self.name


class Municipality(models.Model):
    name = models.CharField(max_length=200)
    code = models.IntegerField(primary_key=True)
    province_code = models.IntegerField()
    region_code = models.IntegerField()
    poly = models.MultiPolygonField(blank=True, null=True)

    province = models.ForeignKey(Province, models.SET_NULL, blank=True,  null=True)
    region = models.ForeignKey(Region, models.SET_NULL, blank=True,  null=True)

    def __str__(self):
        return self.name


class Monument(models.Model):
    label = models.CharField(max_length=200)
    q_number = models.CharField(max_length=200, unique=True)
    wlm_n = models.CharField(max_length=200, blank='', default='')
    start_n = models.DateTimeField(blank=True, null=True)
    end_n = models.DateTimeField(blank=True, null=True)
    data = models.JSONField(default=dict)

    position = models.PointField(blank=True, null=True)

    first_revision = models.DateTimeField(blank=True, null=True)

    municipality = models.ForeignKey(Municipality, models.SET_NULL, null=True, blank=True, related_name='monuments')
    province = models.ForeignKey(Province, models.SET_NULL, blank=True,  null=True, related_name='monuments')
    region = models.ForeignKey(Region, models.SET_NULL, blank=True,  null=True, related_name='monuments')

    categories = models.ManyToManyField(Category, blank=True)

    #TODO ADD REFS TO PROVINCE AND REGION TO SPEEDUP QUERIES

    def __str__(self):
        return self.label

#TODO :PROBABLY NOT NEEDED (use start_n, end_n)
class MonumentAuthorization(models.Model):
    monument = models.ForeignKey(Monument, models.CASCADE)
    authorized = models.BooleanField()
    event_date = models.DateField()
    data = models.JSONField(default=dict)


class Picture(models.Model):
    monument = models.ForeignKey(Monument, models.CASCADE)
    image_id = models.CharField(max_length=200, unique=True)
    image_url = models.URLField(max_length=2000)
    image_date = models.DateTimeField(blank=True, null=True)
    image_type = models.CharField(max_length=20)
    data = models.JSONField(default=dict)


class CategorySnapshot(models.Model):
    label = models.CharField(max_length=200)
    q_number = models.CharField(max_length=200, unique=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.label