from django.contrib import admin
from .models import Profile, Experience


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