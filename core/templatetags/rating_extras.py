"""
core/templatetags/rating_extras.py
Puani ekranda gostermek icin iki kucuk yardimci: yildiz satiri ve
Turkce ondalik ayracli sayi bicimi.
"""

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from django import template

register = template.Library()

# Olcek 1-10. Degisirse yildiz sayisi da degisir.
SCALE = 10


def _to_decimal(value):
    """Sablondan gelen sayiyi Decimal'e cevirir; olmuyorsa None."""
    if value is None or value == "":
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None


@register.filter
def yildiz_satiri(value):
    """
    Puani 10 elemanli bir listeye cevirir: "full" | "half" | "empty".
    Sablon bu listeyi dolasip yildizlari basar.

    Ornek: 7.4 -> en yakin 0,5'e yuvarlanir (7,5) -> 7 dolu, 1 yarim, 2 bos.
    """
    score = _to_decimal(value)
    if score is None:
        return []

    # Yarim yildiz adimlarla sayiyoruz: 1 adim = 0,5 puan.
    # round() yerine ROUND_HALF_UP; round() bankaci yuvarlamasi yapar.
    steps = int((score * 2).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    steps = max(0, min(SCALE * 2, steps))

    row = []
    for index in range(1, SCALE + 1):
        if steps >= index * 2:
            row.append("full")
        elif steps == index * 2 - 1:
            row.append("half")
        else:
            row.append("empty")
    return row


@register.filter
def puan(value):
    """
    Ortalama puani Turkce ondalik ayraciyla, tek hane sabit yazar:
    7.4 -> "7,4" · 8 -> "8,0"

    Sadece ORTALAMA icin. Alt kriter puanlari tam sayi, orada ondalik
    bilgi tasimaz ("8/10" yazar, "8,0/10" degil).

    Sitenin LANGUAGE_CODE'u en-us; ayara dokunmadan burada bicimliyoruz.
    """
    score = _to_decimal(value)
    if score is None:
        return ""
    quantized = score.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
    return f"{quantized}".replace(".", ",")
