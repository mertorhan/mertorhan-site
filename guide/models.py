from django.db import models


class Guide(models.Model):
    # --- Sabit seçenekler (admin'de açılır menü olur) ---
    ENTRY_TYPE_CHOICES = [
        ("mekan", "Tek Mekan"),
        ("rota", "Çok Duraklı Rota"),
    ]
    BUDGET_CHOICES = [
        ("₺", "₺ — Ekonomik"),
        ("₺₺", "₺₺ — Orta"),
        ("₺₺₺", "₺₺₺ — Yüksek"),
    ]
    BEST_TIME_CHOICES = [
        ("ilkbahar", "İlkbahar"),
        ("yaz", "Yaz"),
        ("sonbahar", "Sonbahar"),
        ("kis", "Kış"),
        ("tum-yil", "Tüm Yıl"),
    ]
    SUITABLE_FOR_CHOICES = [
        ("cift", "Çiftler"),
        ("aile", "Ailecek"),
        ("solo", "Tek Başına"),
        ("arkadas", "Arkadaş Grubu"),
        ("herkes", "Herkese Uygun"),
    ]

    # --- Temel kimlik ---
    title = models.CharField("Başlık", max_length=200)
    slug = models.SlugField("Adres (slug)", max_length=80, unique=True, null=True, blank=True)
    entry_type = models.CharField("Tür", max_length=10, choices=ENTRY_TYPE_CHOICES, default="rota")

    # --- Görsel + tanıtım metinleri ---
    cover_image = models.ImageField("Kapak görseli", upload_to="guide/", blank=True, null=True)
    highlight = models.CharField("Vurucu cümle (hero)", max_length=200, blank=True, default="")
    summary = models.TextField("Kart özeti", blank=True, default="")
    overview = models.TextField("Genel bakış / editör notu", blank=True, default="")

    # --- "Bir Bakışta" + filtre alanları ---
    city = models.CharField("Şehir", max_length=80, blank=True, default="")
    budget = models.CharField("Bütçe", max_length=6, choices=BUDGET_CHOICES, blank=True, default="")
    best_time = models.CharField("En iyi zaman", max_length=20, choices=BEST_TIME_CHOICES, blank=True, default="")
    suitable_for = models.CharField("Kime uygun", max_length=20, choices=SUITABLE_FOR_CHOICES, blank=True, default="")
    duration = models.CharField("Süre", max_length=50, blank=True, default="")

    # --- Detay sayfası ek bölümleri (opsiyonel) ---
    verdict = models.TextField("Dürüst değerlendirme", blank=True, default="")
    practical_info = models.TextField("Pratik bilgi", blank=True, default="")
    # --- Harita (tek mekan girişleri için; rotalarda duraklar kullanılır) ---
    latitude = models.DecimalField("Enlem", max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField("Boylam", max_digits=9, decimal_places=6, null=True, blank=True)

    # --- Yayın durumu ---
    is_featured = models.BooleanField("Öne çıkan", default=False)
    is_published = models.BooleanField("Yayında", default=True)
    published_at = models.DateField("Yayın tarihi", auto_now_add=True)

    class Meta:
        ordering = ["-published_at"]
        verbose_name = "Gezi / Öneri"
        verbose_name_plural = "Gezi / Öneriler"

    def __str__(self):
        return self.title


class GuideStop(models.Model):
    POINT_TYPE_CHOICES = [
        ("gezilecek", "Gezilecek Yer"),
        ("yeme-icme", "Yeme-İçme"),
        ("ogrenme", "Öğrenme"),
        ("konaklama", "Konaklama"),
        ("deneyim", "Deneyim"),
    ]

    guide = models.ForeignKey(
        Guide,
        on_delete=models.CASCADE,
        related_name="stops",
        verbose_name="Bağlı gezi",
    )
    order = models.PositiveIntegerField("Sıra", default=1)
    name = models.CharField("Durak adı", max_length=200)
    point_type = models.CharField("Durak türü", max_length=12, choices=POINT_TYPE_CHOICES, default="gezilecek")
    description = models.TextField("Açıklama", blank=True, default="")
    hours = models.CharField("Önerilen saat", max_length=80, blank=True, default="")
    cost = models.CharField("Yaklaşık ücret", max_length=80, blank=True, default="")
    # --- Harita ---
    latitude = models.DecimalField("Enlem", max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField("Boylam", max_digits=9, decimal_places=6, null=True, blank=True)

    class Meta:
        ordering = ["order"]
        verbose_name = "Gezi Durağı"
        verbose_name_plural = "Gezi Durakları"

    def __str__(self):
        return f"{self.order}. {self.name}"