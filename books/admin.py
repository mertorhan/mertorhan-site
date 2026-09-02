from django.contrib import admin

from core.rating_admin import BaseScoreInline, ScoreAverageMixin
from .models import Book, BookQuote, BookScore


# Alıntılar, kitabın kendi sayfasında alt alta düzenlensin (GuideStop'taki inline kalıbı)
class BookQuoteInline(admin.TabularInline):
    model = BookQuote
    extra = 1
    fields = ("order", "text", "page")
    ordering = ("order",)


class BookScoreInline(BaseScoreInline):
    model = BookScore
    criterion_flag = "for_books"
    score_lookup = "bookscore__book"


@admin.register(Book)
class BookAdmin(ScoreAverageMixin, admin.ModelAdmin):
    list_display = ("title", "author", "rating", "is_published", "is_featured", "is_hero", "published_at")
    list_filter = ("is_published", "is_featured", "is_hero")
    search_fields = ("title", "author", "summary")
    list_editable = ("is_published", "is_featured", "is_hero")
    prepopulated_fields = {"slug": ("title",)}
    # Puanlar alintilarin ustunde: once degerlendirme, sonra alinti.
    inlines = [BookScoreInline, BookQuoteInline]
    # rating artik alt kriterlerden hesaplaniyor, elle girilmiyor.
    readonly_fields = ("rating",)