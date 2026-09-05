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
]
