from django.db.models import Q
from rest_framework import generics
from rest_framework.pagination import PageNumberPagination

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


class BlogPostListView(generics.ListAPIView):
    """GET /api/v1/blog/ - yayindaki yazilarin listesi.

    ListAPIView yalnizca GET tanimlar; POST 405 doner.
    """

    serializer_class = BlogPostSerializer
    pagination_class = BlogPostPagination

    def get_queryset(self):
        return published_posts()


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

    Detay ucu yok: Photo'da slug alani bulunmuyor ve tum kunye bilgisi
    zaten liste kaydinda donuyor.
    """

    serializer_class = PhotoSerializer
    pagination_class = BlogPostPagination

    def get_queryset(self):
        return published_photos()
