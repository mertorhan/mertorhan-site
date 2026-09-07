from django.db.models import Count, Q
from django.db.models.functions import ExtractYear
from django.shortcuts import render, get_object_or_404

from .models import Author, Book, Genre, Publisher, Translator


# --------------------------------------------------------------------
# Filtre altyapisi
#
# Asagidaki yardimcilar (PUAN_KOVALARI, _sayilar, _secenek,
# _yil_secenekleri, _isim_secenekleri, _puan_secenekleri) movies/views.py'den
# KOPYALANDI. Bu bilincli bir tekrar, dikkatsizlik degil.
#
# Ortak bir yere tasima isi AYRI BIR KARTTA yapilacak. Gerekce: iki ornek
# gormeden dogru soyutlama cikarilamaz. Su an film ile kitap benzer ama ayni
# degil (filmde Film/Dizi ust ayrimi var, kitapta yok); erken soyutlarsak
# soyutlama bu farki tasimak icin egilir ve ikisine birden kotu uyar.
# Ucuncu bir bolum gelirse veya ikisi bir sure yan yana durup gercekten ayni
# kalirsa, o zaman ortak yer belli olur.
# --------------------------------------------------------------------

# Puan kovalari. Sinir deger UST kovaya gider: 9,0 -> 9plus, 8,0 -> 8to9.
# Puani olmayan (NULL) kitap hicbir kovaya girmez; karsilastirmalar NULL'i
# zaten disarida birakiyor.
# Sinirlar filmdekiyle AYNI olsun diye birebir kopyalandi — iki bolumde
# "8 — 9" ayni araligi anlatmali.
PUAN_KOVALARI = [
    ("9plus", "9 ve üzeri", Q(rating__gte=9)),
    ("8to9", "8 — 9", Q(rating__gte=8, rating__lt=9)),
    ("7to8", "7 — 8", Q(rating__gte=7, rating__lt=8)),
    ("alt7", "7 altı", Q(rating__lt=7)),
]

# Isim listeleri: (parametre adi, baslik, model, Book'taki alan)
#
# Parametre adi duz "tur" — movies'te "tur_id" olmak ZORUNDAYDI cunku orada
# "tur" Film/Dizi ayrimina ayrilmisti. Kitapta oyle bir ust ayrim yok, isim
# serbest.
#
# yayinevi digerlerinden farkli: ForeignKey (kitabin TEK yayinevi olur),
# otekiler ManyToMany. Filtreleme ve sayma kodu ikisinde de ayni calisiyor,
# bu yuzden ayni listede duruyorlar.
ISIM_FILTRELERI = [
    ("yazar", "Yazar", Author, "authors"),
    ("cevirmen", "Çevirmen", Translator, "translators"),
    ("yayinevi", "Yayınevi", Publisher, "publisher"),
    ("tur", "Tür", Genre, "genres"),
]


def _sayilar(deger_listesi):
    """
    Adres cubugundan gelen degerleri tam sayiya cevirir, cevrilemeyeni atar.
    Elle yazilmis bir adres (?yazar=abc) sayfayi patlatmasin.
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

    ADET her zaman veritabanindaki TOPLAM yayinlanmis kitap sayisi:
    diger filtre secimlerine gore DEGISMEZ.
    """
    taban = Book.objects.filter(is_published=True)

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
            taban.exclude(read_at=None)
            .annotate(yil=ExtractYear("read_at"))
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

    Dort modelin de Book'a ters sorgu adi "book" (hicbirinde related_name
    verilmedi), bu yuzden tek fonksiyon dordunu de sayiyor — FK olan
    Publisher dahil.
    """
    kayitlar = (
        model.objects.annotate(
            adet=Count("book", filter=Q(book__is_published=True))
        )
        .filter(adet__gt=0)
    )
    return [_secenek(k.pk, k.name, k.adet, secililer) for k in kayitlar]


def _puan_secenekleri(secililer):
    """Dort kovanin adedi tek sorguda."""
    sayimlar = Book.objects.filter(is_published=True).aggregate(
        **{anahtar: Count("id", filter=kosul) for anahtar, _, kosul in PUAN_KOVALARI}
    )
    return [
        _secenek(anahtar, etiket, sayimlar[anahtar], secililer)
        for anahtar, etiket, _ in PUAN_KOVALARI
        if sayimlar[anahtar]
    ]


def book_list(request):
    books = Book.objects.filter(is_published=True)

    # Öne çıkan kart: önce işaretli olan; yoksa en yeni
    featured = books.filter(is_featured=True).first() or books.first()
    others = books.exclude(pk=featured.pk) if featured else books

    # ------------------------------------------------------------------
    # Yedi filtre — KATMAN KURALI
    #
    # Filtreler SADECE asagidaki grid'i suzer. featured'a dokunulmuyor:
    # filtreye uymasa bile yerinde kaliyor.
    #
    # Birlestirme: ayni filtre icinde coklu secim VEYA (__in / Q|Q),
    # farkli filtreler arasi VE (ardisik .filter cagrilari).
    # ------------------------------------------------------------------
    secimler = {ad: request.GET.getlist(ad) for ad in
                ["basim", "okuma", "yazar", "cevirmen", "yayinevi", "tur", "puan"]}

    filtre_var = False

    basim = _sayilar(secimler["basim"])
    if basim:
        others = others.filter(release_year__in=basim)
        filtre_var = True

    okuma = _sayilar(secimler["okuma"])
    if okuma:
        others = others.filter(read_at__year__in=okuma)
        filtre_var = True

    iliski_secildi = False
    for ad, _baslik, _model, alan in ISIM_FILTRELERI:
        idler = _sayilar(secimler[ad])
        if idler:
            # Her iliski icin AYRI .filter cagrisi: ayri JOIN acilir ve
            # "yazar A VE tur Roman" dogru calisir. Tek cagrida
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
        # kitapta secili iki yazar varsa kitap grid'de IKI KEZ cikar.
        #
        # yayinevi tek basina mukerrer uretmez (FK, coka-bir) ama dongu onu
        # da buraya sokabiliyor. Fazladan distinct() zararsiz; iki ayri yol
        # acmak kodu kurali anlatmaz hale getirirdi.
        others = others.distinct()

    # ------------------------------------------------------------------
    # Secenek listeleri. Hepsi view'da hazirlanir, sablon sadece basar.
    # Hic secenegi olmayan filtre listeye girmez: olu bir acilir panel
    # basmayalim.
    # ------------------------------------------------------------------
    ham_filtreler = [
        ("basim", "Basım yılı", _yil_secenekleri("release_year", secimler["basim"])),
        ("okuma", "Okuma yılı", _yil_secenekleri("read_at", secimler["okuma"])),
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

    return render(request, "books/book_list.html", {
        "featured": featured,
        "books": others,
        "filtreler": filtreler,
        "filtre_var": filtre_var,
    })


def book_detail(request, slug):
    # prefetch: alt kriterler sayfada listeleniyor. Onsuz her kriter icin
    # bir sorgu daha acilirdi.
    book = get_object_or_404(
        Book.objects.prefetch_related("scores__criterion"),
        slug=slug,
        is_published=True,
    )
    return render(request, "books/book_detail.html", {"book": book})
