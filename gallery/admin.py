from django.contrib import admin
from .models import Photo


@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "location", "is_published", "created_at")
    list_filter = ("category", "is_published")
    search_fields = ("title", "location", "camera")
    list_editable = ("is_published",)