# mertorhan.com — Proje Rehberi

Bu dosya Claude Code içindir. Projeye dair kalıcı bilgiler ve kurallar burada.

## Dil
Benimle **Türkçe** konuş. Kod ve değişken isimleri İngilizce, ekranda görünen
metinler Türkçe.

## Proje nedir
Mert Orhan'ın kişisel marka sitesi. Django ile yazılmış, PythonAnywhere'de canlı.
Site bir vitrin/rehber — reklam panosu değil.

**Marka pusulası: "SAT DEĞİL, GÖSTER."**
- Billboard/slogan/pazarlama dili yasak.
- Dürüstlük > estetik.
- Kimlik: kuran/üreten bağımsız biri. "İş arayan" tonu kullanma.

## Teknik künye
- Django 6.0.6 · SQLite · python-decouple · Pillow
- Yerel: `~/Desktop/mertorhan-site` · sanal ortam proje içinde (`venv/`)
- Canlı: PythonAnywhere · `~/mertorhan-site` · sanal ortam `mertorhan-env`
- Depo: github.com/mertorhan/mertorhan-site (ana dal: `main`, **public**)

## Uygulamalar (6)
| App | İçerik |
|---|---|
| `core` | Profile, Experience, ContactMessage, ana sayfa, hakkında, `base.html` |
| `blog` | BlogPost, Category |
| `gallery` | Photo, görsel optimizasyon (`imaging.py`, `optimize_photos`) |
| `guide` | Guide, GuideStop (haritalı gezi rotaları) |
| `movies` | Review |
| `books` | Book, BookQuote |

## URL haritası (`config/urls.py`)
`/admin/` · `/blog/` · `/gallery/` · `/guide/` · `/filmler/` · `/kitaplar/` · `/` (core)

⚠️ `path('', include('core.urls'))` **her zaman en altta** kalmalı — üste alınırsa
diğer tüm adresleri yutar.

## Tasarım tokenları
Renk ve font **asla sabit değer olarak yazılmaz**, `static/css/style.css` içindeki
`:root` değişkenleri kullanılır:

- Zemin: `--paper: #f4f1e9` · `--card: #fbf9f3`
- Metin: `--ink: #232019` · `--body: #332f29` · `--secondary: #5f5a4f` · `--faint: #9a9282`
- Vurgu: `--terracotta: #b4533a` · Durum: `--green: #5e8b5a`
- Çizgi: `--line: rgba(35, 32, 25, 0.15)` · Genişlik: `--container: 1160px`
- Font: `--font-serif` Newsreader · `--font-sans` Hanken Grotesk

`style.css` numaralı bölümlerden oluşur (~2300 satır). Yeni CSS eklerken uygun
bölüme ekle; uymuyorsa sona numaralı yeni bölüm aç. Bölüm başlıklarını bozma.

## Sık komutlar (yerelde, venv aktifken)
```bash
source venv/bin/activate
python manage.py runserver
python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic
```

## JIRA

İşler Jira'da takip edilir. Proje anahtarı: **KB**
Kartlar `KB-12` gibi numaralanır; epic'ler de aynı anahtarı taşır (`KB-1`).

Bir işe başlarken sana kart numarasını veririm. Numara verilmediyse **sor** —
kartsız iş yapmıyoruz.

## ÇALIŞMA KURALLARI

1. **Önce plan, sonra kod.** Dosyaya dokunmadan önce ne yapacağını maddeler
   hâlinde söyle ve onayımı bekle.
2. **Küçük adımlar.** Aynı anda tek konu. Beş dosyayı birden değiştirme.
3. **Nedenini açıkla.** Her değişikliğin gerekçesini anlat — bu proje aynı zamanda
   benim öğrenme sürecim. Ezber yaptırma.
4. **Varsayım yapma.** Emin değilsen sor.
5. İş bitince **rapor formatına göre özet ver**.

## KAPSAM FRENİ

Sana verilen kartın dışına çıkma. Bu kural diğer her şeyin üstündedir.

- Yolda başka bir sorun görürsen **düzeltme.** Bana söyle, Jira'ya kart açayım.
- "Zaten oradaydım, hazır düzelttim" yapma. Küçük de olsa yapma.
- Bir iş için birden fazla dosya değişmesi normaldir; birden fazla **konu**
  değişmesi normal değildir.

Neden: aynı anda iki iş yaparsan, bir şey kırıldığında hangisinin kırdığı
belli olmaz. Test etmesi de geri alması da zorlaşır.

İstisna yok. Emin değilsen sor.

## DAL (BRANCH) DÜZENİ

**Kural: `main` üzerinde iş yapılmaz.** Her iş maddesi kendi dalında yürür.

### Başlarken
1. `git status` ile çalışma alanının temiz olduğunu doğrula.
2. Kirliyse **bana sor** — kendi kararınla temizleme.
3. Dalı aç:
```bash
   git checkout main
   git pull
   git checkout -b is/KB-12-kisa-aciklama
```

### Dal isimlendirme (Türkçe karakter ve boşluk YOK)

Kalıp: `tur/KB-<numara>-kisa-aciklama`

- Geliştirme → `is/KB-12-galeri-asimetrik-duzen`
- Hata düzeltme → `duzeltme/KB-15-lightbox-tasmasi`
- Deneme → `deneme/KB-20-...`

Kart numarası dal adında **zorunlu.** Numarayı bilmiyorsan dal açma, bana sor.

### Biterken

1. `python manage.py check` çalıştır. Hata varsa önce onu çöz.
2. **Commit at** (bu senin işin, benim değil). Mantıksal olarak ayrı
   değişiklikler ayrı commit'lere bölünür.
3. **Push etme.** Merge ve push kararı bana ait.
4. Raporunu aşağıdaki formatta ver.

### Rapor formatı

    KART:     KB-12
    DAL:      is/KB-12-galeri-asimetrik-duzen
    COMMIT:   <commit mesaji/mesajlari>
    DEGISEN:  <dosya listesi, her biri icin tek satir neden>
    RISK:     <ne kirilabilir, neyi kacirmis olabilirim>
    TEST:     <benim tarayicida ne kontrol etmem gerekiyor, madde madde>

`RISK` satırını boş bırakma. "Risk yok" diyeceksen bile neden olmadığını yaz.

### İstisna
Tek commit'lik ufak işlerde (ör. bu dosyayı güncellemek) dal şart değil.
Emin değilsen dal aç — maliyeti sıfır.

### ⚠️ MIGRATION UYARISI
Dal silmek **veritabanını geri almaz.** Bu yüzden:
- Migration üretilecekse önce bana haber ver.
- `makemigrations` çalıştırabilirsin.
- **`migrate` komutunu onayım olmadan çalıştırma.**

## GIT KURALLARI
- `git push` **yapma** — push'u ben yaparım.
- `git merge` / `git rebase` **yapma** — merge kararı bana ait.
- `git reset --hard`, `git clean` gibi yıkıcı komutları **asla** çalıştırma.
- Commit mesajları Türkçe ama **Türkçe karakter kullanmadan** yazılır ve
  **kart numarasıyla başlar**:
  `KB-12: Galeri asimetrik duzen`
  `KB-15: Lightbox tasmasi duzeltildi`
- Depo public — koda hiçbir sır, şifre, anahtar, kişisel e-posta gömülmez.

## DOKUNMA (değiştirme, silme, okuma amaçlı bile açma)
- `.env` — gizli anahtarlar burada. **Kalıcı izin isteme.**
- `db.sqlite3` — yerel veritabanı
- `media/` — yüklenen fotoğraflar (repoda yok, sunucuda yaşar)
- `venv/` · `staticfiles/`
- `.gitignore` içeriğini onayım olmadan değiştirme

## İçerik nerede yaşar
Site metinleri ve görselleri **veritabanından** gelir, koddan değil. Yani
"LinkedIn linki yanlış" gibi bir sorun genelde kod hatası değil, admin
panelindeki kayıttır. Kodu değiştirmeden önce bunu bana hatırlat.