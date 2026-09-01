from django.contrib import admin
from .models import Book, BookQuote


# Alıntılar, kitabın kendi sayfasında alt alta düzenlensin (GuideStop'taki inline kalıbı)
class BookQuoteInline(admin.TabularInline):
    model = BookQuote
    extra = 1
    fields = ("order", "text", "page")
    ordering = ("order",)


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "rating", "is_published", "is_featured", "is_hero", "published_at")
    list_filter = ("is_published", "is_featured", "is_hero")
    search_fields = ("title", "author", "summary")
    list_editable = ("is_published", "is_featured", "is_hero")
    prepopulated_fields = {"slug": ("title",)}
    inlines = [BookQuoteInline]