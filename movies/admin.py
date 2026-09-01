from django.contrib import admin
from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("title", "content_type", "release_year", "rating", "is_published", "is_featured", "is_hero", "published_at")
    list_filter = ("content_type", "is_published", "is_featured", "is_hero", "genre")
    search_fields = ("title", "director", "lead_actors", "summary")
    list_editable = ("is_published", "is_featured", "is_hero")
    prepopulated_fields = {"slug": ("title",)}