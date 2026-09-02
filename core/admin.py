from django.contrib import admin
from .models import Profile, Experience, ContactMessage, RatingCriterion


# Deneyimleri Profil sayfasında alt alta düzenlemek için inline
class ExperienceInline(admin.TabularInline):
    model = Experience
    extra = 1
    fields = ("order", "date_range", "role", "description")
    ordering = ("order",)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("full_name", "role", "email")
    inlines = [ExperienceInline]


@admin.register(RatingCriterion)
class RatingCriterionAdmin(admin.ModelAdmin):
    list_display = ("name", "order", "for_movies", "for_books", "is_active")
    # name satir linki oldugu icin list_editable'a giremez; geri kalani
    # liste ekranindan toplu duzenlenebilir.
    list_editable = ("order", "for_movies", "for_books", "is_active")
    search_fields = ("name", "description")


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "created_at", "is_read")
    list_filter = ("is_read", "created_at")
    search_fields = ("name", "email", "message")
    readonly_fields = ("name", "email", "message", "created_at")
    list_editable = ("is_read",)
    ordering = ("-created_at",)