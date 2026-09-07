from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


# --------------------------------------------------------------------
# Kunye listeleri
#
# Bu uc model core'da DEGIL books'ta yasiyor. Ayni gerekce movies icin de
# gecerli (movies/models.py'nin ilk yorum blogu): kitap turleri (Roman,
# Deneme) film turleriyle AYNI LISTE OLMAMALI. Bu yuzden asagidaki Genre
# books'a ait, movies.Genre ile paylasilmiyor — movies'ten import yok.
# RatingCriterion core'a girdi cunku iki bolum gercekten ayni kriter
# listesini paylasiyordu; burada paylasmiyorlar.
# --------------------------------------------------------------------

class Author(models.Model):
    name = models.CharField("Ad", max_length=200, unique=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Yazar"
        verbose_name_plural = "Yazarlar"

    def __str__(self):
        return self.name


class Publisher(models.Model):
    name = models.CharField("Ad", max_length=200, unique=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Yayınevi"
        verbose_name_plural = "Yayınevleri"

    def __str__(self):
        return self.name


class Genre(models.Model):
    name = models.CharField("Ad", max_length=200, unique=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Kitap türü"
        verbose_name_plural = "Kitap türleri"

    def __str__(self):
        return self.name


class Book(models.Model):
    # --- Kimlik ---
    title = models.CharField("Kitap adı", max_length=200)
    slug = models.SlugField("Adres (slug)", max_length=80, unique=True, null=True, blank=True)
    cover_image = models.ImageField("Kapak", upload_to="books/", blank=True, null=True)

    # --- Künye ---
    author = models.CharField("Yazar", max_length=200)
    translator = models.CharField("Çevirmen", max_length=200, blank=True, default="")
    # published_at ile KARISTIRILMASIN: o auto_now_add, kaydin siteye
    # eklendigi tarih. release_year kitabin basim yili.
    release_year = models.PositiveIntegerField("Basım yılı", null=True, blank=True)

    # --- Künye: çoklu ilişkiler (KB-107) ---
    # Yukaridaki author metin alani BILEREK duruyor (movies'teki KB-32
    # sirasinin aynisi): once bu iliskiler kuruluyor, sonra veri admin'den
    # elle giriliyor, eski alan EN SON ayri bir kartta siliniyor. Sira ters
    # cevrilemez — API ve mobil uygulama su an author'a bagli.
    #
    # related_name verilmedi: varsayilan book_set yeterli, filtre sorgulari
    # Book uzerinden ileri yonde calisacak.
    authors = models.ManyToManyField(Author, blank=True, verbose_name="Yazarlar")
    genres = models.ManyToManyField(Genre, blank=True, verbose_name="Türler")
    # PROTECT: kullanimda olan bir yayinevi silinirse kitaplar sessizce
    # yayinevsiz kalirdi. (BookScore.criterion ile ayni gerekce.)
    publisher = models.ForeignKey(
        Publisher,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name="Yayınevi",
    )

    # movies.Review.watched_at'in kitap karsiligi; yayin tarihi
    # (published_at) ile karistirilmasin — bu, kitabin okundugu tarih.
    read_at = models.DateField("Okuma tarihi", null=True, blank=True)

    # --- Senin değerlendirmen ---
    # rating artik elle girilmiyor: alt kriter puanlarinin ortalamasi.
    # Hesap ScoreAverageMixin.save_related() icinde yapiliyor (KB-42).
    # Alan adi bilerek degismedi, sablonlar buna bagli.
    rating = models.DecimalField(
        "Ortalama puan (otomatik)", max_digits=3, decimal_places=1, null=True, blank=True
    )
    summary = models.TextField("Kart özeti", blank=True, default="")
    body = models.TextField("Özet / Eleştiri")

    # --- Yayın durumu ---
    is_featured = models.BooleanField("Öne çıkan", default=False)
    # is_featured bolum ici one cikaniligi, is_hero ana sayfa vitrinini
    # belirler; ikisi ayri islere bakar.
    is_hero = models.BooleanField("Ana sayfa vitrininde göster", default=False)
    is_published = models.BooleanField("Yayında", default=True)
    published_at = models.DateField("Yayın tarihi", auto_now_add=True)

    class Meta:
        ordering = ["-published_at"]
        verbose_name = "Kitap"
        verbose_name_plural = "Kitaplar"

    def __str__(self):
        return self.title


class BookScore(models.Model):
    """
    Bir kitabin TEK bir kriterden aldigi puan.
    Book.rating bu satirlarin ortalamasi. (movies.ReviewScore'un esi.)
    """
    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        # related_name "scores" olmak ZORUNDA: ScoreAverageMixin
        # ortalamayi bu ad uzerinden hesapliyor.
        related_name="scores",
        verbose_name="Kitap",
    )
    # PROTECT: kullanimda olan bir kriter silinirse puanlar sessizce
    # yok olur ve ortalamalar aciklanamaz sekilde degisirdi.
    criterion = models.ForeignKey(
        "core.RatingCriterion",
        on_delete=models.PROTECT,
        verbose_name="Kriter",
    )
    # Olcek 1-10; sinirlar burada tanimli. Eskiden puanin tek kurali
    # "negatif olamaz"di, admin'e 47 girilebiliyordu.
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
                fields=["book", "criterion"], name="unique_book_criterion"
            )
        ]
        verbose_name = "Kriter Puanı"
        verbose_name_plural = "Kriter Puanları"

    def __str__(self):
        return f"{self.criterion} — {self.value if self.value is not None else '—'}"


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