from django.shortcuts import render, get_object_or_404
from .models import Guide


# Detay sayfasında kutu olarak gösterilecek kategoriler (sıra önemli)
CATEGORY_SECTIONS = [
    ("yeme-icme", "Yeme-İçme"),
    ("ogrenme", "Öğrenme"),
    ("konaklama", "Konaklama"),
    ("deneyim", "Deneyim"),
]


def guide_list(request):
    # Yayında olan tüm gezileri çek (en yeni üstte — Meta.ordering'den gelir)
    guides = Guide.objects.filter(is_published=True)

    # Öne çıkan kart: önce "öne çıkan" işaretli; o yoksa en yeni
    featured = guides.filter(is_featured=True).first() or guides.first()

    # Öne çıkan hariç geri kalanlar (grid için)
    if featured:
        others = guides.exclude(pk=featured.pk)
    else:
        others = guides

    return render(request, "guide/guide_list.html", {
        "featured": featured,
        "guides": others,
    })


def guide_detail(request, slug):
    # Slug'a göre tek geziyi bul; yoksa 404
    guide = get_object_or_404(Guide, slug=slug, is_published=True)

    # Bu geziye bağlı duraklar (sıraya göre — Meta.ordering'den gelir)
    # list(...) → tek sorguda çek, kategorileri Python'da süz (4 ayrı sorgu olmasın)
    stops = list(guide.stops.all())

    # Dolu kategorileri hazırla — boş olanlar listeye hiç girmez,
    # yani sayfada da hiç görünmez (senin istisna kuralın burada 🎯)
    category_sections = []
    for key, label in CATEGORY_SECTIONS:
        section_stops = [s for s in stops if s.point_type == key]
        if section_stops:
            category_sections.append({"label": label, "stops": section_stops})

    return render(request, "guide/guide_detail.html", {
        "guide": guide,
        "stops": stops,
        "category_sections": category_sections,
    })