from django.conf import settings


def analytics(request):
    """Analytics ayarlarini her sablona tasir.

    GA olcum kimligi settings uzerinden .env'den geliyor. Context processor
    olmadan her view'in bu degeri context'e tek tek eklemesi gerekirdi;
    base.html tum sayfalarda ortak oldugu icin tek noktadan besliyoruz.

    request parametresi burada kullanilmiyor ama Django'nun context processor
    sozlesmesi geregi zorunlu.
    """
    return {'GA_MEASUREMENT_ID': settings.GA_MEASUREMENT_ID}
