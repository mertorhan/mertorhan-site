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

    # Once satir sonlarini tek tipe cevir (\r\n -> \n),
    # cunku form metni Windows tarzi \r\n ile gelir; yoksa split bulamaz.
    body = post.body.replace("\r\n", "\n").replace("\r", "\n")

    # Ilk paragraf + geri kalani (alintiyi aralarina koymak icin)
    parts = body.split("\n\n", 1)
    first_part = parts[0]
    rest_part = parts[1] if len(parts) > 1 else ""

    return render(request, "blog/post_detail.html", {
        "post": post,
        "first_part": first_part,
        "rest_part": rest_part,
    })