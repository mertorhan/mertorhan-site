from django.db.models import Count, Q
from django.db.models.functions import ExtractYear
from django.shortcuts import render, get_object_or_404

from .models import Actor, Director, Genre, Review, Screenwriter


# Puan kovalari. Sinir deger UST kovaya gider: 9,0 -> 9plus, 8,0 -> 8to9.
# Puani olmayan (NULL) film hicbir kovaya girmez; karsilastirmalar NULL'i
# zaten disarida birakiyor.
# Bu tek liste hem filtrelemede hem sayaclarda kullaniliyor — kova sinirini
# degistirmek isteyen SADECE buraya baksin.
PUAN_KOVALARI = [
    ("9plus", "9 ve üzeri", Q(rating__gte=9)),
    ("8to9", "8 — 9", Q(rating__gte=8, rating__lt=9)),
    ("7to8", "7 — 8", Q(rating__gte=7, rating__lt=8)),
    ("alt7", "7 altı", Q(rating__lt=7)),
]

# Isim listeleri: (parametre adi, baslik, model, Review'daki alan)
ISIM_FILTRELERI = [
    ("yonetmen", "Yönetmen", Director, "directors"),
    ("senarist", "Senarist", Screenwriter, "screenwriters"),
    ("oyuncu", "Oyuncu", Actor, "actors"),
    # DIKKAT: parametre adi "tur" DEGIL. "tur" zaten Film/Dizi ayriminda
    # kullaniliyor (asagida selected), ikisi cakisirdi.
    ("tur_id", "Tür", Genre, "genres"),
]


def _sayilar(deger_listesi):
    """
    Adres cubugundan gelen degerleri tam sayiya cevirir, cevrilemeyeni atar.
    Elle yazilmis bir adres (?yonetmen=abc) sayfayi patlatmasin.
    """
    sayilar = []
    for deger in deger_listesi:
        try:
            sayilar.append(int(deger))
        except (TypeError, ValueError):
            continue
    return sayilar


def _secenek(deger, etiket, adet, secililer):
    """Sablonun basacagi tek secenek; hesap burada biter."""
    return {
        "deger": str(deger),
        "etiket": str(etiket),
        "adet": adet,
        "secili": str(deger) in secililer,
    }


def _yil_secenekleri(alan, secililer):
    """
    Yil + adet listesi, yeniden eskiye.

    ADET her zaman veritabanindaki TOPLAM yayinlanmis film sayisi:
    ustteki Film/Dizi sekmesine ve diger secimlere gore DEGISMEZ.
    """
    taban = Review.objects.filter(is_published=True)

    if alan == "release_year":
        satirlar = (
            taban.exclude(release_year=None)
            .values("release_year")
            .annotate(adet=Count("id"))
            .order_by("-release_year")
        )
        ciftler = [(s["release_year"], s["adet"]) for s in satirlar]
    else:
        satirlar = (
            taban.exclude(watched_at=None)
            .annotate(yil=ExtractYear("watched_at"))
            .values("yil")
            .annotate(adet=Count("id"))
            .order_by("-yil")
        )
        ciftler = [(s["yil"], s["adet"]) for s in satirlar]

    return [_secenek(yil, yil, adet, secililer) for yil, adet in ciftler if adet]


def _isim_secenekleri(model, secililer):
    """
    Kunye kayitlarini adetleriyle listeler. Hic kullanilmayan kayit
    (adet=0) listeye HIC girmez. Siralama modelin Meta.ordering'inden
    (name) geliyor.
    """
    kayitlar = (
        model.objects.annotate(
            adet=Count("review", filter=Q(review__is_published=True))
        )
        .filter(adet__gt=0)
    )
    return [_secenek(k.pk, k.name, k.adet, secililer) for k in kayitlar]


def _puan_secenekleri(secililer):
    """Dort kovanin adedi tek sorguda."""
    sayimlar = Review.objects.filter(is_published=True).aggregate(
        **{anahtar: Count("id", filter=kosul) for anahtar, _, kosul in PUAN_KOVALARI}
    )
    return [
        _secenek(anahtar, etiket, sayimlar[anahtar], secililer)
        for anahtar, etiket, _ in PUAN_KOVALARI
        if sayimlar[anahtar]
    ]


def review_list(request):
    reviews = Review.objects.filter(is_published=True)

    # Tür filtresi: ?tur=film / ?tur=dizi (Blog'daki ?kategori deseninin aynısı)
    selected = request.GET.get("tur", "")
    if selected:
        reviews = reviews.filter(content_type=selected)

    # Öne çıkan kart: önce işaretli olan; yoksa en yeni
    featured = reviews.filter(is_featured=True).first() or reviews.first()
    others = reviews.exclude(pk=featured.pk) if featured else reviews

    # ------------------------------------------------------------------
    # Yedi filtre — KATMAN KURALI
    #
    # Ustteki Tumu/Film/Dizi secimi HER SEYI suzer (one cikan + grid);
    # buradaki yedi filtre ise ondan gecenler icinde SADECE grid'i suzer.
    # featured'a dokunulmuyor: filtreye uymasa bile yerinde kaliyor.
    #
    # Birlestirme: ayni filtre icinde coklu secim VEYA (__in / Q|Q),
    # farkli filtreler arasi VE (ardisik .filter cagrilari).
    # ------------------------------------------------------------------
    secimler = {ad: request.GET.getlist(ad) for ad in
                ["yapim", "izleme", "yonetmen", "senarist", "oyuncu", "tur_id", "puan"]}

    filtre_var = False

    yapim = _sayilar(secimler["yapim"])
    if yapim:
        others = others.filter(release_year__in=yapim)
        filtre_var = True

    izleme = _sayilar(secimler["izleme"])
    if izleme:
        others = others.filter(watched_at__year__in=izleme)
        filtre_var = True

    iliski_secildi = False
    for ad, _baslik, _model, alan in ISIM_FILTRELERI:
        idler = _sayilar(secimler[ad])
        if idler:
            # Her iliski icin AYRI .filter cagrisi: ayri JOIN acilir ve
            # "yonetmen A VE tur Action" dogru calisir. Tek cagrida
            # birlestirseydik "ayni satirda ikisi birden" anlamina gelirdi.
            others = others.filter(**{f"{alan}__id__in": idler})
            iliski_secildi = True
            filtre_var = True

    puan_secili = [a for a in secimler["puan"] if a in {k for k, _, _ in PUAN_KOVALARI}]
    if puan_secili:
        kovalar = {anahtar: kosul for anahtar, _, kosul in PUAN_KOVALARI}
        sorgu = Q()
        for anahtar in puan_secili:
            sorgu |= kovalar[anahtar]
        others = others.filter(sorgu)
        filtre_var = True

    if iliski_secildi:
        # ZORUNLU: coka-cok iliski uzerinden filtrelemek JOIN uretir; bir
        # filmde secili iki yonetmen varsa film grid'de IKI KEZ cikar.
        others = others.distinct()

    # ------------------------------------------------------------------
    # Secenek listeleri. Hepsi view'da hazirlanir, sablon sadece basar.
    # Hic secenegi olmayan filtre listeye girmez: olu bir acilir panel
    # basmayalim.
    # ------------------------------------------------------------------
    ham_filtreler = [
        ("yapim", "Yapım yılı", _yil_secenekleri("release_year", secimler["yapim"])),
        ("izleme", "İzleme yılı", _yil_secenekleri("watched_at", secimler["izleme"])),
    ]
    ham_filtreler += [
        (ad, baslik, _isim_secenekleri(model, secimler[ad]))
        for ad, baslik, model, _alan in ISIM_FILTRELERI
    ]
    ham_filtreler.append(("puan", "Puan", _puan_secenekleri(secimler["puan"])))

    filtreler = [
        {
            "ad": ad,
            "baslik": baslik,
            "secenekler": secenekler,
            "secili_adet": sum(1 for s in secenekler if s["secili"]),
        }
        for ad, baslik, secenekler in ham_filtreler
        if secenekler
    ]

    return render(request, "movies/review_list.html", {
        "featured": featured,
        "reviews": others,
        "selected": selected,
        "type_choices": Review.CONTENT_TYPE_CHOICES,
        "filtreler": filtreler,
        "filtre_var": filtre_var,
    })


def review_detail(request, slug):
    # prefetch: alt kriterler sayfada listeleniyor. Onsuz her kriter icin
    # bir sorgu daha acilirdi (9 kriter = 9 ekstra sorgu).
    review = get_object_or_404(
        Review.objects.prefetch_related(
            "scores__criterion", "directors", "screenwriters", "actors", "genres"
        ),
        slug=slug,
        is_published=True,
    )
    return render(request, "movies/review_detail.html", {"review": review})
