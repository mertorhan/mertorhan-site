from django.contrib import admin
from .models import Category, BlogPost, PostSection


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


# Bloklari yazinin kendi sayfasinda duzenlemek icin "inline".
# Stacked (Tabular degil): 11 alan var ve text cok satirli bir metin kutusu —
# tabular duzende hepsi tek satira sikisir, paragraf yazilamaz hale gelir.
class PostSectionInline(admin.StackedInline):
    model = PostSection
    extra = 1  # Acilista 1 bos blok (Django varsayilani 3, gurultulu)
    fieldsets = (
        (None, {"fields": ("kind", "order")}),
        ("Metin (paragraf · başlık · alıntı)", {"fields": ("text",)}),
        # Tur-ozel gruplar katli baslar: her blokta 11 alanin acik durmasi formu
        # okunmaz hale getiriyor. Basliga tiklayinca acilir. "collapse" Django
        # admin'in kendi hazir sinifi — ek JavaScript yok.
        (
            "Sadece başlık bloğu için",
            {"classes": ("collapse",), "fields": ("heading_level", "in_toc")},
        ),
        (
            "Sadece görsel bloğu için",
            {"classes": ("collapse",), "fields": ("image", "image_title", "image_caption", "image_alt")},
        ),
        (
            "Sadece alıntı bloğu için",
            {"classes": ("collapse",), "fields": ("quote_source",)},
        ),
        (
            "Sadece gömü bloğu için",
            {"classes": ("collapse",), "fields": ("embed_url",)},
        ),
    )


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "is_published", "is_featured", "is_hero", "published_at")
    list_filter = ("category", "is_published", "is_featured", "is_hero")
    search_fields = ("title", "summary", "body")
    list_editable = ("is_published", "is_featured", "is_hero")
    prepopulated_fields = {"slug": ("title",)}
    inlines = [PostSectionInline]  # Bloklari BlogPost sayfasina gomer