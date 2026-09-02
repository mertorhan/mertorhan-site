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
    # Arama ve filtre YENI iliskiler uzerinden. Eski metin alanlarina
    # bakmaya devam etselerdi veri yeni iliskilere girildigi anda arama
    # ve filtre bos donerdi.
    # Iliski uzerinden arama JOIN yapar; ayni film birden fazla eslesen
    # satir uretebilir. Django changelist bunu kendisi distinct'liyor
    # (get_search_results may_have_duplicates=True dondurur) — olculdu.
    list_filter = ("content_type", "is_published", "is_featured", "is_hero", "genres")
    search_fields = ("title", "directors__name", "actors__name", "summary")
    list_editable = ("is_published", "is_featured", "is_hero")
    prepopulated_fields = {"slug": ("title",)}
    # Cift panelli secim araci: soldaki listeden secip saga atiyorsun.
    # Yanindaki "+" ile sayfadan cikmadan yeni isim eklenebiliyor.
    filter_horizontal = ("directors", "screenwriters", "actors", "genres")
    inlines = [ReviewScoreInline]
    # rating artik alt kriterlerden hesaplaniyor, elle girilmiyor.
    readonly_fields = ("rating",)
