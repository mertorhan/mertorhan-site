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
    stops = list(guide.stops.all())

    # Dolu kategorileri hazırla — boş olanlar listeye hiç girmez
    category_sections = []
    for key, label in CATEGORY_SECTIONS:
        section_stops = [s for s in stops if s.point_type == key]
        if section_stops:
            category_sections.append({"label": label, "stops": section_stops})

    # --- Harita noktaları ---
    # Yalnızca koordinatı OLAN duraklar haritaya girer; hiç yoksa harita çizilmez.
    # float(...) → Decimal doğrudan JSON'a çevrilemez; sayıya çeviriyoruz.
    map_points = [
        {"order": s.order, "name": s.name, "lat": float(s.latitude), "lng": float(s.longitude)}
        for s in stops
        if s.latitude is not None and s.longitude is not None
    ]

    # Tek mekan girişi: koordinat durakta değil, gezinin kendi üstünde
    if not map_points and guide.latitude is not None and guide.longitude is not None:
        map_points = [{
            "order": 1,
            "name": guide.title,
            "lat": float(guide.latitude),
            "lng": float(guide.longitude),
        }]

    # --- Google Maps "tüm rotayı aç" derin bağlantısı (2+ nokta varsa) ---
    # origin=ilk durak, destination=son durak, aradakiler waypoints.
    # Duraklar arası "|" ayracı URL'de %7C olarak yazılır (kodlanmış hali).
    gmaps_route_url = ""
    if len(map_points) >= 2:
        origin = f"{map_points[0]['lat']},{map_points[0]['lng']}"
        destination = f"{map_points[-1]['lat']},{map_points[-1]['lng']}"
        gmaps_route_url = (
            "https://www.google.com/maps/dir/?api=1"
            f"&origin={origin}&destination={destination}&travelmode=walking"
        )
        middle = map_points[1:-1]
        if middle:
            waypoints = "%7C".join(f"{p['lat']},{p['lng']}" for p in middle)
            gmaps_route_url += f"&waypoints={waypoints}"

    return render(request, "guide/guide_detail.html", {
        "guide": guide,
        "stops": stops,
        "category_sections": category_sections,
        "map_points": map_points,
        "gmaps_route_url": gmaps_route_url,
    })