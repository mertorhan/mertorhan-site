from django.shortcuts import render, get_object_or_404
from .models import Book


def book_list(request):
    books = Book.objects.filter(is_published=True)

    # Öne çıkan kart: önce işaretli olan; yoksa en yeni
    featured = books.filter(is_featured=True).first() or books.first()
    others = books.exclude(pk=featured.pk) if featured else books

    return render(request, "books/book_list.html", {
        "featured": featured,
        "books": others,
    })


def book_detail(request, slug):
    book = get_object_or_404(Book, slug=slug, is_published=True)
    return render(request, "books/book_detail.html", {"book": book})