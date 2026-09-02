"""
core/rating_admin.py
Alt kriterli puanlamanin admin tarafi. Film & Dizi (movies) ve Kitap
(books) ayni davranisi paylasiyor; kod burada tek nusha duruyor.

Uc parca var:
  BaseScoreForm      puan satirinin formu (kriter pasif gorunur)
  BaseScoreInline    eksik kriterler icin hazir satir uretir
  ScoreAverageMixin  ortalamayi inline'lardan SONRA hesaplar
"""

from decimal import Decimal, ROUND_HALF_UP

from django import forms
from django.contrib import admin

from .models import RatingCriterion


class BaseScoreForm(forms.ModelForm):
    """
    Puan satirinin formu.

    criterion'u readonly_fields ile salt okunur YAPAMAYIZ: readonly alan
    hic input basmaz, yeni satirda kriter bos gider ve kayit patlar.
    Dogru arac disabled: widget pasif cizilir, gonderilen deger yok
    sayilir, Django degeri initial'dan okur.

    Meta YOK: inline, modelform_factory(model, form=..., fields=...) ile
    modeli ve alanlari kendisi veriyor. Boylece bu form hem ReviewScore
    hem BookScore icin calisiyor — criterion alan adi ikisinde de ayni.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        field = self.fields["criterion"]
        field.disabled = True

        # Acilir listede sadece bu satirin kendi kriteri dursun. Alan
        # zaten pasif; butun kriterleri her satirda bastan basmak hem
        # gereksiz HTML hem de pasif/kitaba ait kriterleri ortaligi
        # karistiracak sekilde gosteriyordu.
        secili = self.initial.get("criterion") or self.instance.criterion_id
        # Kriteri olmayan tek form, admin'in JS icin bastigi bos sablon
        # satiri (empty_form). Onun listesi de bos kalsin, yoksa pasif ve
        # baska ture ait kriterler oradan sizip goruntuye giriyor.
        field.queryset = field.queryset.filter(pk=secili) if secili else field.queryset.none()


class BaseScoreInline(admin.TabularInline):
    """
    Puan satirlari icin ortak inline.

    Alt sinif uc seyi soylemek zorunda:
      model           ReviewScore / BookScore
      criterion_flag  hangi kriterler bu turde kullanilir
      score_lookup    puan satirindan ana kayda giden ters iliski

    Ayrica ANA MODEL, puan satirlarini related_name="scores" ile tutmak
    zorunda: get_formset icindeki mevcut satir sayimi (obj.scores.count())
    bu ada bagli. Ucuncu bir icerik turu eklenip baska bir related_name
    verilirse hata ScoreAverageMixin'e gelmeden burada AttributeError
    olarak patlar — o yuzden sart iki sinifin belgesinde de yaziyor.
    """

    form = BaseScoreForm
    # extra=0: satirlari asagida kendimiz uretiyoruz, Django'nun bos
    # satir eklemesine gerek yok.
    extra = 0
    fields = ("criterion", "value")

    criterion_flag = None   # ornek: "for_movies"
    score_lookup = None     # ornek: "reviewscore__review"

    def get_formset(self, request, obj=None, **kwargs):
        """
        Puani henuz girilmemis kriterler icin hazir satir uretir.

        Yeni kayitta bu "tum aktif kriterler" demek; kayitli bir icerikte
        "sonradan eklenen kriterler" demek. Ikincisi olmazsa criterion
        salt okunur oldugu icin yeni bir kriteri eski kayda girmenin yolu
        kalmaz.

        Admin, formset'i kurarken initial parametresi GECIRMEZ. Bu yuzden
        ciplak sinifi degil, initial'i kendi enjekte eden bir alt sinif
        donduruyoruz.
        """
        formset_class = super().get_formset(request, obj, **kwargs)

        criteria = RatingCriterion.objects.filter(**{self.criterion_flag: True}, is_active=True)
        if obj is not None:
            criteria = criteria.exclude(**{self.score_lookup: obj})
        initial = [{"criterion": criterion.pk} for criterion in criteria]

        mevcut = obj.scores.count() if obj is not None else 0

        class PrefilledFormSet(formset_class):
            extra = len(initial)
            # Satirlari kriter listesi belirliyor; elle satir eklemenin
            # karsiligi yok (kriter secilemiyor). max_num'i dolu satir
            # sayisina esitleyince admin "Baska bir tane ekle" bagini
            # gizliyor.
            max_num = mevcut + len(initial)

            def __init__(self, *args, **inner_kwargs):
                inner_kwargs["initial"] = initial
                super().__init__(*args, **inner_kwargs)

        return PrefilledFormSet


class ScoreAverageMixin:
    """
    Ortalamayi alt kriter puanlarindan hesaplayan ModelAdmin karisimi.
    Ana modelde "rating" alani ve puan satirlarinda related_name="scores"
    bekler; ikisi de saglandigi icin bu kod hic parametrelenmiyor.
    """

    def save_related(self, request, form, formsets, change):
        """
        Bu hesap modelin save() metodu icinde OLAMAZ: admin ana kaydi
        inline'lardan ONCE yazar (save_model -> save_related). save()
        icinde hesaplasaydik ortalama hep bir kayit geriden gelirdi —
        KB-30'da ayni tuzaga dusulmustu.
        """
        super().save_related(request, form, formsets, change)

        nesne = form.instance
        values = [v for v in nesne.scores.values_list("value", flat=True) if v is not None]

        if values:
            # round() kullanmiyoruz: bankaci yuvarlamasi yapiyor, yani
            # yarimi en yakin CIFT sayiya cekiyor — round(2.5) -> 2,
            # round(0.5) -> 0. Ondalikta ise sonuc float'in ikili
            # gosterimine kaliyor: round(7.45, 1) yukari gidip 7.5
            # veriyor cunku 7.45 ikilide tam yarim degil. Sorun "yanlis
            # yone yuvarlamasi" degil, hangi yone gidecegini kodun
            # soylememesi. Burada kural acik olmali: yarim yukari.
            nesne.rating = (Decimal(sum(values)) / len(values)).quantize(
                Decimal("0.1"), rounding=ROUND_HALF_UP
            )
        else:
            nesne.rating = None

        nesne.save(update_fields=["rating"])
