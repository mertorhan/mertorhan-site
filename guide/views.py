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

    # --- 1) Filtreleri adres çubuğundan oku ---
    # Örn: /guide/?sehir=İzmir&butce=₺₺  (boşsa filtre yok demektir)
    sehir = request.GET.get("sehir", "")
    tur = request.GET.get("tur", "")
    butce = request.GET.get("butce", "")
    zaman = request.GET.get("zaman", "")

    # --- 2) Dolu olan her filtreyi sorguya ekle ---
    # QuerySet "tembel"dir: filter üst üste eklenir, tek SQL sorgusu çalışır.
    if sehir:
        guides = guides.filter(city=sehir)
    if tur:
        guides = guides.filter(entry_type=tur)
    if butce:
        guides = guides.filter(budget=butce)
    if zaman:
        guides = guides.filter(best_time=zaman)

    filtre_aktif = any([sehir, tur, butce, zaman])

    # --- 3) Öne çıkan büyük kart: sadece filtre YOKKEN göster ---
    # Filtre varken kullanıcı net bir sonuç listesi bekler.
    featured = None
    others = guides
    if not filtre_aktif:
        featured = guides.filter(is_featured=True).first() or guides.first()
        if featured:
            others = guides.exclude(pk=featured.pk)

    # --- 4) Şehir menüsü: elle yazmak yerine veritabanından, tekrarsız ---
    # Yeni şehirli bir gezi eklediğinde menüye kendiliğinden düşer.
    cities = (
        Guide.objects.filter(is_published=True)
        .exclude(city="")
        .values_list("city", flat=True)
        .distinct()
        .order_by("city")
    )

    return render(request, "guide/guide_list.html", {
        "featured": featured,
        "guides": others,
        "cities": cities,
        "entry_type_choices": Guide.ENTRY_TYPE_CHOICES,
        "budget_choices": Guide.BUDGET_CHOICES,
        "best_time_choices": Guide.BEST_TIME_CHOICES,
        "selected": {"sehir": sehir, "tur": tur, "butce": butce, "zaman": zaman},
        "filtre_aktif": filtre_aktif,
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