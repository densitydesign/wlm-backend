from django.contrib import admin
from main.models import (Region, Province, Municipality, Monument, MonumentAuthorization, Picture, Snapshot)

admin.site.register(Region)
admin.site.register(Province)
admin.site.register(Municipality)
admin.site.register(Monument)
admin.site.register(MonumentAuthorization)
admin.site.register(Picture)
admin.site.register(Snapshot)
