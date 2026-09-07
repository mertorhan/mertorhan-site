from django.contrib import admin

from core.rating_admin import BaseScoreInline, ScoreAverageMixin
from .models import Author, Book, BookQuote, BookScore, Genre, Publisher, Translator


# Kunye listeleri: dordu de tek alanli, tek isleri isim tutmak.
# Ayri ayri kayitli olmalari sart — filter_horizontal'in yanindaki "+"
# dugmesi ancak admin'e kayitli modeller icin cikiyor.
# Liste + arama: ayni ismin iki farkli yazimini gorup duzeltebilmek icin.
@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Translator)
class TranslatorAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Publisher)
class PublisherAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


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
    list_display = ("title", "author", "release_year", "rating", "is_published", "is_featured", "is_hero", "published_at")
    list_filter = ("is_published", "is_featured", "is_hero", "genres", "publisher")
    # Arama hem ESKI metin alanina (author) hem YENI iliskiye
    # (authors__name) bakiyor. movies'te arama tamamen iliskiye
    # tasinmisti; burada bilerek ikisi birlikte duruyor: veri elle
    # girilene kadar tek basina authors__name arama sonuclarini
    # bosaltirdi. Eski alan silindiginde author da buradan cikacak.
    # Iliski uzerinden arama JOIN yapar; ayni kitap birden fazla eslesen
    # satir uretebilir. Django changelist bunu kendisi distinct'liyor
    # (get_search_results may_have_duplicates=True dondurur).
    #
    # translators__name BILEREK yok: arama zaten dort alana bakiyor ve
    # cevirmen adiyla kitap aramak gercekci bir ihtiyac degil. Her yeni
    # iliski bir JOIN daha demek.
    search_fields = ("title", "author", "authors__name", "summary")
    list_editable = ("is_published", "is_featured", "is_hero")
    prepopulated_fields = {"slug": ("title",)}
    # Cift panelli secim araci: soldaki listeden secip saga atiyorsun.
    # Yanindaki "+" ile sayfadan cikmadan yeni isim eklenebiliyor.
    filter_horizontal = ("authors", "translators", "genres")
    # Puanlar alintilarin ustunde: once degerlendirme, sonra alinti.
    inlines = [BookScoreInline, BookQuoteInline]
    # rating artik alt kriterlerden hesaplaniyor, elle girilmiyor.
    readonly_fields = ("rating",)