from django.urls import path

from . import views

# app_name zorunlu: blog/urls.py'de namespace yok ve "post_list"/"post_detail"
# isimleri global. Namespace olmasa API rotasi blog'dan sonra geldigi icin
# reverse() API adresini dondurur, mevcut sablon linkleri bozulurdu.
app_name = "api"

urlpatterns = [
    path("blog/", views.BlogPostListView.as_view(), name="blog_list"),
    path("blog/<slug:slug>/", views.BlogPostDetailView.as_view(), name="blog_detail"),
    path("movies/", views.ReviewListView.as_view(), name="movie_list"),
    path("movies/<slug:slug>/", views.ReviewDetailView.as_view(), name="movie_detail"),
    path("books/", views.BookListView.as_view(), name="book_list"),
    path("books/<slug:slug>/", views.BookDetailView.as_view(), name="book_detail"),
    path("photos/", views.PhotoListView.as_view(), name="photo_list"),

    # Filtre secenekleri. Onek AYRI ("filters/books/"), bilerek:
    # "books/filters/" yazsaydik yukaridaki "books/<slug:slug>/" desenine
    # girerdi ve slug'i "filters" olan bir kitap sonsuza dek erisilemez
    # olurdu. Onek ayri oldugu icin boyle bir cakisma imkansiz.
    path("filters/books/", views.BookFiltersView.as_view(), name="book_filters"),
    path("filters/movies/", views.MovieFiltersView.as_view(), name="movie_filters"),
    path("filters/blog/", views.BlogFiltersView.as_view(), name="blog_filters"),
    path("filters/photos/", views.PhotoFiltersView.as_view(), name="photo_filters"),
]
