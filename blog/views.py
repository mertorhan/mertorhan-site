from django.shortcuts import render, get_object_or_404
from .models import BlogPost, Category


def post_list(request):
    # prefetch_related: reading_time property'si bloklari okur. Olmasaydi
    # sablondaki {{ featured.reading_time }} her cagride ayri sorgu atardi.
    published = BlogPost.objects.filter(is_published=True).prefetch_related("sections")

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
    # prefetch_related: bloklari tek ek sorguda ceker.
    # Olmasaydi sablondaki dongu her blok icin ayri sorgu atardi (N+1).
    post = get_object_or_404(
        BlogPost.objects.prefetch_related("sections"),
        slug=slug,
        is_published=True,
    )

    # Once satir sonlarini tek tipe cevir (\r\n -> \n),
    # cunku form metni Windows tarzi \r\n ile gelir; yoksa split bulamaz.
    body = post.body.replace("\r\n", "\n").replace("\r", "\n")

    # Ilk paragraf + geri kalani (alintiyi aralarina koymak icin)
    parts = body.split("\n\n", 1)
    first_part = parts[0]
    rest_part = parts[1] if len(parts) > 1 else ""

    # Icindekiler listesi. Sablonda hazirlanamaz: Django sablonu boolean
    # alana gore filtreleyemez.
    # .all() (.filter() degil): yukaridaki prefetch onbellegini kullanir,
    # .filter() yazilsaydi prefetch bosa gider ve yeni sorgu atilirdi.
    toc = [
        s for s in post.sections.all()
        if s.kind == "heading" and s.in_toc and s.text
    ]

    # Esik ISARETLI baslik sayisina bakar, toplam baslik sayisina DEGIL.
    # Yazida 6 baslik olup 1'i isaretliyse liste cikmaz: tek maddelik
    # icindekiler gezinmeye yaramaz, sadece gurultu olur.
    if len(toc) < 2:
        toc = []

    return render(request, "blog/post_detail.html", {
        "post": post,
        "first_part": first_part,
        "rest_part": rest_part,
        "toc": toc,
    })