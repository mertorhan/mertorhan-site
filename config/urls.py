from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from decouple import config

# Admin adresi .env'den gelir (depo public — gercek adres koda yazilmaz).
# .env'de tanimsizsa veya bos birakilmissa varsayilan 'admin/' surer;
# bos deger ana sayfayi yutacagi icin ayrica ele aliniyor.
ADMIN_URL = config('ADMIN_URL', default='admin/').strip() or 'admin/'

urlpatterns = [
    path(ADMIN_URL, admin.site.urls),
    path("blog/", include("blog.urls")),
    path('gallery/', include('gallery.urls')),
    path('guide/', include('guide.urls')),
    path('filmler/', include('movies.urls')),
    path('kitaplar/', include('books.urls')),
    path('', include('core.urls')),
]

# Gelistirmede (DEBUG=True) yuklenen medya dosyalarini servis et
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)