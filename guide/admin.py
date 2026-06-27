from django.contrib import admin
from .models import Guide, GuideStop


# Durakları, gezinin kendi sayfasında alt alta düzenlemek için "inline"
class GuideStopInline(admin.TabularInline):
    model = GuideStop
    extra = 1  # Boş 1 satır gösterir (yeni durak eklemek kolay olsun)
    fields = ("order", "name", "point_type", "description", "hours", "cost")
    ordering = ("order",)


@admin.register(Guide)
class GuideAdmin(admin.ModelAdmin):
    list_display = ("title", "entry_type", "city", "is_published", "is_featured", "published_at")
    list_filter = ("entry_type", "city", "is_published", "is_featured")
    search_fields = ("title", "summary", "overview")
    list_editable = ("is_published", "is_featured")
    prepopulated_fields = {"slug": ("title",)}
    inlines = [GuideStopInline]  # Durak tablosunu Guide sayfasına gömer


@admin.register(GuideStop)
class GuideStopAdmin(admin.ModelAdmin):
    list_display = ("order", "name", "guide", "point_type")
    list_filter = ("point_type", "guide")
    search_fields = ("name", "description")