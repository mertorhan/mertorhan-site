from django.contrib import admin
from .models import Category, BlogPost


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "is_published", "is_featured", "published_at")
    list_filter = ("category", "is_published", "is_featured")
    search_fields = ("title", "summary", "body")
    list_editable = ("is_published", "is_featured")
    prepopulated_fields = {"slug": ("title",)}