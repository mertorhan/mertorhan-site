from django.db.models import Count, Q
from django.shortcuts import render

from .models import Photo, PhotoCategory


def photo_list(request):
    photos = Photo.objects.filter(is_published=True)

    # Kategori filtresi ID tabanli: ?kategori=3
    # Sayisal olmayan deger yok sayilir — eski ?kategori=Manzara bicimindeki
    # bir yer imi sayfayi patlatmasin, tumunu gostersin.
    ham_secim = request.GET.get("kategori", "")
    try:
        secili_id = int(ham_secim)
    except (TypeError, ValueError):
        secili_id = None

    if secili_id is not None:
        photos = photos.filter(category_id=secili_id)

    # Kategori haplari sayaclariyla. Adet YAYINDA OLAN fotograflari sayar;
    # adedi 0 olan kategori hic gorunmez (bos hap tiklanip bos sayfa
    # acmasin).
    kategoriler = [
        {
            "deger": str(kategori.pk),
            "etiket": kategori.name,
            "adet": kategori.adet,
            "secili": kategori.pk == secili_id,
        }
        for kategori in PhotoCategory.objects.annotate(
            adet=Count("photo", filter=Q(photo__is_published=True))
        ).filter(adet__gt=0)
    ]

    return render(request, "gallery/photo_list.html", {
        "photos": photos,
        "selected": secili_id,
        "kategoriler": kategoriler,
    })
