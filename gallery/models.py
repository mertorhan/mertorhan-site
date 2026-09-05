import os

from django.conf import settings
from django.db import models

from .imaging import _gorseli_ac, kucult, kucuk_kopya_uret


def gorsel_olcusu(yol):
    """
    Bir gorselin EKRANDA gorunecek olcusunu dondurur: (genislik, yukseklik).

    Dosyadaki ham olcuyu DEGIL, EXIF donme bilgisi uygulanmis hâli
    veriyoruz. Kameralar dikey cekilen fotografi cogu zaman yatay
    kaydedip "bunu 90 derece dondur" notunu EXIF'e yaziyor; ham olcu
    boyle bir dosyada 6000x4000, ekranda gorunen ise 4000x6000 oluyor.

    Olcum imaging.py'deki _gorseli_ac() ile ayni yoldan gecsin ki yeni
    kayitlar ile eski kayitlari dolduran komut ayni sonucu uretsin.
    """
    with _gorseli_ac(yol) as img:
        return img.size


class PhotoCategory(models.Model):
    """
    Galeri kategorisi. Once Photo uzerinde sabit secenekli bir metin
    alaniydi; yeni kategori eklemek kod degisikligi ve migration
    gerektiriyordu. Artik admin'den yonetiliyor.
    """
    name = models.CharField("Ad", max_length=60, unique=True)
    order = models.PositiveIntegerField("Sıra", default=10)

    class Meta:
        ordering = ["order", "name"]
        verbose_name = "Fotoğraf Kategorisi"
        verbose_name_plural = "Fotoğraf Kategorileri"

    def __str__(self):
        return self.name


class Photo(models.Model):
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

    # Buyuk gorselin olcusu. Sablon bunu <img width/height> olarak basiyor;
    # tarayici oran icin yer ayirinca izgara yuklenirken ziplamiyor.
    # editable=False: elle girilmez, save() icinde olculur.
    image_width = models.PositiveIntegerField(null=True, blank=True, editable=False)
    image_height = models.PositiveIntegerField(null=True, blank=True, editable=False)

    title = models.CharField("Başlık", max_length=200)
    # SET_NULL: kategori silinirse fotograf silinmesin, kategorisiz kalsin.
    category = models.ForeignKey(
        PhotoCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Kategori",
    )
    location = models.CharField("Konum", max_length=120, blank=True, default="")
    taken_at = models.DateField("Çekim tarihi", null=True, blank=True)

    # EXIF bilgileri (hepsi opsiyonel, serbest metin)
    camera = models.CharField("Kamera", max_length=100, blank=True, default="")
    lens = models.CharField("Lens", max_length=100, blank=True, default="")
    iso = models.CharField("ISO", max_length=20, blank=True, default="")
    shutter_speed = models.CharField("Enstantane", max_length=20, blank=True, default="")
    aperture = models.CharField("Diyafram", max_length=20, blank=True, default="")
    focal_length = models.CharField("Odak", max_length=20, blank=True, default="")

    # Elle siralama. Araliklı numara ver (10, 20, 30) ki araya yeni bir
    # fotograf sokmak icin butun listeyi yeniden numaralamak gerekmesin.
    # Hepsi 0 kaldigi surece siralama bugunku gibi yeniden eskiye kalir.
    order = models.PositiveIntegerField("Sıra", default=0)

    is_published = models.BooleanField("Yayında", default=True)
    created_at = models.DateField("Eklenme tarihi", auto_now_add=True)

    class Meta:
        ordering = ["order", "-created_at"]
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

        # 3) Olcuyu KUCULTMEDEN SONRAKI dosyadan al.
        #    Once olcseydik 6000px'lik ham olcuyu yazardik; ImageField'in
        #    width_field/height_field otomatigi de tam bunu yapiyor
        #    (dosyayi yuklenen ham hâliyle, kucultmeden ONCE ve EXIF
        #    donmesini uygulamadan okuyor). O yuzden burada elle olcuyoruz.
        self.image_width, self.image_height = gorsel_olcusu(yeni_yol)

        # 4) Alanlari guncelle ve SADECE bunlari kaydet.
        #    DIKKAT: update_fields'a girmeyen alan HIC kaydedilmez —
        #    boyut alanlari bu listede olmazsa sessizce NULL kalir.
        self.image.name = yeni_ad
        self.thumbnail.name = kucuk_ad
        self._acilistaki_gorsel = yeni_ad

        super().save(update_fields=["image", "thumbnail", "image_width", "image_height"])

    def __str__(self):
        return self.title