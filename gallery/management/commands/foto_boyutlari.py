"""
Mevcut fotograflarin boyut alanlarini doldurur.

Boyut alanlari (image_width / image_height) yeni eklendi; bu alanlar
yalnizca fotograf KAYDEDILIRKEN olculuyor. Daha once yuklenmis kayitlar
bos kalir — bu komut onlari tek seferde doldurur.

Kullanim:
    python manage.py foto_boyutlari            # sadece bos olanlar
    python manage.py foto_boyutlari --force    # dolu olanlari da yeniden olc

Tekrar tekrar calistirilabilir: dolu kayitlari atlar.
"""

import os

from django.core.management.base import BaseCommand

from gallery.models import Photo, gorsel_olcusu


class Command(BaseCommand):
    help = "Fotograflarin image_width / image_height alanlarini doldurur."

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Boyutu ZATEN DOLU olan kayitlari da yeniden olcer.",
        )

    def handle(self, *args, **secenekler):
        zorla = secenekler["force"]

        fotograflar = Photo.objects.all()
        if not zorla:
            # Tek bir alani bile eksikse yeniden olcelim
            fotograflar = fotograflar.filter(image_width=None) | fotograflar.filter(image_height=None)
            fotograflar = fotograflar.distinct()

        taranan = 0
        yazilan = 0
        atlanan = 0

        for foto in fotograflar:
            taranan += 1

            if not foto.image:
                self.stdout.write(self.style.WARNING(
                    f"  ATLANDI (gorsel alani bos): {foto.title[:40]}"
                ))
                atlanan += 1
                continue

            yol = foto.image.path
            if not os.path.exists(yol):
                self.stdout.write(self.style.WARNING(
                    f"  ATLANDI (dosya diskte yok): {foto.image.name}"
                ))
                atlanan += 1
                continue

            try:
                # models.gorsel_olcusu: imaging._gorseli_ac uzerinden olcer,
                # yani EXIF donmesi uygulanmis "ekranda gorunen" olcu.
                # Yeni kayitlarla ayni yol olsun diye ayni fonksiyon.
                genislik, yukseklik = gorsel_olcusu(yol)
            except (OSError, ValueError) as hata:
                # Bozuk / yarim inmis dosya tum komutu durdurmasin
                self.stdout.write(self.style.WARNING(
                    f"  ATLANDI (dosya okunamadi: {hata}): {foto.image.name}"
                ))
                atlanan += 1
                continue

            # .update(): save() devreye girip dosyayi TEKRAR kucultmeye
            # kalkmasin. Her kayitta yeniden sikisan JPEG'in kalitesi erir.
            Photo.objects.filter(pk=foto.pk).update(
                image_width=genislik,
                image_height=yukseklik,
            )
            yazilan += 1
            self.stdout.write(f"  {foto.title[:40]:40} {genislik}x{yukseklik}")

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(
            f"{taranan} fotograf tarandi, {yazilan} yazildi, {atlanan} atlandi."
        ))
