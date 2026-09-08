from django.core.exceptions import ValidationError
from django.test import TestCase

from .models import Review


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
