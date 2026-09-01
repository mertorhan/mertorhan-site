from django.shortcuts import render, redirect
from blog.models import BlogPost
from guide.models import Guide
from gallery.models import Photo
from movies.models import Review
from books.models import Book
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

    # Ana sayfa vitrini: dort turden de isaretli olanlar yarisir, en guncel
    # olan kazanir. Eskiden hero HER ZAMAN bir geziydi (KB-88).
    #
    # BU LISTENIN SIRASI AYNI ZAMANDA ESITLIK KURALIDIR.
    # published_at bir DateField (saat yok), ustelik Guide/Review/Book'ta
    # auto_now_add — ayni gun iki tur isaretli olmasi olagan.
    #
    # SIRALAMA IKI ASAMALI:
    #   1. Once published_at — yeni olan onde.
    #   2. Tarihler ESITSE bu listenin sirasi belirler:
    #      Blog > Gezi > Film > Kitap.
    # Yani "Blog hep kazanir" DEGIL; sadece tarih esitliginde
    # oncelikli. Python'un sort'u kararli oldugu icin 2. asama
    # ek kod gerektirmiyor. reverse=True esitlerin sirasini
    # tersine CEVIRMEZ (olculdu).
    # Sirayi degistirmek isteyen bu listeye baksin.
    adaylar = []
    for model, url_adi, etiket in (
        (BlogPost, "post_detail", "Blog"),
        (Guide, "guide_detail", None),          # etiket asagida entry_type'tan
        (Review, "review_detail", "Film & Dizi"),
        (Book, "book_detail", "Kitap"),
    ):
        # Her turden SADECE en yenisi yarisa girer: ordering zaten
        # -published_at, o yuzden .first() en guncel isaretliyi verir.
        # Dort ayri sorgu cunku dort ayri tablo tek sorguda birlestirilemez.
        nesne = model.objects.filter(is_hero=True, is_published=True).first()
        # slug bos olan icerik vitrine cikmaz: {% url %} NoReverseMatch
        # firlatir ve ana sayfa komple patlardi. Dort modelde de slug
        # null=True/blank=True, yani bos slug mumkun.
        if nesne and nesne.slug:
            adaylar.append((nesne, url_adi, etiket))

    # Siralama Python tarafinda: dort ayri tablonun sonucu veritabaninda
    # tek ORDER BY ile siralanamaz.
    adaylar.sort(key=lambda aday: aday[0].published_at, reverse=True)

    if adaylar:
        hero, hero_url_adi, hero_etiket = adaylar[0]
        # Guide'in etiketi sabit degil: "Tek Mekan" / "Cok Durakli Rota".
        if hero_etiket is None:
            hero_etiket = hero.get_entry_type_display()
    else:
        hero = hero_url_adi = hero_etiket = None

    # Öne çıkan film/dizi incelemeleri (yoksa en yeni)
    reviews = Review.objects.filter(is_published=True, is_featured=True)[:3]
    if not reviews:
        reviews = Review.objects.filter(is_published=True)[:3]

    # Öne çıkan kitaplar (yoksa en yeni)
    books = Book.objects.filter(is_published=True, is_featured=True)[:3]
    if not books:
        books = Book.objects.filter(is_published=True)[:3]

    # Ana sayfa galeri şeridi için son fotoğraflar
    gallery_photos = Photo.objects.filter(is_published=True)[:4]

    # Profil (tek kayıt) — fotoğraf vb. için
    profile = Profile.objects.first()

    return render(request, "core/home.html", {
        "posts": posts,
        "guides": guides,
        "hero": hero,
        "hero_url_adi": hero_url_adi,
        "hero_etiket": hero_etiket,
        "reviews": reviews,
        "books": books,
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