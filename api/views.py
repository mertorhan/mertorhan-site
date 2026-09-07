from django.db.models import Count, Q
from django.db.models.functions import ExtractYear
from rest_framework import generics
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from blog.models import BlogPost
from books.models import Book
from gallery.models import Photo
from movies.models import Review
from .serializers import (
    BlogPostSerializer, BlogPostDetailSerializer,
    ReviewSerializer, ReviewDetailSerializer,
    BookSerializer, BookDetailSerializer,
    PhotoSerializer,
)


# --------------------------------------------------------------------
# Filtre altyapisi
#
# PUAN_KOVALARI ve _sayilar, movies/views.py ile books/views.py'den
# KOPYALANDI. Bu UCUNCU kopya ve bilincli bir tekrar.
#
# Neden hala tasinmadi: site view'lari sablon baglami hazirliyor (secenek
# listeleri, adetler, secili isaretleri), API ise sadece queryset suzuyor.
# Ortak olan kisim kurallar — kova sinirlari, bozuk degerin atilmasi,
# VEYA/VE katmanlari. Bunlari ortak bir yere tasima isi AYRI BIR KARTTA
# yapilacak; artik uc ornek var, dogru soyutlama nihayet gorulebilir.
#
# O kart yapilana kadar DIKKAT: kova sinirini degistiren UC dosyaya birden
# bakmak zorunda.
# --------------------------------------------------------------------

# Sinirlar site ile AYNI olmali: mobil uygulamada "8 — 9" ile web'de
# "8 — 9" ayni araligi anlatmazsa kullanici hakli olarak sasirir.
# Sinir deger UST kovaya gider: 9,0 -> 9plus, 8,0 -> 8to9.
# Puani olmayan (NULL) kayit hicbir kovaya girmez.
PUAN_KOVALARI = {
    '9plus': Q(rating__gte=9),
    '8to9': Q(rating__gte=8, rating__lt=9),
    '7to8': Q(rating__gte=7, rating__lt=8),
    'alt7': Q(rating__lt=7),
}

# Kova etiketleri AYRI bir yapida: PUAN_KOVALARI'nin sekli bilerek
# degistirilmedi, _puan_filtresi ona bagli.
# Liste cunku SIRA onemli — yuksekten dusuge, sitedeki sirayla ayni.
# Metinler de site ile ayni olmali (books/views.py, movies/views.py).
PUAN_ETIKETLERI = [
    ('9plus', '9 ve üzeri'),
    ('8to9', '8 — 9'),
    ('7to8', '7 — 8'),
    ('alt7', '7 altı'),
]


def _sayilar(deger_listesi):
    """Sorgu parametrelerini tam sayiya cevirir, cevrilemeyeni atar.

    ?author=abc HATA DONDURMEZ, sessizce yok sayilir ve tum liste doner.
    Site de boyle davraniyor (books/views.py) — iki taraf ayni sekilde
    affedici olsun ki mobil taraf iki farkli davranis kodlamasin.
    """
    sayilar = []
    for deger in deger_listesi:
        try:
            sayilar.append(int(deger))
        except (TypeError, ValueError):
            continue
    return sayilar


def _iliski_filtreleri(queryset, params, esleme):
    """Iliski parametrelerini uygular, distinct gerekip gerekmedigini doner.

    esleme: {parametre adi: queryset alan yolu}

    Her iliski icin AYRI .filter cagrisi: ayri JOIN acilir ve
    "yazar A VE tur Roman" dogru calisir. Tek cagrida birlestirseydik
    "ayni satirda ikisi birden" anlamina gelirdi.
    """
    iliski_secildi = False
    for ad, alan in esleme.items():
        idler = _sayilar(params.getlist(ad))
        if idler:
            queryset = queryset.filter(**{f'{alan}__id__in': idler})
            iliski_secildi = True
    return queryset, iliski_secildi


def _puan_filtresi(queryset, params):
    """Secili puan kovalarini VEYA ile birlestirip uygular.

    Taninmayan kova adi (?rating=uydurma) sessizce atilir.
    """
    secililer = [k for k in params.getlist('rating') if k in PUAN_KOVALARI]
    if not secililer:
        return queryset
    sorgu = Q()
    for anahtar in secililer:
        sorgu |= PUAN_KOVALARI[anahtar]
    return queryset.filter(sorgu)


def _yil_filtresi(queryset, params, ad, alan):
    """Yil parametresini uygular. Ayni parametre birden fazlaysa VEYA (__in)."""
    yillar = _sayilar(params.getlist(ad))
    if yillar:
        queryset = queryset.filter(**{alan: yillar})
    return queryset


class BlogPostPagination(PageNumberPagination):
    """Sayfa basina 20 kayit.

    settings.py'ye REST_FRAMEWORK blogu eklenmedigi icin sayfalama
    global degil, view seviyesinde tanimli.
    """

    page_size = 20


def published_posts():
    """Yayindaki yazilarin ortak queryset'i.

    Hem liste hem detay ucu bunu kullaniyor; yayin filtresi tek yerde
    dursun ki ileride bir uc yanlislikla taslak sizdirmasin.

    - is_published: yayinda olmayan icerik API'den asla donmez.
    - slug bos olanlar elenir: detay ucu slug ile calisiyor, ulasilamayan
      kaydi listede gostermek mobil tarafi yaniltir.
    - prefetch_related("sections"): reading_time property'si bloklari geziyor,
      olmasaydi her kayit icin ayri sorgu atilirdi (N+1).
    - select_related("category"): kategori adi her kayitta seri hale getiriliyor.
    """
    return (
        BlogPost.objects
        .filter(is_published=True)
        .exclude(slug__isnull=True)
        .exclude(slug='')
        .select_related('category')
        .prefetch_related('sections')
    )


def _kategori_filtresi(queryset, params):
    """?category=3 -> category__id__in. Blog ve galeri icin ortak.

    distinct() YOK ve bu bilincli: BlogPost.category ile Photo.category
    ForeignKey, yani coka-bir. Bir yazinin tek kategorisi olur, JOIN mukerrer
    satir uretmez. KB-110'da FK olan publisher fazladan distinct() aliyordu
    ama o M2M'lerle AYNI DONGUDEYDI; burada tek filtre var, dongu yok.

    ID tabanli — sitedeki blog ile FARKLI. Site blog'u ada gore suzuyor
    (?kategori=Yazilim, blog/views.py), galeriyi id'ye gore. API'de TUM
    iliski filtreleri id aliyor ki mobil tarafta tek desen kalsin: "filtre
    ucundan value al, liste ucuna aynen gonder".
    """
    idler = _sayilar(params.getlist('category'))
    if idler:
        queryset = queryset.filter(category__id__in=idler)
    return queryset


class BlogPostListView(generics.ListAPIView):
    """GET /api/v1/blog/ - yayindaki yazilarin listesi.

    Filtre (istege bagli, verilmezse tum liste doner):

      ?category=3   kategori id   category

    Ayni parametre birden cok kez verilirse VEYA (?category=1&category=2
    ikisinin de yazilari). Sayiya cevrilemeyen deger sessizce atilir, 400
    DONMEZ — KB-110'daki davranisin aynisi.

    Secenek listesi /api/v1/filters/blog/ ucunda.

    ListAPIView yalnizca GET tanimlar; POST 405 doner.
    """

    serializer_class = BlogPostSerializer
    pagination_class = BlogPostPagination

    def get_queryset(self):
        return _kategori_filtresi(published_posts(), self.request.query_params)


class BlogPostDetailView(generics.RetrieveAPIView):
    """GET /api/v1/blog/<slug>/ - tek yazi ve bloklari.

    RetrieveAPIView yalnizca GET tanimlar; PUT/PATCH/DELETE 405 doner.
    """

    serializer_class = BlogPostDetailSerializer
    lookup_field = 'slug'

    def get_queryset(self):
        return published_posts()


def published_reviews():
    """Yayindaki film/dizi incelemelerinin ortak queryset'i.

    Kunye iliskileri (directors, screenwriters, actors, genres) sadece
    detay serializer'inda oldugu icin prefetch burada DEGIL,
    ReviewDetailView'da zincirleniyor - liste ucu bosa sorgu atmasin.
    """
    return (
        Review.objects
        .filter(is_published=True)
        .exclude(slug__isnull=True)
        .exclude(slug='')
    )


def published_books():
    """Yayindaki kitaplarin ortak queryset'i.

    quotes prefetch'i sadece detayda gerekli; BookDetailView'da ekleniyor.
    """
    return (
        Book.objects
        .filter(is_published=True)
        .exclude(slug__isnull=True)
        .exclude(slug='')
    )


def published_photos():
    """Yayindaki fotograflarin queryset'i.

    Photo modelinde slug YOK, bu yuzden slug elemesi de yok.
    select_related("category"): kategori adi her kayitta seri hale
    getiriliyor, olmasaydi her foto icin ayri sorgu atilirdi (N+1).
    """
    return (
        Photo.objects
        .filter(is_published=True)
        .select_related('category')
    )


class ReviewListView(generics.ListAPIView):
    """GET /api/v1/movies/ - yayindaki film ve dizi incelemeleri.

    Filtreler (hepsi istege bagli, hicbiri verilmezse tum liste doner):

      ?year=2020          yapim yili        release_year
      ?watched_year=2024  izleme yili       watched_at'in yili
      ?director=1         yonetmen id       directors
      ?screenwriter=1     senarist id       screenwriters
      ?actor=1            oyuncu id         actors
      ?genre=1            tur id            genres
      ?rating=9plus       puan kovasi       9plus/8to9/7to8/alt7
      ?content_type=film  film ya da dizi   content_type

    Ayni parametre birden cok kez verilirse VEYA (?actor=1&actor=2 ikisinin
    de filmleri), farkli parametreler arasi VE. Sitedeki davranisin aynisi.

    PREFETCH YOK ve bu bilincli: ReviewSerializer hicbir iliski alani
    serialize etmiyor, iliski uzerinden filtrelemek de JOIN uretir, ek sorgu
    ACMAZ. Prefetch eklemek liste ucunda kullanilmayan veriyi cekmek olurdu
    — published_reviews() docstring'i de bunu soyluyor. Kunye iliskileri
    ReviewDetailView'da prefetch'leniyor, orada gercekten seri hale
    getiriliyorlar.
    """

    serializer_class = ReviewSerializer
    pagination_class = BlogPostPagination

    def get_queryset(self):
        params = self.request.query_params
        queryset = published_reviews()

        queryset = _yil_filtresi(queryset, params, 'year', 'release_year__in')
        queryset = _yil_filtresi(queryset, params, 'watched_year', 'watched_at__year__in')

        # content_type TEKIL: bir inceleme ya film ya dizi. Taninmayan deger
        # (?content_type=belgesel) sessizce atilir.
        gecerli_turler = {anahtar for anahtar, _etiket in Review.CONTENT_TYPE_CHOICES}
        icerik_turu = params.get('content_type')
        if icerik_turu in gecerli_turler:
            queryset = queryset.filter(content_type=icerik_turu)

        queryset, iliski_secildi = _iliski_filtreleri(queryset, params, {
            'director': 'directors',
            'screenwriter': 'screenwriters',
            'actor': 'actors',
            'genre': 'genres',
        })

        queryset = _puan_filtresi(queryset, params)

        if iliski_secildi:
            # ZORUNLU: coka-cok iliski uzerinden filtrelemek JOIN uretir; bir
            # filmde secili iki oyuncu varsa film sonucta IKI KEZ cikar.
            queryset = queryset.distinct()

        return queryset


class ReviewDetailView(generics.RetrieveAPIView):
    """GET /api/v1/movies/<slug>/ - tek inceleme, govde ve kunyesiyle."""

    serializer_class = ReviewDetailSerializer
    lookup_field = 'slug'

    def get_queryset(self):
        return published_reviews().prefetch_related(
            'directors', 'screenwriters', 'actors', 'genres'
        )


class BookListView(generics.ListAPIView):
    """GET /api/v1/books/ - yayindaki kitaplar.

    Filtreler (hepsi istege bagli, hicbiri verilmezse tum liste doner):

      ?year=2020        basim yili      release_year
      ?read_year=2024   okuma yili      read_at'in yili
      ?author=1         yazar id        authors
      ?translator=1     cevirmen id     translators
      ?publisher=1      yayinevi id     publisher (FK)
      ?genre=1          tur id          genres
      ?rating=9plus     puan kovasi     9plus/8to9/7to8/alt7

    Ayni parametre birden cok kez verilirse VEYA (?author=1&author=2
    ikisinin de kitaplari), farkli parametreler arasi VE. Sitedeki
    davranisin aynisi.

    PREFETCH YOK, ReviewListView'daki ile ayni gerekce: BookSerializer
    iliski alani serialize etmiyor (release_year ve read_at duz alan),
    filtre de JOIN ile calisiyor. Kunye iliskileri BookDetailView'da
    prefetch'leniyor.
    """

    serializer_class = BookSerializer
    pagination_class = BlogPostPagination

    def get_queryset(self):
        params = self.request.query_params
        queryset = published_books()

        queryset = _yil_filtresi(queryset, params, 'year', 'release_year__in')
        queryset = _yil_filtresi(queryset, params, 'read_year', 'read_at__year__in')

        queryset, iliski_secildi = _iliski_filtreleri(queryset, params, {
            'author': 'authors',
            'translator': 'translators',
            'publisher': 'publisher',
            'genre': 'genres',
        })

        queryset = _puan_filtresi(queryset, params)

        if iliski_secildi:
            # ZORUNLU: coka-cok iliski uzerinden filtrelemek JOIN uretir; bir
            # kitapta secili iki yazar varsa kitap sonucta IKI KEZ cikar.
            #
            # publisher tek basina mukerrer uretmez (FK, coka-bir) ama ayni
            # dongude oldugu icin buraya girebiliyor. Fazladan distinct()
            # zararsiz; iki ayri yol acmak kodu kurali anlatmaz hale
            # getirirdi. (books/views.py'de de ayni karar.)
            queryset = queryset.distinct()

        return queryset


class BookDetailView(generics.RetrieveAPIView):
    """GET /api/v1/books/<slug>/ - tek kitap, govde, alintilar ve kunyesiyle.

    prefetch/select_related: BookDetailSerializer artik kunye iliskilerini de
    donduruyor. Onlarsiz her iliski icin ayri sorgu acilirdi (N+1).
    ReviewDetailView'daki desenin aynisi.
    """

    serializer_class = BookDetailSerializer
    lookup_field = 'slug'

    def get_queryset(self):
        return (
            published_books()
            .select_related('publisher')
            .prefetch_related('quotes', 'authors', 'translators', 'genres')
        )


class PhotoListView(generics.ListAPIView):
    """GET /api/v1/photos/ - yayindaki fotograflar.

    Filtre (istege bagli, verilmezse tum liste doner):

      ?category=3   kategori id   category

    Ayni parametre birden cok kez verilirse VEYA. Sayiya cevrilemeyen deger
    sessizce atilir, 400 DONMEZ. Secenek listesi /api/v1/filters/photos/'da.

    Detay ucu yok: Photo'da slug alani bulunmuyor ve tum kunye bilgisi
    zaten liste kaydinda donuyor.
    """

    serializer_class = PhotoSerializer
    pagination_class = BlogPostPagination

    def get_queryset(self):
        return _kategori_filtresi(published_photos(), self.request.query_params)


# --------------------------------------------------------------------
# Filtre secenekleri uclari
#
# Secenek + sayac hesaplama artik books, movies, gallery ve api'de —
# DORDUNCU kopya. Yukaridaki filtre altyapisi ucuncuydu; bu kart ikisini
# birden buyuttu. Bilincli, ama borc da buyudu: ortak yere tasima AYRI BIR
# KARTTA yapilacak.
#
# NEDEN sitedeki teknik AYNEN kopyalanamadi:
# Site sayaci TERS yonden aliyor —
#     Author.objects.annotate(adet=Count("book", filter=Q(book__is_published=True)))
# Bu teknik published_books()/published_posts()'un slug elemesini GOREMEZ,
# cunku eleme queryset'te duruyor, iliskide degil. Sayac ile liste ayni
# tabandan gelmezse listede olmayan bir kayit sayaca girer.
#
# Bu yuzden burada ILERI yonden sayiyoruz: taban queryset'ten baslayip
# .values(...).annotate(...) ile grupluyoruz. Sonuc olarak slug'i bos
# yayinlanmis bir kayit SITEDE sayilir, API'de sayilmaz — istenen bu,
# zaten listede de donmuyor.
# --------------------------------------------------------------------


def _secenek(deger, etiket, adet):
    """Sablon degil, JSON: her secenek TAM UC alan tasir.

    Mobil tarafta tek bir filtre bileseni dort ucun hepsine hizmet edecek;
    bunun sarti bicimin her yerde ayni olmasi.
    """
    return {'value': deger, 'label': str(etiket), 'count': adet}


def _iliski_secenekleri(taban, alan):
    """Bir iliski alani icin secenek listesi, taban queryset'ten sayarak.

    alan: "authors" gibi M2M ya da "publisher"/"category" gibi FK.

    order_by ACIKCA veriliyor. Verilmezse modelin Meta.ordering'i
    (-published_at) GROUP BY'a girer ve ayni yazar birden fazla satira
    bolunur — sessiz ve fark edilmesi zor bir hata.

    Count(distinct=True): tek JOIN'de gerekmiyor ama ucuz sigorta.
    isnull=False: iliskisi olmayan kayit NULL grubu uretmesin.
    """
    satirlar = (
        taban
        .filter(**{f'{alan}__isnull': False})
        .values(f'{alan}__id', f'{alan}__name')
        .annotate(adet=Count('id', distinct=True))
        .order_by(f'{alan}__name')
    )
    return [
        _secenek(s[f'{alan}__id'], s[f'{alan}__name'], s['adet'])
        for s in satirlar if s['adet']
    ]


def _yil_secenekleri(taban, alan, tarih_alani=False):
    """Yil secenekleri, yeniden eskiye.

    value SAYI donuyor (metin degil): mobil taraf filtre ucundan aldigi
    degeri liste ucuna aynen gonderecek, tip donusumuyle ugrasmasin.
    """
    if tarih_alani:
        satirlar = (
            taban.exclude(**{alan: None})
            .annotate(yil=ExtractYear(alan))
            .values('yil')
            .annotate(adet=Count('id'))
            .order_by('-yil')
        )
        ciftler = [(s['yil'], s['adet']) for s in satirlar]
    else:
        satirlar = (
            taban.exclude(**{alan: None})
            .values(alan)
            .annotate(adet=Count('id'))
            .order_by(f'-{alan}')
        )
        ciftler = [(s[alan], s['adet']) for s in satirlar]

    return [_secenek(yil, yil, adet) for yil, adet in ciftler if adet]


def _puan_secenekleri(taban):
    """Dort kovanin adedi tek sorguda, yuksekten dusuge."""
    sayimlar = taban.aggregate(
        **{anahtar: Count('id', filter=PUAN_KOVALARI[anahtar])
           for anahtar, _etiket in PUAN_ETIKETLERI}
    )
    return [
        _secenek(anahtar, etiket, sayimlar[anahtar])
        for anahtar, etiket in PUAN_ETIKETLERI
        if sayimlar[anahtar]
    ]


def _content_type_secenekleri(taban):
    """Film/dizi secenekleri.

    Etiketler Review.CONTENT_TYPE_CHOICES'tan okunuyor, elle YAZILMIYOR:
    modele yeni bir tur eklenirse burasi kendiliginden ogrenir.
    Sira da CHOICES'taki sira.
    """
    sayimlar = dict(
        taban.values_list('content_type')
        .annotate(adet=Count('id'))
        .order_by()
        .values_list('content_type', 'adet')
    )
    return [
        _secenek(anahtar, etiket, sayimlar[anahtar])
        for anahtar, etiket in Review.CONTENT_TYPE_CHOICES
        if sayimlar.get(anahtar)
    ]


def _dolu_olanlar(secenekler):
    """Secenegi kalmayan anahtari yanittan TAMAMEN cikarir.

    Bos dizi donmuyoruz: mobil taraf "anahtar var ama bos" ile "anahtar
    yok" arasinda ayrim yapmak zorunda kalmasin, tek kural olsun —
    yanitta ne varsa gosterilir.
    """
    return {ad: liste for ad, liste in secenekler.items() if liste}


class FiltreSecenekleriView(APIView):
    """Filtre seceneklerini donduren uclarin ortak tabani.

    Bu uclar PARAMETRE ALMAZ: sayaclar her zaman veritabanindaki toplam
    yayinlanmis kayit sayisini gosterir, diger secimlere gore DEGISMEZ.
    Sitedeki kural da bu.

    SAYFALAMA YOK. Listeler kisa (kategori, yazar, yil) ve mobil tarafin
    filtre panelini acabilmek icin hepsini birden gormesi gerekiyor;
    sayfalama burada sadece gereksiz karmasa olurdu.

    Yalnizca GET tanimli, POST 405 doner.
    """

    def get(self, request):
        return Response(_dolu_olanlar(self.secenekler()))

    def secenekler(self):
        raise NotImplementedError


class BookFiltersView(FiltreSecenekleriView):
    """GET /api/v1/filters/books/ - kitap filtrelerinin secenekleri.

    Anahtarlar /api/v1/books/ ucunun SORGU PARAMETRE ADLARIYLA birebir ayni:
    buradan alinan value, oraya aynen gonderilebilir.
    """

    def secenekler(self):
        taban = published_books()
        return {
            'year': _yil_secenekleri(taban, 'release_year'),
            'read_year': _yil_secenekleri(taban, 'read_at', tarih_alani=True),
            'author': _iliski_secenekleri(taban, 'authors'),
            'translator': _iliski_secenekleri(taban, 'translators'),
            'publisher': _iliski_secenekleri(taban, 'publisher'),
            'genre': _iliski_secenekleri(taban, 'genres'),
            'rating': _puan_secenekleri(taban),
        }


class MovieFiltersView(FiltreSecenekleriView):
    """GET /api/v1/filters/movies/ - film/dizi filtrelerinin secenekleri."""

    def secenekler(self):
        taban = published_reviews()
        return {
            'year': _yil_secenekleri(taban, 'release_year'),
            'watched_year': _yil_secenekleri(taban, 'watched_at', tarih_alani=True),
            'director': _iliski_secenekleri(taban, 'directors'),
            'screenwriter': _iliski_secenekleri(taban, 'screenwriters'),
            'actor': _iliski_secenekleri(taban, 'actors'),
            'genre': _iliski_secenekleri(taban, 'genres'),
            'rating': _puan_secenekleri(taban),
            'content_type': _content_type_secenekleri(taban),
        }


class BlogFiltersView(FiltreSecenekleriView):
    """GET /api/v1/filters/blog/ - blog filtrelerinin secenekleri.

    prefetch_related(None): published_posts() sections'i prefetch'liyor ama
    burada .values() ile gruplama yapiyoruz, nesne kurulmuyor — prefetch
    bosa calisirdi. None lookup'lari temizliyor.
    """

    def secenekler(self):
        taban = published_posts().prefetch_related(None)
        return {'category': _iliski_secenekleri(taban, 'category')}


class PhotoFiltersView(FiltreSecenekleriView):
    """GET /api/v1/filters/photos/ - galeri filtrelerinin secenekleri."""

    def secenekler(self):
        return {'category': _iliski_secenekleri(published_photos(), 'category')}
