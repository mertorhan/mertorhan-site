from django.shortcuts import render
from blog.models import BlogPost


def home(request):
    # Ana sayfadaki "Öne çıkan yazılar" bölümü için yazıları getir.
    # Once "öne çıkan" işaretli yazılar; onlar yoksa en yeni yazılar.
    posts = BlogPost.objects.filter(is_published=True, is_featured=True)[:3]
    if not posts:
        posts = BlogPost.objects.filter(is_published=True)[:3]

    return render(request, "core/home.html", {"posts": posts})


def about(request):
    return render(request, "core/about.html")