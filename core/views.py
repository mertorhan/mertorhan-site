from django.shortcuts import render, redirect
from blog.models import BlogPost
from guide.models import Guide
from gallery.models import Photo
from .models import Profile
from .forms import ContactForm


def home(request):
    # Öne çıkan yazılar (yoksa en yeni)
    posts = BlogPost.objects.filter(is_published=True, is_featured=True)[:3]
    if not posts:
        posts = BlogPost.objects.filter(is_published=True)[:3]

    # Öne çıkan rotalar (yoksa en yeni)
    guides = Guide.objects.filter(is_published=True, is_featured=True)[:3]
    if not guides:
        guides = Guide.objects.filter(is_published=True)[:3]

    # Hero için tek bir öne çıkan gezi
    hero_guide = guides[0] if guides else None

    # Ana sayfa galeri şeridi için son fotoğraflar (Blok 3'te kullanılacak)
    gallery_photos = Photo.objects.filter(is_published=True)[:4]

    # Profil (tek kayıt) — fotoğraf vb. için
    profile = Profile.objects.first()

    return render(request, "core/home.html", {
        "posts": posts,
        "guides": guides,
        "hero_guide": hero_guide,
        "gallery_photos": gallery_photos,
        "profile": profile,
    })


def about(request):
    # Hakkında sayfası tek Profil kaydından beslenir
    profile = Profile.objects.first()

    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()                       # mesajı veritabanına kaydet
            # PRG: kaydettikten sonra temiz bir sayfaya yönlendir.
            # ?sent=1 -> yönlendirilen sayfada pop-up göstermek için işaret
            return redirect("/hakkinda/?sent=1")
        # form geçersizse: asagiya dusup hatalarla birlikte formu geri gosteririz
    else:
        form = ContactForm()

    # "sent" artik POST'tan degil, adresteki ?sent=1'den okunuyor
    sent = request.GET.get("sent") == "1"

    return render(request, "core/about.html", {
        "profile": profile,
        "form": form,
        "sent": sent,
    })