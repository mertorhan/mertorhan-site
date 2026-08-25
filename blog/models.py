from django.db import models


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
    published_at = models.DateField("Yayın tarihi", auto_now_add=True)

    class Meta:
        ordering = ["-published_at"]
        verbose_name = "Blog Yazısı"
        verbose_name_plural = "Blog Yazıları"

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

    def __str__(self):
        return f"{self.order} · {self.get_kind_display()}"