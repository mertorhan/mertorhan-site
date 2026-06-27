from django.shortcuts import render
from blog.models import BlogPost
from guide.models import Guide
from gallery.models import Photo
from .models import Profile


def home(request):
    # Öne çıkan yazılar (yoksa en yeni)
    posts = BlogPost.objects.filter(is_published=True, is_featured=True)[:3]
    if not posts:
        posts = BlogPost.objects.filter(is_published=True)[:3]

    # Öne çıkan rotalar (yoksa en yeni)
    guides = Guide.objects.filter(is_published=True, is_featured=True)[:3]
    if not guides:
        guides = Guide.objects.filter(is_published=True)[:3]

    # Hero için tek bir öne çıkan gezi
    hero_guide = guides[0] if guides else None

    # Ana sayfa galeri şeridi için son fotoğraflar (Blok 3'te kullanılacak)
    gallery_photos = Photo.objects.filter(is_published=True)[:4]

    # Profil (tek kayıt) — fotoğraf vb. için
    profile = Profile.objects.first()

    return render(request, "core/home.html", {
        "posts": posts,
        "guides": guides,
        "hero_guide": hero_guide,
        "gallery_photos": gallery_photos,
        "profile": profile,
    })


def about(request):
    # Hakkında sayfası tek Profil kaydından beslenir
    profile = Profile.objects.first()
    return render(request, "core/about.html", {"profile": profile})