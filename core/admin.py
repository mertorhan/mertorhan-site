from django.contrib import admin
from .models import Profile, Experience, ContactMessage


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


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "created_at", "is_read")
    list_filter = ("is_read", "created_at")
    search_fields = ("name", "email", "message")
    readonly_fields = ("name", "email", "message", "created_at")
    list_editable = ("is_read",)
    ordering = ("-created_at",)