from django.shortcuts import render, get_object_or_404
from .models import Review


def review_list(request):
    reviews = Review.objects.filter(is_published=True)

    # Tür filtresi: ?tur=film / ?tur=dizi (Blog'daki ?kategori deseninin aynısı)
    selected = request.GET.get("tur", "")
    if selected:
        reviews = reviews.filter(content_type=selected)

    # Öne çıkan kart: önce işaretli olan; yoksa en yeni
    featured = reviews.filter(is_featured=True).first() or reviews.first()
    others = reviews.exclude(pk=featured.pk) if featured else reviews

    return render(request, "movies/review_list.html", {
        "featured": featured,
        "reviews": others,
        "selected": selected,
        "type_choices": Review.CONTENT_TYPE_CHOICES,
    })


def review_detail(request, slug):
    review = get_object_or_404(Review, slug=slug, is_published=True)
    return render(request, "movies/review_detail.html", {"review": review})