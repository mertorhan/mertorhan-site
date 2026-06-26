from django.shortcuts import render
from .models import Photo


def photo_list(request):
    photos = Photo.objects.filter(is_published=True)

    # Kategori filtresi (Blog'daki ?kategori=... deseni)
    selected = request.GET.get("kategori", "")
    if selected:
        photos = photos.filter(category=selected)

    return render(request, "gallery/photo_list.html", {
        "photos": photos,
        "selected": selected,
    })