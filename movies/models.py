from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


# --------------------------------------------------------------------
# Kunye listeleri
#
# Bu dort model core'da DEGIL movies'te yasiyor: kitabin yazari ve turu
# ayri bir kartin isi ve kitap turleri (Roman, Deneme) film turleriyle
# AYNI LISTE OLMAMALI. RatingCriterion core'a girdi cunku iki bolum
# gercekten ayni kriter listesini paylasiyordu; burada paylasmiyorlar.
# --------------------------------------------------------------------

class Director(models.Model):
    name = models.CharField("Ad", max_length=200, unique=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Yönetmen"
        verbose_name_plural = "Yönetmenler"

    def __str__(self):
        return self.name


class Screenwriter(models.Model):
    name = models.CharField("Ad", max_length=200, unique=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Senarist"
        verbose_name_plural = "Senaristler"

    def __str__(self):
        return self.name


class Actor(models.Model):
    name = models.CharField("Ad", max_length=200, unique=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Oyuncu"
        verbose_name_plural = "Oyuncular"

    def __str__(self):
        return self.name


class Genre(models.Model):
    name = models.CharField("Ad", max_length=200, unique=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Tür"
        verbose_name_plural = "Türler"

    def __str__(self):
        return self.name


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

    # --- Künye: çoklu ilişkiler (KB-32) ---
    # Yukaridaki dort metin alani (director, screenwriter, lead_actors,
    # genre) BILEREK duruyor. Once bu iliskiler kuruluyor, sonra veri
    # admin'den elle giriliyor, eski alanlar EN SON ayri bir kartta
    # siliniyor. Sira ters cevrilemez.
    #
    # related_name verilmedi: varsayilan review_set yeterli, filtre
    # sorgulari Review uzerinden ileri yonde calisacak.
    directors = models.ManyToManyField(Director, blank=True, verbose_name="Yönetmenler")
    screenwriters = models.ManyToManyField(Screenwriter, blank=True, verbose_name="Senaristler")
    actors = models.ManyToManyField(Actor, blank=True, verbose_name="Oyuncular")
    genres = models.ManyToManyField(Genre, blank=True, verbose_name="Türler")

    # KB-31: yayin tarihi (published_at) ile karistirilmasin — bu, filmin
    # izlendigi tarih.
    watched_at = models.DateField("İzleme tarihi", null=True, blank=True)

    # --- Senin değerlendirmen ---
    # rating artik elle girilmiyor: alt kriter puanlarinin ortalamasi.
    # Hesap ReviewAdmin.save_related() icinde yapiliyor (KB-37).
    # Alan adi bilerek degismedi, sablonlar buna bagli.
    rating = models.DecimalField(
        "Ortalama puan (otomatik)", max_digits=3, decimal_places=1, null=True, blank=True
    )
    summary = models.TextField("Kart özeti", blank=True, default="")
    body = models.TextField("Yorum / İnceleme")

    # --- Yayın durumu (diğer app'lerdeki kalıpla aynı) ---
    is_featured = models.BooleanField("Öne çıkan", default=False)
    # is_featured bolum ici one cikaniligi, is_hero ana sayfa vitrinini
    # belirler; ikisi ayri islere bakar.
    is_hero = models.BooleanField("Ana sayfa vitrininde göster", default=False)
    is_published = models.BooleanField("Yayında", default=True)
    published_at = models.DateField("Yayın tarihi", auto_now_add=True)

    class Meta:
        ordering = ["-published_at"]
        verbose_name = "Film / Dizi İncelemesi"
        verbose_name_plural = "Film / Dizi İncelemeleri"

    def __str__(self):
        return self.title


class ReviewScore(models.Model):
    """
    Bir incelemenin TEK bir kriterden aldigi puan.
    Review.rating bu satirlarin ortalamasi.
    """
    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name="scores",
        verbose_name="İnceleme",
    )
    # PROTECT: kullanimda olan bir kriter silinirse puanlar sessizce
    # yok olur ve ortalamalar aciklanamaz sekilde degisirdi.
    criterion = models.ForeignKey(
        "core.RatingCriterion",
        on_delete=models.PROTECT,
        verbose_name="Kriter",
    )
    # Olcek 1-10; sinirlar burada tanimli (KB-35). Eskiden puanin tek
    # kurali "negatif olamaz"di, admin'e 47 girilebiliyordu.
    value = models.PositiveSmallIntegerField(
        "Puan (1-10)",
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
    )

    class Meta:
        ordering = ["criterion__order"]
        constraints = [
            models.UniqueConstraint(
                fields=["review", "criterion"], name="unique_review_criterion"
            )
        ]
        verbose_name = "Kriter Puanı"
        verbose_name_plural = "Kriter Puanları"

    def __str__(self):
        return f"{self.criterion} — {self.value if self.value is not None else '—'}"