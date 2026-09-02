from decimal import Decimal, ROUND_HALF_UP

from django import forms
from django.contrib import admin

from core.models import RatingCriterion
from .models import Review, ReviewScore


class ReviewScoreForm(forms.ModelForm):
    """
    Puan satirinin formu.

    criterion'u readonly_fields ile salt okunur YAPAMAYIZ: readonly alan
    hic input basmaz, yeni satirda kriter bos gider ve kayit patlar.
    Dogru arac disabled: widget pasif cizilir, gonderilen deger yok
    sayilir, Django degeri initial'dan okur.
    """

    class Meta:
        model = ReviewScore
        fields = ("criterion", "value")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        field = self.fields["criterion"]
        field.disabled = True

        # Acilir listede sadece bu satirin kendi kriteri dursun. Alan
        # zaten pasif; butun kriterleri her satirda bastan basmak hem
        # gereksiz HTML hem de pasif/kitap kriterlerini ortaligi
        # karistiracak sekilde gosteriyordu.
        secili = self.initial.get("criterion") or self.instance.criterion_id
        # Kriteri olmayan tek form, admin'in JS icin bastigi bos sablon
        # satiri (empty_form). Onun listesi de bos kalsin, yoksa pasif ve
        # kitaba ait kriterler oradan sizip goruntuye giriyor.
        field.queryset = field.queryset.filter(pk=secili) if secili else field.queryset.none()


class ReviewScoreInline(admin.TabularInline):
    model = ReviewScore
    form = ReviewScoreForm
    # extra=0: satirlari asagida kendimiz uretiyoruz, Django'nun bos
    # satir eklemesine gerek yok.
    extra = 0
    fields = ("criterion", "value")

    def get_formset(self, request, obj=None, **kwargs):
        """
        Puani henuz girilmemis kriterler icin hazir satir uretir.

        Yeni incelemede bu "tum aktif kriterler" demek; kayitli bir
        incelemede "sonradan eklenen kriterler" demek. Ikincisi olmazsa
        criterion salt okunur oldugu icin yeni bir kriteri eski filme
        girmenin yolu kalmaz.

        Admin, formset'i kurarken initial parametresi GECIRMEZ. Bu yuzden
        ciplak sinifi degil, initial'i kendi enjekte eden bir alt sinif
        donduruyoruz.
        """
        formset_class = super().get_formset(request, obj, **kwargs)

        criteria = RatingCriterion.objects.filter(for_movies=True, is_active=True)
        if obj is not None:
            criteria = criteria.exclude(reviewscore__review=obj)
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


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("title", "content_type", "release_year", "rating", "is_published", "is_featured", "is_hero", "published_at")
    list_filter = ("content_type", "is_published", "is_featured", "is_hero", "genre")
    search_fields = ("title", "director", "lead_actors", "summary")
    list_editable = ("is_published", "is_featured", "is_hero")
    prepopulated_fields = {"slug": ("title",)}
    inlines = [ReviewScoreInline]
    # rating artik alt kriterlerden hesaplaniyor, elle girilmiyor.
    readonly_fields = ("rating",)

    def save_related(self, request, form, formsets, change):
        """
        Ortalamayi alt kriter puanlarindan hesaplar.

        Bu hesap Review.save() icinde OLAMAZ: admin ana kaydi
        inline'lardan ONCE yazar (save_model -> save_related). save()
        icinde hesaplasaydik ortalama hep bir kayit geriden gelirdi —
        KB-30'da ayni tuzaga dusulmustu.
        """
        super().save_related(request, form, formsets, change)

        review = form.instance
        values = [v for v in review.scores.values_list("value", flat=True) if v is not None]

        if values:
            # round() kullanmiyoruz: bankaci yuvarlamasi yapiyor
            # (round(7.45, 1) -> 7.4). Burada yarim yukari yuvarlanmali.
            review.rating = (Decimal(sum(values)) / len(values)).quantize(
                Decimal("0.1"), rounding=ROUND_HALF_UP
            )
        else:
            review.rating = None

        review.save(update_fields=["rating"])
