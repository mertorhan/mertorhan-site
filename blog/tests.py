from django.test import TestCase
from django.urls import reverse

from .admin import BlogPostAdmin
from .models import BlogPost, PostSection


class PostDetailTests(TestCase):
    """KB-28: yazi govdesi sadece PostSection bloklarindan basiliyor."""

    def _yazi(self, **alanlar):
        # body hala zorunlu alan (model bu kartta degismiyor); ayirt edici
        # metin istemeyen testlerde notr bir deger yeterli.
        alanlar.setdefault("body", "notr govde")
        return BlogPost.objects.create(title="Deneme", slug="deneme", **alanlar)

    def _sayfa(self, yazi):
        yanit = self.client.get(reverse("post_detail", args=[yazi.slug]))
        self.assertEqual(yanit.status_code, 200)
        return yanit

    def _baslik(self, yazi, sira, metin, in_toc=True):
        return PostSection.objects.create(
            post=yazi, order=sira, kind="heading", heading_level="h2",
            text=metin, in_toc=in_toc,
        )

    # Isaretci metinler ASCII ve tek kelime: markdown filtresi metni <p> ile
    # sariyor, tirnak ya da Turkce karakter kacislanirsa arama yaniltirdi.

    def test_blok_metinleri_sayfada_gorunuyor(self):
        # Iddia: paragraf ve alinti bloklarinin metni detay sayfasinda basiliyor.
        yazi = self._yazi()
        PostSection.objects.create(post=yazi, order=1, kind="paragraph", text="ALFABLOK")
        PostSection.objects.create(post=yazi, order=2, kind="quote", text="BETABLOK")
        yanit = self._sayfa(yazi)
        self.assertContains(yanit, "ALFABLOK")
        self.assertContains(yanit, "BETABLOK")

    def test_body_metni_sayfada_gorunmuyor(self):
        # Iddia: body alanindaki metin (iki paragrafi da) sayfaya hic dusmuyor.
        yazi = self._yazi(body="OLUGOVDEBIR\n\nOLUGOVDEIKI")
        yanit = self._sayfa(yazi)
        self.assertNotContains(yanit, "OLUGOVDEBIR")
        self.assertNotContains(yanit, "OLUGOVDEIKI")

    def test_pullquote_metni_ve_sinifi_sayfada_yok(self):
        # Iddia: pullquote metni basilmiyor ve HTML'de class="pullquote" hic gecmiyor.
        yazi = self._yazi(pullquote="OLUALINTI")
        yanit = self._sayfa(yazi)
        self.assertNotContains(yanit, "OLUALINTI")
        self.assertNotContains(yanit, 'class="pullquote"')

    def test_iki_isaretli_baslik_icindekiler_basar(self):
        # Iddia: iki in_toc basligi varsa icindekiler listesi basiliyor.
        yazi = self._yazi()
        self._baslik(yazi, 1, "Birinci")
        self._baslik(yazi, 2, "Ikinci")
        self.assertContains(self._sayfa(yazi), 'class="article-toc"')

    def test_tek_isaretli_baslik_icindekiler_basmaz(self):
        # Iddia: tek isaretli baslikta liste basilmiyor; isaretsiz ikinci baslik esige sayilmiyor.
        yazi = self._yazi()
        self._baslik(yazi, 1, "Birinci")
        self._baslik(yazi, 2, "Ikinci", in_toc=False)
        self.assertNotContains(self._sayfa(yazi), 'class="article-toc"')


class BlogPostAdminTests(TestCase):
    """KB-28: admin aramasi olu body alanina bakmiyor."""

    def test_admin_aramasi_body_kullanmiyor(self):
        # Iddia: BlogPostAdmin.search_fields icinde "body" yok.
        self.assertNotIn("body", BlogPostAdmin.search_fields)
