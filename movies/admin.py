from django.contrib import admin

from core.rating_admin import BaseScoreInline, ScoreAverageMixin
from .models import Review, ReviewScore


class ReviewScoreInline(BaseScoreInline):
    model = ReviewScore
    criterion_flag = "for_movies"
    score_lookup = "reviewscore__review"


@admin.register(Review)
class ReviewAdmin(ScoreAverageMixin, admin.ModelAdmin):
    list_display = ("title", "content_type", "release_year", "rating", "is_published", "is_featured", "is_hero", "published_at")
    list_filter = ("content_type", "is_published", "is_featured", "is_hero", "genre")
    search_fields = ("title", "director", "lead_actors", "summary")
    list_editable = ("is_published", "is_featured", "is_hero")
    prepopulated_fields = {"slug": ("title",)}
    inlines = [ReviewScoreInline]
    # rating artik alt kriterlerden hesaplaniyor, elle girilmiyor.
    readonly_fields = ("rating",)
