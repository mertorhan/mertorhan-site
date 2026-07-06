from django.db import models


class Book(models.Model):
    # --- Kimlik ---
    title = models.CharField("Kitap adı", max_length=200)
    slug = models.SlugField("Adres (slug)", max_length=80, unique=True, null=True, blank=True)
    cover_image = models.ImageField("Kapak", upload_to="books/", blank=True, null=True)

    # --- Künye ---
    author = models.CharField("Yazar", max_length=200)
    translator = models.CharField("Çevirmen", max_length=200, blank=True, default="")

    # --- Senin değerlendirmen ---
    rating = models.PositiveIntegerField("Puanım (1-10)", null=True, blank=True)
    summary = models.TextField("Kart özeti", blank=True, default="")
    body = models.TextField("Özet / Eleştiri")

    # --- Yayın durumu ---
    is_featured = models.BooleanField("Öne çıkan", default=False)
    is_published = models.BooleanField("Yayında", default=True)
    published_at = models.DateField("Yayın tarihi", auto_now_add=True)

    class Meta:
        ordering = ["-published_at"]
        verbose_name = "Kitap"
        verbose_name_plural = "Kitaplar"

    def __str__(self):
        return self.title


class BookQuote(models.Model):
    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        related_name="quotes",
        verbose_name="Kitap",
    )
    order = models.PositiveIntegerField("Sıra", default=1)
    text = models.TextField("Alıntı")
    page = models.CharField("Sayfa (ops.)", max_length=20, blank=True, default="")

    class Meta:
        ordering = ["order"]
        verbose_name = "Alıntı"
        verbose_name_plural = "Alıntılar"

    def __str__(self):
        return f"{self.order}. alıntı — {self.book.title}"