from rest_framework import generics
from rest_framework.pagination import PageNumberPagination

from blog.models import BlogPost
from .serializers import BlogPostSerializer, BlogPostDetailSerializer


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
