from django.shortcuts import render, get_object_or_404
from .models import BlogPost, Category


def post_list(request):
    published = BlogPost.objects.filter(is_published=True)

    # Filtre hapları için tüm kategoriler
    categories = Category.objects.all()

    # Adresteki ?kategori=... değerini oku (yoksa boş = "Tümü")
    selected = request.GET.get("kategori", "")
    if selected:
        published = published.filter(category__name=selected)

    # Öne çıkan kart: önce "öne çıkan"; o yoksa en yeni
    featured = published.filter(is_featured=True).first() or published.first()

    if featured:
        others = published.exclude(pk=featured.pk)
    else:
        others = published

    return render(request, "blog/post_list.html", {
        "featured": featured,
        "posts": others,
        "categories": categories,
        "selected": selected,
    })


def post_detail(request, slug):
    post = get_object_or_404(BlogPost, slug=slug, is_published=True)
    return render(request, "blog/post_detail.html", {"post": post})