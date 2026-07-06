from django.db import models


class Review(models.Model):
    CONTENT_TYPE_CHOICES = [
        ("film", "Film"),
        ("dizi", "Dizi"),
    ]

    # --- Kimlik ---
    title = models.CharField("Ad", max_length=200)
    slug = models.SlugField("Adres (slug)", max_length=80, unique=True, null=True, blank=True)
    content_type = models.CharField("Tür", max_length=5, choices=CONTENT_TYPE_CHOICES, default="film")
    cover_image = models.ImageField("Kapak / Afiş", upload_to="movies/", blank=True, null=True)

    # --- Künye ---
    director = models.CharField("Yönetmen", max_length=200, blank=True, default="")
    screenwriter = models.CharField("Senarist", max_length=200, blank=True, default="")
    lead_actors = models.CharField("Başrol oyuncuları", max_length=300, blank=True, default="")
    release_year = models.PositiveIntegerField("Yapım yılı", null=True, blank=True)
    genre = models.CharField("Tarz (örn: Bilim Kurgu)", max_length=100, blank=True, default="")

    # --- Senin değerlendirmen ---
    rating = models.PositiveIntegerField("Puanım (1-10)", null=True, blank=True)
    summary = models.TextField("Kart özeti", blank=True, default="")
    body = models.TextField("Yorum / İnceleme")

    # --- Yayın durumu (diğer app'lerdeki kalıpla aynı) ---
    is_featured = models.BooleanField("Öne çıkan", default=False)
    is_published = models.BooleanField("Yayında", default=True)
    published_at = models.DateField("Yayın tarihi", auto_now_add=True)

    class Meta:
        ordering = ["-published_at"]
        verbose_name = "Film / Dizi İncelemesi"
        verbose_name_plural = "Film / Dizi İncelemeleri"

    def __str__(self):
        return self.title