from django.shortcuts import render
from blog.models import BlogPost
from guide.models import Guide


def home(request):
    # Ana sayfadaki "Öne çıkan yazılar" bölümü için yazıları getir.
    # Once "öne çıkan" işaretli yazılar; onlar yoksa en yeni yazılar.
    posts = BlogPost.objects.filter(is_published=True, is_featured=True)[:3]
    if not posts:
        posts = BlogPost.objects.filter(is_published=True)[:3]

    # Ana sayfadaki "Öne çıkan rotalar" bölümü için gezileri getir (aynı mantık).
    guides = Guide.objects.filter(is_published=True, is_featured=True)[:3]
    if not guides:
        guides = Guide.objects.filter(is_published=True)[:3]

    # Hero için tek bir öne çıkan gezi (yoksa en yeni). Liste boşsa None gelir.
    hero_guide = guides[0] if guides else None

    return render(request, "core/home.html", {
        "posts": posts,
        "guides": guides,
        "hero_guide": hero_guide,
    })


def about(request):
    return render(request, "core/about.html")