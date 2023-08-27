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
    CategorySnapshotError,
)

admin.site.register(Region)
admin.site.register(Province)
admin.site.register(Municipality)

class CategoryAdmin(admin.ModelAdmin):
    list_display = ["label", "q_number", "group", "app_category"]
    list_filter = ["app_category"]
    search_fields = ["label", "q_number"]

admin.site.register(Category, CategoryAdmin)


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
admin.site.register(CategorySnapshotError)