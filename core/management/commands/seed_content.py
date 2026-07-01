"""
core/management/commands/seed_content.py
Bugün netleştirdiğimiz içerikleri veritabanına yükler:
  - Profil: tanım cümlesi (tagline), kimlik çipleri (role), Hakkımda başlığı ve biyografi
  - Deneyim: Pi-Course, QNB Finansbank, Eğitim (en yeni üstte)

Çalıştırma:  python manage.py seed_content
Not: Fotoğraf, LinkedIn, e-posta, CV alanlarına DOKUNMAZ (varsa korunur).
"""

from django.core.management.base import BaseCommand
from core.models import Profile, Experience


TAGLINE = (
    "Karmaşık problemlerle uğraşmayı, onları çözüp dijital ürünlere ve "
    "süreçlere dönüştürmeyi seven; dünyayı fotoğraflayarak anlamaya çalışan biri."
)

ROLE_CHIPS = "Ürün yönetimi · Okur-yazar · Amatör fotoğrafçı"

ABOUT_TITLE = "Hakkımda"

BIO = """Merakım en baştan beri iki koldan ilerledi: bir yanda işletme ve ekonomi, diğer yanda yazılım ve teknoloji. Bu ikisi tek başına beni tam yansıtmadığı için hep ikisini bir arada ele alan bir yaklaşım aradım; yolum da tam ortada duran bir alanla, Yönetim Bilişim Sistemleri (MIS) ile kesişti — işi teknolojiyle, insanı sistemle buluşturan bir alan.

Sonrasında, daha 3. sınıftayken tanıştığım kurumsal hayatta beyaz yakalı olarak farklı pozisyonlarda görev aldım. Ağırlıklı olarak KOBİ'lerin iş süreçlerini dijitalleştiren bir platformun ürün yönetimi ekibinde çalışırken kendimi bulduğumu hissettim. Fakat her beyaz yakalının hayali gibi, bende de kendi işimi yapma isteği vardı; kurumsal hayattan ayrılıp eğitim teknolojileri sektöründe faaliyet gösteren bir girişime ortak olarak girdim. Temel sorumluluğum bilişim tarafı olsa da; muhasebeden yasal süreçlere, insan kaynaklarından ekip yönetimine kadar bir şirketin hemen her köşesine girdiğim yoğun bir iki yıl geçirdim.

Şimdi ise farklı projelere girebilmek, aynı zamanda dünyayı gezip anlayabilmek için tamamen bağımsızlaştığım bir sürece girdim. Bu site de o yolculuğun bir parçası. Bir yandan farklı projelerde farklı insanlarla tanışırken, bir yandan da merak ettiğim her konuda okuma-yazma fırsatı buluyorum: ekonomiden tarihe, teknolojiden fiziğe aklıma takılan ne varsa okuyor, araştırıyor ve öğrendiklerimi burada yazıyorum. Fotoğrafçılık ise bu merakımın en sevdiğim hâli; dünyayı çerçeveleyerek anlamaya, anladıkça da yeni soruların peşinden koşmaya çalışıyorum. Kısacası burası, öğrendiklerimi büyük bir keyifle paylaşarak —ve çoğu zaman paylaşırken öğrenerek— yazdığım bir yer."""


EXPERIENCES = [
    {
        "order": 1,
        "date_range": "2024 – 2026",
        "role": "Pi-Course · Şirket Ortağı · Eğitim teknolojileri girişimi",
        "description": """Ürün ve yazılım geliştirme
- Şirket vizyonu doğrultusunda ürün ihtiyaçlarının belirlenmesi.
- Teknik dokümanların ve iş analizlerinin hazırlanması.
- Yazılımcı ortakla ürünün geliştirilmesi ve uçtan uca kullanıcı testlerinin yürütülmesi.
- Şirket içi eğitimlerin düzenlenmesi ve ürünlerin tanıtılması.

Operasyon ve kurumsallaşma
- Resmi ve yasal süreçlerin yürütülmesi.
- Muhasebe ve insan kaynakları süreçlerinin yönetimi.
- İş süreçlerinin standartlaştırılması ve dokümante edilmesi (SOP).""",
    },
    {
        "order": 2,
        "date_range": "2018 – 2023",
        "role": "QNB Finansbank · Ürün Yönetimi & Dijital Dönüşüm",
        "description": """Uzun dönem stajlar
- Ticari/Kurumsal Bankacılık Pazarlaması ve Uluslararası Bankacılık departmanlarında uzun dönem staj.
- Raporların ve yönetim sunumlarının hazırlanması, muhabir bankalarla iletişim.

Yönetici Adaylığı (MT) programı
- 6 aylık, banka içi yoğun sınıf eğitimlerinden oluşan bir yönetici adaylığı programı.
- Temel bankacılık ve finanstan satış ve müşteri yönetimine, liderlik gelişiminden departman tanıtımlarına kadar teorik eğitimler.
- Call center'dan şubeye farklı departmanlarda uygulamalı oryantasyon ve yerinde öğrenme.

KOBİ bankacılığı ürün yönetimi
- KOBİ kredileri tarafında ürün yönetimi ekibinde görev.
- Kredi gelişimi ve saha takibi için düzenli raporlamalar.
- Saha ile IT ekibi arasında köprü görevi; kredi ekranlarının doğru çalıştığından emin olunması.

Dijital dönüşüm
- Müşterilerin farklı firmalarca sağlanan ürün ve hizmetlere tek şifreyle (SSO) eriştiği platformun ürün yönetiminde aktif rol.
- 3. parti entegrasyonları için IT ekibiyle ortak süreç yönetimi.
- RPA (robotik süreç otomasyonu) ile rutin süreçlerin otomasyonu.
- Çağrı merkezine ulaşan müşterilerin doğru yönlendirilmesi için IVR (sesli yanıt) yönetimi.
- Çağrı merkezi çalışanlarının müşteri sorunlarını daha hızlı çözebilmesi için ekranlarının geliştirilmesi.
- Müşteri–çağrı merkezi arasında Canlı Chat ile yazılı iletişimin sağlanması.
- Yeni ürünlerin ilgili departmanlara tanıtılması ve doğru kullanımı için şirket içi eğitimler.
- İş analizi ve raporlama süreçleriyle ürünlerin doğru ve eksiksiz çalıştığından emin olunması.""",
    },
    {
        "order": 3,
        "date_range": "2014 – 2019",
        "role": "Eğitim — Boğaziçi Üniversitesi · Yönetim Bilişim Sistemleri (MIS)",
        "description": """- İşletme ve teknolojinin kesiştiği MIS bölümü; iki ilgi alanını birden besleyen bir alan.
- Öğrenci Temsilciliği'nde bölüm ve fakülte başkanlığı.
- Öğrenci Temsilciliği Okul Yönetim Kurulu üyeliği.
- Bilişim Kulübü'nde (Compec) ISACA siber güvenlik alt kurulu başkanlığı.
- Bilişim Kulübü (Compec) yönetim kurulu üyeliği.""",
    },
]


class Command(BaseCommand):
    help = "Profil ve Deneyim içeriklerini veritabanına yükler."

    def handle(self, *args, **options):
        # 1) Tek Profil kaydını al ya da oluştur
        profile = Profile.objects.first()
        if profile is None:
            profile = Profile(full_name="Mert Orhan")
            self.stdout.write("Profil bulunamadı, yenisi oluşturuluyor…")

        # 2) Sadece bizim alanları güncelle (foto/linkedin/e-posta/cv'ye dokunma)
        profile.full_name = profile.full_name or "Mert Orhan"
        profile.tagline = TAGLINE
        profile.role = ROLE_CHIPS
        profile.about_title = ABOUT_TITLE
        profile.bio = BIO
        profile.save()
        self.stdout.write(self.style.SUCCESS("✓ Profil güncellendi (tagline, çipler, Hakkımda)."))

        # 3) Deneyimleri sıfırla ve yeniden yaz
        silinen = profile.experiences.count()
        profile.experiences.all().delete()
        for exp in EXPERIENCES:
            Experience.objects.create(profile=profile, **exp)
        self.stdout.write(
            self.style.SUCCESS(
                f"✓ Deneyim yenilendi ({silinen} eski silindi, {len(EXPERIENCES)} yeni eklendi)."
            )
        )

        self.stdout.write(self.style.SUCCESS("Bitti. Web uygulamasını 'Reload' etmeyi unutma."))