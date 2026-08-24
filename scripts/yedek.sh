#!/usr/bin/env bash
#
# mertorhan.com — haftalik yedekleme betigi   (Jira: KB-17)
#
# NE YAPAR
#   1. db.sqlite3 dosyasini SQLite'in kendi guvenli yedekleme yoluyla kopyalar
#   2. media/ klasorunu tek bir .tar.gz arsivine sikistirir
#   3. Her turden son 8 yedegi saklar, daha eskilerini siler
#   4. Ne yaptigini ekrana yazar (PythonAnywhere bunu log'a dusuruyor)
#
# NEDEN "HER GUN CALISIP SADECE PAZARTESI IS YAPIYOR"
#   PythonAnywhere zamanlanmis gorevlerde haftalik secenek sunmuyor; yalnizca
#   saatlik ve gunluk var. Bu yuzden gorev her gun tetiklenir, haftalik freni
#   betigin kendisi uygular: Pazartesi degilse hicbir sey yapmadan cikar.
#
# KULLANIM
#   bash scripts/yedek.sh          -> yalnizca Pazartesi is yapar
#   bash scripts/yedek.sh force    -> gun kontrolunu atlar (elle test icin)
#
# NEREDE CALISIR
#   Bu betik SUNUCU icindir (PythonAnywhere). Asagidaki yollar oraya aittir;
#   yerel makinede calistirilmasi beklenmez.

# set -e         : bir komut hata verirse betik hemen dursun, sessizce devam etmesin
# set -u         : tanimsiz degisken kullanilirsa hata versin (yazim hatasi yakalar)
# set -o pipefail: boru hattinda ORTADAKI bir komut patlarsa da hata sayilsin
#                  (yoksa "sqlite3 ... | grep" gibi yerlerde hata gizlenir)
set -euo pipefail


# ══════════════════════════════════════════════════════════════
#  AYARLAR — butun yollar burada. Degisirse tek yerden duzeltilir.
# ══════════════════════════════════════════════════════════════
PROJECT_DIR="/home/mertorhan/mertorhan-site"
BACKUP_DIR="/home/mertorhan/backups"
DB_FILE="$PROJECT_DIR/db.sqlite3"
MEDIA_DIR_NAME="media"           # PROJECT_DIR icindeki klasorun adi
KEEP_COUNT=8                     # saklanacak yedek sayisi (db ve media icin AYRI AYRI)
BACKUP_TZ="Europe/Istanbul"      # asagida aciklandi

# Sunucunun saati UTC calisiyor. Saat dilimini burada sabitliyoruz ki hem
# "bugun Pazartesi mi?" sorusu hem de dosya adindaki tarih Istanbul'a gore
# hesaplansin. Boylece yedek dosyasinin adi, sitede gordugun tarihle ayni olur.
# (Sitenin TIME_ZONE ayari da Europe/Istanbul — KB-11.)
export TZ="$BACKUP_TZ"


# ══════════════════════════════════════════════════════════════
#  YARDIMCI FONKSIYONLAR
# ══════════════════════════════════════════════════════════════

# Hatayi stderr'e yazar ve sifirdan FARKLI kod ile cikar.
# stderr'e yazmasinin sebebi: log'da normal ciktidan ayirt edilebilsin.
hata() {
    echo "HATA: $*" >&2
    exit 1
}

# Insan okuyabilir dosya boyutu dondurur (ornek: 288K, 23M)
boyut() {
    du -h "$1" | cut -f1
}


# ══════════════════════════════════════════════════════════════
#  1) HAFTALIK FREN
# ══════════════════════════════════════════════════════════════

# ${1:-} yazimi: argüman verilmemisse bos string kullan.
# Duz $1 yazsaydik "set -u" yuzunden argümansiz calistirmada betik patlardi.
FORCE_ARG="${1:-}"

if [ "$FORCE_ARG" != "force" ]; then
    # date +%u  -> haftanin gunu (1=Pazartesi ... 7=Pazar)
    if [ "$(date +%u)" -ne 1 ]; then
        echo "Bugun Pazartesi degil ($(date '+%A, %d.%m.%Y %H:%M %Z')). Yedek alinmadi."
        echo "Gun kontrolunu atlamak icin: bash $0 force"
        exit 0        # Bu bir hata DEGIL; gorev basarisiz sayilmasin diye 0.
    fi
fi


# ══════════════════════════════════════════════════════════════
#  2) ON KONTROLLER — is yapmadan once ortami dogrula
# ══════════════════════════════════════════════════════════════

# sqlite3 komutu yoksa DUZ KOPYAYA DUSMUYORUZ. Sebep: SQLite dosyasi yazma
# sirasinda kopyalanirsa bozuk cikabilir ve bunu ancak geri yuklemeye
# calistiginda fark edersin. Sessiz bir bozuk yedek, yedegin olmamasindan
# daha tehlikelidir. O yuzden burada durup sesli hata veriyoruz.
command -v sqlite3 >/dev/null 2>&1 \
    || hata "sqlite3 komutu bulunamadi. Duz kopyaya DUSULMEDI (bozuk yedek riski). Yedek alinmadi."

[ -d "$BACKUP_DIR" ]                  || hata "Yedek klasoru yok: $BACKUP_DIR"
[ -w "$BACKUP_DIR" ]                  || hata "Yedek klasorune yazma izni yok: $BACKUP_DIR"
[ -f "$DB_FILE" ]                     || hata "Veritabani dosyasi bulunamadi: $DB_FILE"
[ -d "$PROJECT_DIR/$MEDIA_DIR_NAME" ] || hata "Medya klasoru bulunamadi: $PROJECT_DIR/$MEDIA_DIR_NAME"


# ══════════════════════════════════════════════════════════════
#  3) DOSYA ADLARI VE GECICI DOSYALAR
# ══════════════════════════════════════════════════════════════

DATE_STAMP="$(date +%F)"          # YYYY-AA-GG  (ornek: 2026-08-24)

DB_OUT="$BACKUP_DIR/db-$DATE_STAMP.sqlite3"
MEDIA_OUT="$BACKUP_DIR/media-$DATE_STAMP.tar.gz"

# Once gecici isme yazip, is bitince asil isme taşiyoruz (mv).
# Sebep: betik yarida olurse (disk dolar, surec kesilir) geride yarim bir
# .tar.gz kalir ve bu "gecerli yedek" gibi gorunur. Gecici isim kullanirsak
# yarim dosya asla yedek sayilmaz.
#
# Isimler NOKTA ile basliyor: hem gizli dosya olurlar, hem de asagidaki
# temizlik kalibina ('db-*.sqlite3') UYMAZLAR — yani silme mantigi bunlara
# hicbir zaman dokunmaz.
TMP_DB="$BACKUP_DIR/.db-gecici.sqlite3"
TMP_MEDIA="$BACKUP_DIR/.media-gecici.tar.gz"

# trap ... EXIT: betik NASIL cikarsa ciksin (basarili, hatali, yarida kesilmis)
# gecici dosyalari sil. Boylece cop birikmez.
trap 'rm -f -- "$TMP_DB" "$TMP_MEDIA"' EXIT

echo "═══════════════════════════════════════════════"
echo "Yedekleme basliyor — $(date '+%A, %d.%m.%Y %H:%M %Z')"
echo "═══════════════════════════════════════════════"


# ══════════════════════════════════════════════════════════════
#  4) VERITABANI YEDEGI
# ══════════════════════════════════════════════════════════════
echo
echo "[1/3] Veritabani yedekleniyor..."

# SQLite'in ".backup" komutu "online backup API"sini kullanir: veritabani o
# anda yazilirken bile tutarli bir kopya uretir. Duz "cp" bunu garanti etmez —
# kopyalama ortasinda yazma olursa yarim islem iceren bozuk dosya cikabilir.
rm -f -- "$TMP_DB"
sqlite3 "$DB_FILE" ".backup '$TMP_DB'" \
    || hata "Veritabani yedegi alinamadi (sqlite3 .backup basarisiz)."

# Aldigimiz kopyayi hemen dogruluyoruz. Okunamayan bir yedek, yedek degildir.
# integrity_check saglamsa tek satir "ok" doner; bozuksa hata satirlarini doker.
#
# Ciktiyi bilerek DEGISKENE aliyoruz, "| grep" YAPMIYORUZ: grep -q ilk eslesmede
# kapanir, bu da sqlite3 tarafinda SIGPIPE'a yol acabilir ve "set -o pipefail"
# yuzunden saglam bir yedek hatali sanilabilir. Ayrica bozukluk halinde
# sqlite3'un yazdigi asil mesaji da boylece log'a gecirebiliyoruz.
integrity_result="$(sqlite3 "$TMP_DB" "PRAGMA integrity_check;")" \
    || hata "Yedek dogrulanamadi (PRAGMA integrity_check calistirilamadi)."

if [ "$integrity_result" != "ok" ]; then
    hata "Yedek dosyasi bozuk cikti, YAZILMADI. sqlite3 cikti: $integrity_result"
fi

mv -f -- "$TMP_DB" "$DB_OUT"
echo "      olustu: $(basename "$DB_OUT")  ($(boyut "$DB_OUT"))  [integrity_check: ok]"


# ══════════════════════════════════════════════════════════════
#  5) MEDYA YEDEGI
# ══════════════════════════════════════════════════════════════
echo
echo "[2/3] Medya klasoru arsivleniyor..."

# -c: arsiv olustur   -z: gzip ile sikistir   -f: hedef dosya
# -C "$PROJECT_DIR": tar'i once o klasore gecir, sonra "media" klasorunu al.
#     Boylece arsiv icindeki yollar "media/foto.jpg" seklinde GORELI olur.
#     -C kullanmasaydik mutlak yol gomulurdu ve geri yuklerken zorlanirdik.
rm -f -- "$TMP_MEDIA"
tar -czf "$TMP_MEDIA" -C "$PROJECT_DIR" "$MEDIA_DIR_NAME" \
    || hata "Medya arsivi olusturulamadi (tar basarisiz)."

mv -f -- "$TMP_MEDIA" "$MEDIA_OUT"
echo "      olustu: $(basename "$MEDIA_OUT")  ($(boyut "$MEDIA_OUT"))"


# ══════════════════════════════════════════════════════════════
#  6) ESKI YEDEKLERI TEMIZLE
# ══════════════════════════════════════════════════════════════
#
# BU BOLUM BETIGIN EN RISKLI KISMI. Silme kumesini daraltan her sey onemli:
#
#   "$BACKUP_DIR"        -> MUTLAK yol. Betik hangi klasorde calistirilirsa
#                           calistirilsin hep ayni yere bakar.
#   -maxdepth 1          -> alt klasorlere INMEZ.
#   -type f              -> yalnizca duz dosya. Hicbir klasor silinemez.
#   -name 'db-*.sqlite3' -> kalip TIRNAK ICINDE; joker'i kabuk degil find cozer.
#   sort                 -> isimler db-YYYY-AA-GG oldugu icin alfabetik sira
#                           kronolojik siraya esittir. En eskiler basa gelir.
#   head -n "$N"         -> bastan (en eskiden) yalnizca N tane secer.
#                           N = toplam - KEEP_COUNT. N <= 0 ise hic silinmez.
#   rm -- "$file"        -> tek tek siler. "rm -rf" YOK. "--" tire ile baslayan
#                           dosya adinin secenek sanilmasini engeller.
#
# NOT: GNU'ya ozgu "head -n -8" kullanilmadi; macOS'ta bulunmuyor ve betigin
# tasinabilir kalmasi tercih edildi.

temizle() {
    local pattern="$1"      # ornek: db-*.sqlite3
    local label="$2"        # ekrana yazilacak etiket
    local file total to_delete deleted
    local files=()

    # Dosyalari once DIZIYE okuyoruz. Iki sebepten:
    #   1. "find | sort | head" boru hattinda head erken kapanir; sort SIGPIPE
    #      alabilir ve "set -o pipefail" yuzunden basarili silme hatali sanilir.
    #   2. Boru hattindaki while dongusu ALT KABUKTA calisir; oradaki "exit 1"
    #      sadece alt kabugu kapatir. Dizi kullanarak ana kabukta kaliyoruz,
    #      boylece hata() gercekten betigi durdurabiliyor.
    # < <(...) : surec ikamesi. Dongu girdiyi sonuna kadar okur, erken kapanma yok.
    while IFS= read -r file; do
        files+=("$file")
    done < <(find "$BACKUP_DIR" -maxdepth 1 -type f -name "$pattern" | sort)

    total=${#files[@]}
    to_delete=$(( total - KEEP_COUNT ))

    if [ "$to_delete" -le 0 ]; then
        echo "      $label: $total yedek var, silinecek yok (sinir: $KEEP_COUNT)"
        return 0
    fi

    echo "      $label: $total yedek var, en eski $to_delete tanesi siliniyor"

    # Dizi sirali (sort'tan geldi) -> bastaki elemanlar EN ESKI olanlar.
    # Bastan basliyoruz, sayaci artiriyoruz, sinira gelince duruyoruz.
    #
    # NEDEN "${files[@]}" uzerinde donuyoruz da for (( i=0; i<N; i++ )) ile
    # INDEKSLEMIYORUZ: bash 3.2'de (macOS'un varsayilani) "local dizi=()" ile
    # "+=" birlikte kullanildiginda dizi 0 yerine 1'den baslar; indeksli dongu
    # ilk elemani bos okur, sonuncusunu atlar. "${files[@]}" ise elemanlari
    # indeks numarasindan bagimsiz, sirayla verir — bash 3.2'de de 5'te de dogru.
    deleted=0
    for file in "${files[@]}"; do
        if [ "$deleted" -ge "$to_delete" ]; then
            break
        fi
        rm -- "$file" || hata "Silinemedi: $file"
        echo "        silindi: $(basename "$file")"
        deleted=$(( deleted + 1 ))
    done
}

echo
echo "[3/3] Eski yedekler temizleniyor (sinir: $KEEP_COUNT)..."
temizle "db-*.sqlite3"   "veritabani"
temizle "media-*.tar.gz" "medya"


# ══════════════════════════════════════════════════════════════
#  7) OZET
# ══════════════════════════════════════════════════════════════
db_count=$(find "$BACKUP_DIR" -maxdepth 1 -type f -name "db-*.sqlite3"   | wc -l)
media_count=$(find "$BACKUP_DIR" -maxdepth 1 -type f -name "media-*.tar.gz" | wc -l)
total_size=$(du -sh "$BACKUP_DIR" | cut -f1)

echo
echo "═══════════════════════════════════════════════"
echo "Yedekleme tamamlandi — $(date '+%d.%m.%Y %H:%M %Z')"
echo "  Klasor        : $BACKUP_DIR"
echo "  Veritabani    : $db_count yedek"
echo "  Medya         : $media_count yedek"
echo "  Toplam boyut  : $total_size"
echo "═══════════════════════════════════════════════"

exit 0
