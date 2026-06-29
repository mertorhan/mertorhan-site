from django.db import models


class Profile(models.Model):
    # --- Kimlik ---
    full_name = models.CharField("Ad Soyad", max_length=120, default="Mert Orhan")
    role = models.CharField("Unvan", max_length=160, blank=True, default="")
    tagline = models.CharField("Ana sayfa sloganı", max_length=200, blank=True, default="")
    photo = models.ImageField("Profil fotoğrafı", upload_to="profile/", blank=True, null=True)

    # --- Hakkında metni ---
    about_title = models.CharField("Hakkında başlığı", max_length=200, blank=True, default="")
    bio = models.TextField("Biyografi", blank=True, default="")

    # --- İletişim / bağlantılar ---
    linkedin_url = models.URLField("LinkedIn adresi", blank=True, default="")
    email = models.EmailField("E-posta", blank=True, default="")
    cv = models.FileField("CV (PDF)", upload_to="cv/", blank=True, null=True)

    class Meta:
        verbose_name = "Profil"
        verbose_name_plural = "Profil"

    def __str__(self):
        return self.full_name


class Experience(models.Model):
    profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name="experiences",
        verbose_name="Profil",
    )
    order = models.PositiveIntegerField("Sıra", default=1)
    date_range = models.CharField("Tarih aralığı", max_length=80)     # örn: "2022 — Bugün"
    role = models.CharField("Pozisyon · Şirket", max_length=200)
    description = models.TextField("Açıklama", blank=True, default="")

    class Meta:
        ordering = ["order"]
        verbose_name = "Deneyim"
        verbose_name_plural = "Deneyimler"

    def __str__(self):
        return self.role
    

class ContactMessage(models.Model):
    name = models.CharField("Ad Soyad", max_length=120)
    email = models.EmailField("E-posta")
    message = models.TextField("Mesaj")
    created_at = models.DateTimeField("Gönderilme tarihi", auto_now_add=True)
    is_read = models.BooleanField("Okundu", default=False)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "İletişim Mesajı"
        verbose_name_plural = "İletişim Mesajları"

    def __str__(self):
        return f"{self.name} — {self.created_at:%d.%m.%Y %H:%M}"