from django.contrib import admin

from core.rating_admin import BaseScoreInline, ScoreAverageMixin
from .models import Actor, Director, Genre, Review, ReviewScore, Screenwriter


# Kunye listeleri: dordu de tek alanli, tek isleri isim tutmak.
# Ayri ayri kayitli olmalari sart — filter_horizontal'in yanindaki "+"
# dugmesi ancak admin'e kayitli modeller icin cikiyor.
# Liste + arama: ayni ismin iki farkli yazimini gorup duzeltebilmek icin.
@admin.register(Director)
class DirectorAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Screenwriter)
class ScreenwriterAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Actor)
class ActorAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


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
    # Cift panelli secim araci: soldaki listeden secip saga atiyorsun.
    # Yanindaki "+" ile sayfadan cikmadan yeni isim eklenebiliyor.
    filter_horizontal = ("directors", "screenwriters", "actors", "genres")
    inlines = [ReviewScoreInline]
    # rating artik alt kriterlerden hesaplaniyor, elle girilmiyor.
    readonly_fields = ("rating",)
