from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from .models import Director, Review


class ReviewRuntimeTests(TestCase):
    """KB-115: sure alani (dakika)."""

    def test_runtime_bos_birakilabilir(self):
        # Sure girilmeden kayit olusabilmeli: dizi bitmeden sure bilinmiyor.
        review = Review.objects.create(title="Suresiz Film", body="Yorum.")
        # Bellekteki nesneye degil, veritabanindan geri okunan kayda bakiliyor;
        # yoksa test alanin kaydedildigini degil, Python nesnesine atandigini
        # olcmus olur.
        kayitli = Review.objects.get(pk=review.pk)
        self.assertIsNone(kayitli.runtime)

    def test_runtime_girilen_deger_geri_okunuyor(self):
        review = Review.objects.create(title="Sureli Film", body="Yorum.", runtime=142)
        kayitli = Review.objects.get(pk=review.pk)
        self.assertEqual(kayitli.runtime, 142)

    def test_runtime_negatif_deger_kabul_etmiyor(self):
        # PositiveIntegerField dogrulayicisini model katmaninda tasir;
        # admin formu da bu yoldan gectigi icin full_clean() ile olculuyor.
        review = Review(title="Eksi Sure", body="Yorum.", runtime=-1)
        with self.assertRaises(ValidationError) as ctx:
            review.full_clean()
        self.assertIn("runtime", ctx.exception.error_dict)


class ReviewOzetTests(TestCase):
    """KB-115: liste sayfasi ustundeki ozet satiri."""

    def _ozet(self, sorgu=""):
        """
        Sayfayi cagirir, ozet listesini {etiket: sayi} sozlugune cevirir.
        Testler sayilari view'in urettigi haliyle okusun diye context
        uzerinden gidiliyor.
        """
        yanit = self.client.get(reverse("review_list") + sorgu)
        self.assertEqual(yanit.status_code, 200)
        return {oge["etiket"]: oge["sayi"] for oge in yanit.context["ozet"]}

    def test_kayit_sayisi_dogru(self):
        for i in range(3):
            Review.objects.create(title=f"Film {i}", slug=f"film-{i}", body="Yorum.")
        self.assertEqual(self._ozet()["KAYIT"], 3)

    def test_runtime_bos_kayitlar_saat_toplamina_girmiyor(self):
        Review.objects.create(title="Sureli", slug="sureli", body="Y.", runtime=120)
        Review.objects.create(title="Suresiz", slug="suresiz", body="Y.")
        ozet = self._ozet()
        self.assertEqual(ozet["KAYIT"], 2)
        self.assertEqual(ozet["SAAT"], 2)

    def test_doksan_dakika_iki_saat(self):
        # 90 dk = 1,5 saat -> 2. Bu test yuvarlama YONUNU olcer, yontemi
        # degil: round() de ayni sonucu verir. Yontemi civileyen test
        # test_yuzelli_dakika_uc_saat.
        Review.objects.create(title="Doksan", slug="doksan", body="Y.", runtime=90)
        self.assertEqual(self._ozet()["SAAT"], 2)

    def test_seksendokuz_dakika_bir_saat(self):
        Review.objects.create(title="Seksendokuz", slug="seksendokuz", body="Y.", runtime=89)
        self.assertEqual(self._ozet()["SAAT"], 1)

    def test_yuzelli_dakika_uc_saat(self):
        # Tek ayirt edici durum: 150 dk = 2,5 saat.
        # round(2.5) == 2 (bankaci yuvarlamasi), bizim formul 3 verir.
        # Bu test kirilmadan (dakika + 30) // 60 degistirilemez.
        Review.objects.create(title="Yuzelli", slug="yuzelli", body="Y.", runtime=150)
        self.assertEqual(self._ozet()["SAAT"], 3)

    def test_yayinda_olmayan_kayit_hicbir_sayaca_girmiyor(self):
        yonetmen = Director.objects.create(name="Gizli Yönetmen")
        gizli = Review.objects.create(
            title="Gizli", slug="gizli", body="Y.", runtime=600, is_published=False
        )
        gizli.directors.add(yonetmen)
        Review.objects.create(title="Acik", slug="acik", body="Y.", runtime=60)

        ozet = self._ozet()
        self.assertEqual(ozet["KAYIT"], 1)
        self.assertEqual(ozet["SAAT"], 1)
        self.assertNotIn("YÖNETMEN", ozet)

    def test_filtre_uygulaninca_sayilar_degismiyor(self):
        # SABIT SAYAC: ustteki Film/Dizi secimi grid'i suzer, sayaci DEGIL.
        Review.objects.create(title="Bir Film", slug="bir-film", body="Y.", content_type="film")
        Review.objects.create(title="Bir Dizi", slug="bir-dizi", body="Y.", content_type="dizi")
        Review.objects.create(title="Iki Dizi", slug="iki-dizi", body="Y.", content_type="dizi")

        self.assertEqual(self._ozet()["KAYIT"], 3)
        self.assertEqual(self._ozet("?tur=dizi")["KAYIT"], 3)
        self.assertEqual(self._ozet("?tur=film")["KAYIT"], 3)

    def test_sifir_olan_istatistik_listede_yok(self):
        # Hic yonetmen iliskisi girilmemis: "0 YÖNETMEN" basilmamali.
        Review.objects.create(title="Yalniz", slug="yalniz", body="Y.")
        ozet = self._ozet()
        self.assertIn("KAYIT", ozet)
        self.assertNotIn("YÖNETMEN", ozet)
        self.assertNotIn("SAAT", ozet)
