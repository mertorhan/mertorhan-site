"""
Galeri gorselleri icin kucultme yardimcilari.

Amac: fotograf makinesinden gelen ~8 MB / 6000px dosyalari
web icin yeterli olcuye indirmek.

KARAR (23 Temmuz): orijinal dosya sunucuda SAKLANMAZ, uzerine yazilir.
Orijinaller Mert'in kendi bilgisayarinda duruyor.
"""

import os

from PIL import Image, ImageOps

# Buyuk gorsel — lightbox'ta gosterilen
MAX_LONG_EDGE = 2000
JPEG_QUALITY = 86

# Kucuk kopya — izgarada gosterilen
THUMB_LONG_EDGE = 800
THUMB_QUALITY = 82


def _gorseli_ac(yol):
    """Dosyayi ac, EXIF donme bilgisini uygula, JPEG'e uygun moda cevir."""
    img = Image.open(yol)

    # Kameralar bazen "bu foto 90 derece donuk" bilgisini EXIF'e yazar.
    # Kucultmeden once bunu GERCEK piksellere uygulamazsak foto yan yatar.
    img = ImageOps.exif_transpose(img)

    # JPEG seffaflik desteklemez: RGBA / P / LA gelirse RGB'ye ceviriyoruz.
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")

    return img


def _jpeg_kaydet(img, yol, kalite):
    """
    progressive=True -> yavas baglantida foto once bulanik, sonra netlesir.
    optimize=True    -> ekstra sikistirma, kalite kaybi yok.
    """
    img.save(yol, format="JPEG", quality=kalite, optimize=True, progressive=True)


def jpeg_yolu(yol):
    """Uzantiyi .jpg yapar (PNG yuklenirse dosya adi yalan soylemesin)."""
    kok, uzanti = os.path.splitext(yol)
    if uzanti.lower() in (".jpg", ".jpeg"):
        return yol
    return kok + ".jpg"


def kucult(yol, max_kenar=MAX_LONG_EDGE, kalite=JPEG_QUALITY):
    """
    Gorseli YERINDE kucultur.
    Uzanti .jpg degilse yeni bir .jpg yazip eskisini siler.
    Yeni dosya yolunu dondurur.
    """
    img = _gorseli_ac(yol)

    # thumbnail() orani korur; sadece buyukse kucultur.
    if max(img.size) > max_kenar:
        img.thumbnail((max_kenar, max_kenar), Image.LANCZOS)

    hedef = jpeg_yolu(yol)
    _jpeg_kaydet(img, hedef, kalite)
    img.close()

    # Uzanti degistiyse eski dosyayi birakmayalim
    if hedef != yol and os.path.exists(yol):
        os.remove(yol)

    return hedef


def kucuk_kopya_uret(kaynak_yol, hedef_yol,
                     max_kenar=THUMB_LONG_EDGE, kalite=THUMB_QUALITY):
    """Izgarada gosterilecek kucuk kopyayi uretir."""
    klasor = os.path.dirname(hedef_yol)
    if klasor:
        os.makedirs(klasor, exist_ok=True)

    img = _gorseli_ac(kaynak_yol)
    img.thumbnail((max_kenar, max_kenar), Image.LANCZOS)
    _jpeg_kaydet(img, hedef_yol, kalite)
    img.close()

    return hedef_yol