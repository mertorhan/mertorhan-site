from django.db import models


class Photo(models.Model):
    CATEGORY_CHOICES = [
        ("Manzara", "Manzara"),
        ("Sokak", "Sokak"),
        ("Portre", "Portre"),
    ]

    image = models.ImageField("Fotoğraf", upload_to="gallery/")
    title = models.CharField("Başlık", max_length=200)
    category = models.CharField("Kategori", max_length=20, choices=CATEGORY_CHOICES, blank=True, default="")
    location = models.CharField("Konum", max_length=120, blank=True, default="")
    taken_at = models.DateField("Çekim tarihi", null=True, blank=True)

    # EXIF bilgileri (hepsi opsiyonel, serbest metin)
    camera = models.CharField("Kamera", max_length=100, blank=True, default="")
    lens = models.CharField("Lens", max_length=100, blank=True, default="")
    iso = models.CharField("ISO", max_length=20, blank=True, default="")
    shutter_speed = models.CharField("Enstantane", max_length=20, blank=True, default="")
    aperture = models.CharField("Diyafram", max_length=20, blank=True, default="")
    focal_length = models.CharField("Odak", max_length=20, blank=True, default="")

    is_published = models.BooleanField("Yayında", default=True)
    created_at = models.DateField("Eklenme tarihi", auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Fotoğraf"
        verbose_name_plural = "Fotoğraflar"

    def __str__(self):
        return self.title