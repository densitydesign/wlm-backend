from django.contrib.gis.db import models


class Snapshot(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    complete = models.BooleanField(default=False)

    csv_export = models.FileField(upload_to="csv_exports", null=True, blank=True)
    xlsx_export = models.FileField(upload_to="xlsx_exports", null=True, blank=True)
    
    def __str__(self):
        return f"{self.created}"


class Category(models.Model):
    label = models.CharField(max_length=200)
    q_number = models.CharField(max_length=200)
    group = models.CharField(max_length=200, blank=True, default="")

    def __str__(self):
        return self.label


class CategorySnapshot(models.Model):
    snapshot = models.ForeignKey(Snapshot, models.CASCADE, related_name="category_snapshots")
    category = models.ForeignKey(Category, models.CASCADE)
    query = models.TextField()
    payload = models.JSONField(null=True, default=None, editable=False)
    complete = models.BooleanField(default=False)
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

    def has_payload(self):
        return bool(self.payload)

    def __str__(self):
        return self.category.label

class Region(models.Model):
    name = models.CharField(max_length=200)
    code = models.IntegerField(primary_key=True)
    poly = models.MultiPolygonField(blank=True, null=True)
    centroid = models.PointField(blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class Province(models.Model):
    name = models.CharField(max_length=200)
    code = models.IntegerField(primary_key=True)
    region_code = models.IntegerField()
    poly = models.MultiPolygonField(blank=True, null=True)
    centroid = models.PointField(blank=True, null=True)

    region = models.ForeignKey(Region, models.SET_NULL, blank=True,  null=True, related_name="provinces")

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class Municipality(models.Model):
    name = models.CharField(max_length=200)
    code = models.IntegerField(primary_key=True)
    province_code = models.IntegerField()
    region_code = models.IntegerField()
    poly = models.MultiPolygonField(blank=True, null=True)
    centroid = models.PointField(blank=True, null=True)

    province = models.ForeignKey(Province, models.SET_NULL, blank=True,  null=True, related_name='municipalities')
    region = models.ForeignKey(Region, models.SET_NULL, blank=True,  null=True, related_name="municipalities")

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class Monument(models.Model):
    label = models.TextField()
    q_number = models.CharField(max_length=200, unique=True)
    parent_q_number = models.CharField(max_length=200, blank=True, default="")
    wlm_n = models.CharField(max_length=200, blank=True, default='')
    start = models.DateTimeField(blank=True, null=True, db_index=True)
    end = models.DateTimeField(blank=True, null=True, db_index=True)
    data = models.JSONField(default=dict)

    position = models.PointField(blank=True, null=True)
    relevant_images = models.JSONField(default=list)

    first_revision = models.DateTimeField(blank=True, null=True, db_index=True)

    municipality = models.ForeignKey(Municipality, models.SET_NULL, null=True, blank=True, related_name='monuments')
    province = models.ForeignKey(Province, models.SET_NULL, blank=True,  null=True, related_name='monuments')
    region = models.ForeignKey(Region, models.SET_NULL, blank=True,  null=True, related_name='monuments',)

    categories = models.ManyToManyField(Category, blank=True)

    snapshot = models.ForeignKey(Snapshot, models.SET_NULL, null=True, blank=True, related_name='monuments')

    first_image_date = models.DateField(blank=True, null=True)
    first_image_date_commons = models.DateField(blank=True, null=True)

    current_wlm_state = models.CharField(blank=True, default='', max_length=20)
    current_commons_state = models.CharField(blank=True, default='', max_length=20)
    
    class Meta:
        index_together = [
            ('start', 'first_revision'),
            ('start', 'first_revision', 'first_image_date'),
        ]    

    def __str__(self):
        return self.label


class Picture(models.Model):
    monument = models.ForeignKey(Monument, models.CASCADE, related_name="pictures")
    image_id = models.CharField(max_length=200, unique=True)
    image_url = models.URLField(max_length=2000)
    image_date = models.DateTimeField(blank=True, null=True, db_index=True)
    image_title = models.TextField(blank=True, default="")
    image_type = models.CharField(max_length=20)
    data = models.JSONField(default=dict)

    class Meta:
        index_together = [
            ('monument', 'image_date'),
        ]    



