from django.contrib.gis import admin
from main.models import (
    Region,
    Province,
    Municipality,
    Monument,
    Picture,
    CategorySnapshot,
    Category,
    Snapshot,
    AppCategory,
    Contest,
)

admin.site.register(Region)
admin.site.register(Province)
admin.site.register(Municipality)
admin.site.register(Category)


class PictureAdmin(admin.ModelAdmin):
    raw_id_fields = ("monument",)


admin.site.register(Picture, PictureAdmin)


class SnapshotAdmin(admin.ModelAdmin):
    readonly_fields = ["updated"]
    list_display = ["__str__", "updated"]


admin.site.register(Snapshot, SnapshotAdmin)


class CategorySnapshotAdmin(admin.ModelAdmin):
    readonly_fields = ["has_payload", "updated"]
    list_display = ["__str__", "updated", "complete"]

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.select_related("category").defer("payload", "query")
        return queryset


admin.site.register(CategorySnapshot, CategorySnapshotAdmin)


class PictureInline(admin.TabularInline):
    model = Picture
    extra = 1


class MonumentAdmin(admin.ModelAdmin):
    search_fields = ["label"]
    list_filter = ["region", "province", "categories", "start"]
    # inlines = [PictureInline]


admin.site.register(Monument, MonumentAdmin)
admin.site.register(AppCategory)
admin.site.register(Contest)
