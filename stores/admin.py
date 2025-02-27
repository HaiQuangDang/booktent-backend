from django.contrib import admin
from .models import Store

@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "status", "created_at", "updated_at")
    list_filter = ("status",)
    search_fields = ("name", "owner__username")
