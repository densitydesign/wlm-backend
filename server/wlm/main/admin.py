from django.contrib.gis import admin
from main.models import (Region, Province, Municipality, Monument, MonumentAuthorization, Picture,  CategorySnapshot, Category)

admin.site.register(Region)
admin.site.register(Province)
admin.site.register(Municipality)
admin.site.register(Monument)
admin.site.register(MonumentAuthorization)
admin.site.register(Category)


class PictureAdmin(admin.ModelAdmin):
    raw_id_fields = ("monument",)
admin.site.register(Picture, PictureAdmin)

class CategorySnapshotAdmin(admin.ModelAdmin):
    readonly_fields = ['updated']
    list_display = ['label', 'updated']

admin.site.register(CategorySnapshot, CategorySnapshotAdmin)
