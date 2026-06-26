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
    pullquote = models.CharField("Vurgulu alıntı", max_length=300, blank=True, default="")
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