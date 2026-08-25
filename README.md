# mertorhan.com

Kişisel bir site: gittiğim yerler, okuduğum kitaplar, izlediğim
filmler ve çektiğim fotoğraflar için bir vitrin.

Django ile yazıldı, PythonAnywhere'de yayında.
Canlı: https://www.mertorhan.com

## Bölümler

| Bölüm | Ne var |
|---|---|
| Gezi & Öneri | Mekân ve rota önerileri, harita, dürüst değerlendirme |
| Blog | Yazılar |
| Film & Dizi | İzlediklerim, puan ve notlarla |
| Kitap | Okuduklarım, alıntılarla |
| Galeri | Fotoğraflar, EXIF bilgisiyle |
| Hakkında | Kısa bio ve iletişim formu |

## Teknoloji

- Django 6.0.6
- SQLite
- Pillow (görsel işleme, otomatik küçültme)
- python-decouple (ortam ayarları)
- Leaflet + OpenStreetMap (harita)

## Yerelde çalıştırma

Depoyu klonla:

    git clone https://github.com/mertorhan/mertorhan-site.git
    cd mertorhan-site

Sanal ortam kur ve bağımlılıkları yükle:

    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt

Proje kökünde `.env` dosyası oluştur:

    SECRET_KEY=buraya-rastgele-bir-anahtar
    DEBUG=True

Yeni bir anahtar üretmek için:

    python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

Veritabanını kur ve çalıştır:

    python manage.py migrate
    python manage.py createsuperuser
    python manage.py runserver

`http://127.0.0.1:8000` adresinden açılır.

## Proje yapısı

    config/     ayarlar ve URL haritası
    core/       ana sayfa, hakkında, iletişim, ortak şablonlar
    blog/       yazılar
    guide/      gezi önerileri ve rotalar
    gallery/    fotoğraflar
    movies/     film ve dizi incelemeleri
    books/      kitaplar ve alıntılar
    scripts/    bakım betikleri (yedekleme)
    static/     CSS ve statik dosyalar
    media/      yüklenen görseller (depoda yok)

## Notlar

- İçerik Django admin panelinden yönetilir.
- `.env`, `db.sqlite3` ve `media/` depoya dahil değildir; her ortam
  kendi kopyasını tutar.
- Proje kökündeki `CLAUDE.md`, bu depoda Claude Code ile çalışırken
  geçerli olan kuralları içerir.
