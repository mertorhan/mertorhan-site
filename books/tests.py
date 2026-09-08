from django.test import TestCase
from django.urls import reverse

from .models import Author, Book


class BookOzetTests(TestCase):
    """KB-115: liste sayfasi ustundeki ozet satiri."""

    def _ozet(self, sorgu=""):
        """
        Sayfayi cagirir, ozet listesini {etiket: sayi} sozlugune cevirir.
        Testler sayilari view'in urettigi haliyle okusun diye context
        uzerinden gidiliyor.
        """
        yanit = self.client.get(reverse("book_list") + sorgu)
        self.assertEqual(yanit.status_code, 200)
        return {oge["etiket"]: oge["sayi"] for oge in yanit.context["ozet"]}

    def test_kitap_sayisi_dogru(self):
        for i in range(3):
            Book.objects.create(
                title=f"Kitap {i}", slug=f"kitap-{i}", author="Yazar", body="Ozet."
            )
        self.assertEqual(self._ozet()["KİTAP"], 3)

    def test_yazar_sayisi_dogru(self):
        yazar = Author.objects.create(name="Tek Yazar")
        # Hicbir kitaba baglanmayan yazar: sayaca girmemeli.
        Author.objects.create(name="Öteki Yazar")
        for i in range(2):
            kitap = Book.objects.create(
                title=f"Kitap {i}", slug=f"kitap-{i}", author="Yazar", body="Ozet."
            )
            kitap.authors.add(yazar)

        ozet = self._ozet()
        self.assertEqual(ozet["KİTAP"], 2)
        # Ayni yazar iki kitapta 1 sayilir, "Öteki Yazar" hic sayilmaz.
        self.assertEqual(ozet["YAZAR"], 1)

    def test_yayinda_olmayan_kitap_sayilmiyor(self):
        yazar = Author.objects.create(name="Gizli Yazar")
        gizli = Book.objects.create(
            title="Gizli", slug="gizli", author="Yazar", body="Ozet.", is_published=False
        )
        gizli.authors.add(yazar)
        Book.objects.create(title="Acik", slug="acik", author="Yazar", body="Ozet.")

        ozet = self._ozet()
        self.assertEqual(ozet["KİTAP"], 1)
        self.assertNotIn("YAZAR", ozet)

    def test_sifir_olan_istatistik_listede_yok(self):
        # Hic yazar iliskisi girilmemis: "0 YAZAR" basilmamali.
        Book.objects.create(title="Yalniz", slug="yalniz", author="Yazar", body="Ozet.")
        ozet = self._ozet()
        self.assertIn("KİTAP", ozet)
        self.assertNotIn("YAZAR", ozet)
