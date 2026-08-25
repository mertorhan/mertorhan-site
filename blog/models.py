import os
from datetime import date

from django.conf import settings
from django.db import models

from gallery.imaging import kucult

# Blog gorselleri icin uzun kenar.
# Galeri 2000px kullaniyor cunku oradaki foto lightbox'ta tam ekran aciliyor.
# Blog gorseli 680px okuma kolonunu hicbir zaman asmiyor; 1400 Retina icin
# fazlasiyla yeterli ve dosya boyutunu ciddi dusurur.
BLOG_IMAGE_LONG_EDGE = 1400


class Category(models.Model):
    name = models.CharField("Ad", max_length=50, unique=True)

    class Meta:
        verbose_name = "Kategori"
        verbose_name_plural = "Kategoriler"

    def __str__(self):
        return self.name


class BlogPost(models.Model):
    title = models.CharField("Başlık", max_length=200)
    slug = models.SlugField("Adres (slug)", max_length=60, unique=True, null=True, blank=True)
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="posts",
        verbose_name="Kategori",
    )
    summary = models.TextField("Özet", blank=True, default="")
    body = models.TextField("İçerik")
    # CharField -> TextField: admin'de artik cok satirli kutu cikar (siir, dize vb.)
    pullquote = models.TextField("Vurgulu alıntı", blank=True, default="")
    cover_image = models.ImageField("Kapak görseli", upload_to="blog/", blank=True, null=True)
    reading_time = models.PositiveIntegerField("Okuma süresi (dk)", default=1)
    is_featured = models.BooleanField("Öne çıkan", default=False)
    is_published = models.BooleanField("Yayında", default=True)
    # default=date.today PARANTEZSIZ: date.today() yazilsaydi deger sunucu
    # baslangicinda bir kez hesaplanir ve donardi (her yeni yazi o gune damgalanirdi).
    # auto_now_add kaldirildi cunku alani editable=False yapiyor, yani admin
    # formunda hic gorunmuyordu — geriye donuk tarih girilemiyordu.
    published_at = models.DateField("Yayın tarihi", default=date.today)

    class Meta:
        ordering = ["-published_at"]
        verbose_name = "Blog Yazısı"
        verbose_name_plural = "Blog Yazıları"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Kayittan sonra "kapak degisti mi?" diyebilmek icin ilk hali akilda tutulur
        self._acilistaki_kapak = self.cover_image.name if self.cover_image else ""

    def save(self, *args, **kwargs):
        yeni_kayit = self.pk is None
        kapak_degisti = (self.cover_image.name or "") != (self._acilistaki_kapak or "")

        # Once normal kayit: dosya diske yazilsin ki uzerinde calisabilelim
        super().save(*args, **kwargs)

        if not self.cover_image:
            return

        # ONEMLI: sadece baslik/govde duzenlendiyse dosyaya DOKUNMUYORUZ.
        # Yoksa her kayitta JPEG yeniden sikisir ve kalite yavas yavas erir.
        if not (yeni_kayit or kapak_degisti):
            return

        yeni_yol = kucult(self.cover_image.path, max_kenar=BLOG_IMAGE_LONG_EDGE)
        yeni_ad = os.path.relpath(yeni_yol, settings.MEDIA_ROOT).replace("\\", "/")

        self.cover_image.name = yeni_ad
        self._acilistaki_kapak = yeni_ad

        super().save(update_fields=["cover_image"])

    def __str__(self):
        return self.title


class PostSection(models.Model):
    """Bir yazinin govdesini olusturan sirali bloklar.

    Yazinin iskeleti bloklardan kurulur; paragraf ve alinti bloklarinin ICI
    ileride markdown olarak islenecek (ayri kart).
    """

    KIND_CHOICES = [
        ("paragraph", "Paragraf"),
        ("heading", "Başlık"),
        ("image", "Görsel"),
        ("quote", "Alıntı"),
        ("embed", "Gömü"),
    ]
    HEADING_LEVEL_CHOICES = [
        ("h2", "Ana başlık"),
        ("h3", "Alt başlık"),
    ]

    post = models.ForeignKey(
        BlogPost,
        on_delete=models.CASCADE,
        related_name="sections",
        verbose_name="Bağlı yazı",
    )
    order = models.PositiveIntegerField("Sıra", default=0)
    kind = models.CharField("Blok türü", max_length=20, choices=KIND_CHOICES, default="paragraph")

    # --- paragraph / heading / quote ortak govdesi ---
    text = models.TextField("Metin", blank=True, default="")

    # --- sadece heading ---
    heading_level = models.CharField(
        "Başlık düzeyi", max_length=2, choices=HEADING_LEVEL_CHOICES, blank=True, default=""
    )
    # Secmeli: bazi basliklar sadece yazi icinde durur, icindekiler listesine girmez.
    in_toc = models.BooleanField("İçindekiler listesinde göster", default=False)

    # --- sadece image ---
    image = models.ImageField("Görsel", upload_to="blog/sections/", blank=True, null=True)
    image_title = models.CharField("Görsel başlığı (üstte)", max_length=200, blank=True, default="")
    image_caption = models.CharField("Görsel etiketi (altta)", max_length=300, blank=True, default="")
    image_alt = models.CharField("Alt metin (erişilebilirlik)", max_length=200, blank=True, default="")

    # --- sadece quote ---
    quote_source = models.CharField("Alıntının kaynağı", max_length=200, blank=True, default="")

    # --- sadece embed ---
    embed_url = models.URLField("Gömü bağlantısı", blank=True, default="")

    class Meta:
        # id ikinci anahtar: ayni order'a sahip iki blokta sira rastgele olmasin.
        ordering = ["order", "id"]
        verbose_name = "Bölüm"
        verbose_name_plural = "Bölümler"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Kayittan sonra "gorsel degisti mi?" diyebilmek icin ilk hali akilda tutulur
        self._acilistaki_gorsel = self.image.name if self.image else ""

    def save(self, *args, **kwargs):
        yeni_kayit = self.pk is None
        gorsel_degisti = (self.image.name or "") != (self._acilistaki_gorsel or "")

        # Once normal kayit: dosya diske yazilsin ki uzerinde calisabilelim
        super().save(*args, **kwargs)

        if not self.image:
            return

        # ONEMLI: sadece metin duzenlendiyse dosyaya DOKUNMUYORUZ.
        # Yoksa her kayitta JPEG yeniden sikisir ve kalite yavas yavas erir.
        if not (yeni_kayit or gorsel_degisti):
            return

        yeni_yol = kucult(self.image.path, max_kenar=BLOG_IMAGE_LONG_EDGE)
        yeni_ad = os.path.relpath(yeni_yol, settings.MEDIA_ROOT).replace("\\", "/")

        self.image.name = yeni_ad
        self._acilistaki_gorsel = yeni_ad

        super().save(update_fields=["image"])

    def __str__(self):
        return f"{self.order} · {self.get_kind_display()}"