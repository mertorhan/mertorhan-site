import os

from django.conf import settings
from django.db import models

from .imaging import kucult, kucuk_kopya_uret


class Photo(models.Model):
    CATEGORY_CHOICES = [
        ("Manzara", "Manzara"),
        ("Sokak", "Sokak"),
        ("Portre", "Portre"),
    ]

    image = models.ImageField("Fotoğraf", upload_to="gallery/")

    # Izgarada gosterilen kucuk kopya. Otomatik uretilir,
    # editable=False oldugu icin admin formunda gorunmez.
    thumbnail = models.ImageField(
        "Küçük kopya",
        upload_to="gallery/thumbs/",
        blank=True,
        null=True,
        editable=False,
    )

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

        # ONEMLI: sadece baslik/EXIF duzenlendiyse dosyaya DOKUNMUYORUZ.
        # Yoksa her kayitta JPEG yeniden sikisir ve kalite yavas yavas erir.
        islem_gerekli = yeni_kayit or gorsel_degisti or not self.thumbnail
        if not islem_gerekli:
            return

        # 1) Buyuk gorseli kucult (yerinde)
        yeni_yol = kucult(self.image.path)
        yeni_ad = os.path.relpath(yeni_yol, settings.MEDIA_ROOT).replace("\\", "/")

        # 2) Kucuk kopyayi uret
        kucuk_ad = "gallery/thumbs/" + os.path.basename(yeni_yol)
        kucuk_kopya_uret(yeni_yol, os.path.join(settings.MEDIA_ROOT, kucuk_ad))

        # 3) Alanlari guncelle ve SADECE bu iki alani kaydet
        self.image.name = yeni_ad
        self.thumbnail.name = kucuk_ad
        self._acilistaki_gorsel = yeni_ad

        super().save(update_fields=["image", "thumbnail"])

    def __str__(self):
        return self.title