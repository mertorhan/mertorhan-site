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
    """GET /api/v1/movies/ - yayindaki film ve dizi incelemeleri."""

    serializer_class = ReviewSerializer
    pagination_class = BlogPostPagination

    def get_queryset(self):
        return published_reviews()


class ReviewDetailView(generics.RetrieveAPIView):
    """GET /api/v1/movies/<slug>/ - tek inceleme, govde ve kunyesiyle."""

    serializer_class = ReviewDetailSerializer
    lookup_field = 'slug'

    def get_queryset(self):
        return published_reviews().prefetch_related(
            'directors', 'screenwriters', 'actors', 'genres'
        )


class BookListView(generics.ListAPIView):
    """GET /api/v1/books/ - yayindaki kitaplar."""

    serializer_class = BookSerializer
    pagination_class = BlogPostPagination

    def get_queryset(self):
        return published_books()


class BookDetailView(generics.RetrieveAPIView):
    """GET /api/v1/books/<slug>/ - tek kitap, govde ve alintilariyla."""

    serializer_class = BookDetailSerializer
    lookup_field = 'slug'

    def get_queryset(self):
        return published_books().prefetch_related('quotes')


class PhotoListView(generics.ListAPIView):
    """GET /api/v1/photos/ - yayindaki fotograflar.

    Detay ucu yok: Photo'da slug alani bulunmuyor ve tum kunye bilgisi
    zaten liste kaydinda donuyor.
    """

    serializer_class = PhotoSerializer
    pagination_class = BlogPostPagination

    def get_queryset(self):
        return published_photos()
