"""
Mevcut galeri fotograflarini tek seferde kucultur.

Kullanim:
    python manage.py optimize_photos --dry-run   # sadece rapor
    python manage.py optimize_photos             # gercek islem
"""

import os

from django.conf import settings
from django.core.management.base import BaseCommand

from gallery.imaging import kucult, kucuk_kopya_uret
from gallery.models import Photo


def _mb(bayt):
    return round(bayt / 1048576, 2)


class Command(BaseCommand):
    help = "Mevcut galeri fotograflarini kucultur ve kucuk kopyalarini uretir."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Dosyalara DOKUNMADAN sadece mevcut durumu raporlar.",
        )

    def handle(self, *args, **secenekler):
        kuru = secenekler["dry_run"]
        fotograflar = Photo.objects.all()

        if not fotograflar:
            self.stdout.write("Galeride fotograf yok.")
            return

        onceki_toplam = 0
        sonraki_toplam = 0
        islenen = 0
        atlanan = 0

        for foto in fotograflar:
            if not foto.image:
                continue

            yol = foto.image.path
            if not os.path.exists(yol):
                self.stdout.write(self.style.WARNING(
                    f"  ATLANDI (dosya yok): {foto.image.name}"
                ))
                atlanan += 1
                continue

            onceki = os.path.getsize(yol)
            onceki_toplam += onceki

            if kuru:
                from PIL import Image
                with Image.open(yol) as im:
                    olcu = im.size
                self.stdout.write(
                    f"  {foto.title[:30]:30} {olcu[0]}x{olcu[1]}  {_mb(onceki)} MB"
                )
                continue

            # 1) Buyuk gorseli kucult
            yeni_yol = kucult(yol)
            yeni_ad = os.path.relpath(yeni_yol, settings.MEDIA_ROOT).replace("\\", "/")

            # 2) Kucuk kopyayi uret
            kucuk_ad = "gallery/thumbs/" + os.path.basename(yeni_yol)
            kucuk_kopya_uret(yeni_yol, os.path.join(settings.MEDIA_ROOT, kucuk_ad))

            # 3) Veritabanini guncelle.
            #    .update() kullaniyoruz ki model'in save() metodu devreye girip
            #    dosyayi TEKRAR islemeye kalkmasin.
            sonraki = os.path.getsize(yeni_yol)
            sonraki_toplam += sonraki

            Photo.objects.filter(pk=foto.pk).update(
                image=yeni_ad,
                thumbnail=kucuk_ad,
            )

            islenen += 1
            self.stdout.write(
                f"  {foto.title[:30]:30} {_mb(onceki)} MB -> {_mb(sonraki)} MB"
            )

        self.stdout.write("")

        if kuru:
            self.stdout.write(self.style.WARNING(
                f"KURU CALISMA — hicbir dosyaya dokunulmadi. "
                f"Toplam: {_mb(onceki_toplam)} MB"
            ))
            return

        if onceki_toplam:
            kazanc = 100 - (sonraki_toplam / onceki_toplam * 100)
        else:
            kazanc = 0

        self.stdout.write(self.style.SUCCESS(
            f"BITTI. {islenen} fotograf islendi, {atlanan} atlandi.\n"
            f"Toplam: {_mb(onceki_toplam)} MB -> {_mb(sonraki_toplam)} MB "
            f"(%{kazanc:.0f} azalma)"
        ))