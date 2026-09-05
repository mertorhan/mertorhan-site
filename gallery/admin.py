from django.contrib import admin
from .models import Photo


@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    list_display = ("title", "order", "category", "location", "is_published", "created_at")
    list_filter = ("category", "is_published")
    search_fields = ("title", "location", "camera")
    # Sira liste ekranindan toplu duzenlenebilsin: tek tek kayit acmadan
    # butun galerinin sirasi ayarlanabiliyor.
    list_editable = ("order", "is_published")
    ordering = ("order", "-created_at")