from django.contrib import admin
from .models import AccessKey

# Register your models here.
@admin.register(AccessKey)
class AccessKeyAdmin(admin.ModelAdmin):
    list_display = ("key", "usage_count", "usage_limit", "device_id", "expires_at", "created_at")
    readonly_fields = ("created_at",)
    search_fields = ("key", "device_id")
