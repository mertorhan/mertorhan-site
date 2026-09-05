from rest_framework import serializers

from blog.models import BlogPost, PostSection
from books.models import Book, BookQuote
from gallery.models import Photo
from movies.models import Review


class PostSectionSerializer(serializers.ModelSerializer):
    """Bir yazinin govdesini olusturan sirali bloklar.

    Sadece detay ucunda donuyor; liste ucu bloklari tasimaz.
    Siralama modeldeki Meta.ordering = ["order", "id"] ile geliyor.
    """

    class Meta:
        model = PostSection
        # Alan adlari sozlesme: mobil taraf bunlara gore yaziliyor.
        fields = [
            'order', 'kind', 'text', 'heading_level', 'in_toc',
            'image', 'image_title', 'image_caption', 'image_alt',
            'quote_source', 'embed_url',
        ]


class BlogPostSerializer(serializers.ModelSerializer):
    """Liste ucunun kayit bicimi. Bloklar (sections) burada DONMEZ."""

    # Kategori adi duz metin, kategorisiz yazida null. StringRelatedField
    # yerine bu: sozlesme Category.__str__'e bagimli kalmasin.
    category = serializers.SerializerMethodField()

    # Modeldeki @property'den okunuyor, burada yeniden hesaplanmiyor.
    reading_time = serializers.ReadOnlyField()

    class Meta:
        model = BlogPost
        fields = [
            'id', 'slug', 'title', 'summary', 'category',
            'published_at', 'reading_time', 'cover_image', 'is_featured',
        ]

    def get_category(self, obj):
        return obj.category.name if obj.category else None


class BlogPostDetailSerializer(BlogPostSerializer):
    """Detay ucu: liste alanlari + yazinin bloklari."""

    sections = PostSectionSerializer(many=True, read_only=True)

    class Meta(BlogPostSerializer.Meta):
        fields = BlogPostSerializer.Meta.fields + ['sections']


class ReviewSerializer(serializers.ModelSerializer):
    """Film/dizi listesinin kayit bicimi. Kunye iliskileri burada DONMEZ."""

    # DecimalField varsayilan olarak "8.5" seklinde METIN doner; mobil taraf
    # sayi bekliyor. coerce_to_string=False sayiya cevirir, deger yoksa null.
    rating = serializers.DecimalField(
        max_digits=3, decimal_places=1, coerce_to_string=False, read_only=True
    )

    class Meta:
        model = Review
        fields = [
            'id', 'slug', 'title', 'content_type', 'cover_image',
            'release_year', 'rating', 'summary', 'published_at',
            'watched_at', 'is_featured',
        ]


class ReviewDetailSerializer(ReviewSerializer):
    """Detay ucu: liste alanlari + govde ve kunye iliskileri.

    Dort iliski de AD LISTESI donuyor. Modeldeki eski metin alanlari
    (director, screenwriter, lead_actors, genre) BILEREK disarida:
    silinmek uzere bekliyorlar, sozlesmeye girerlerse sonradan kirici olur.

    SlugRelatedField secildi cunku dort model de tek alanli (name);
    boylece sozlesme __str__'e bagimli kalmiyor.
    """

    directors = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field='name'
    )
    screenwriters = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field='name'
    )
    actors = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field='name'
    )
    genres = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field='name'
    )

    class Meta(ReviewSerializer.Meta):
        fields = ReviewSerializer.Meta.fields + [
            'body', 'directors', 'screenwriters', 'actors', 'genres',
        ]


class BookQuoteSerializer(serializers.ModelSerializer):
    """Kitaptan secilmis alintilar.

    Sadece detay ucunda donuyor; siralama modeldeki
    Meta.ordering = ["order"] ile geliyor.
    """

    class Meta:
        model = BookQuote
        fields = ['order', 'text', 'page']


class BookSerializer(serializers.ModelSerializer):
    """Kitap listesinin kayit bicimi. Alintilar burada DONMEZ."""

    # Review'daki ile ayni gerekce: sayi donsun, deger yoksa null.
    rating = serializers.DecimalField(
        max_digits=3, decimal_places=1, coerce_to_string=False, read_only=True
    )

    class Meta:
        model = Book
        # author ve translator modelde duz CharField, iliski degil.
        fields = [
            'id', 'slug', 'title', 'author', 'translator', 'cover_image',
            'rating', 'summary', 'published_at', 'is_featured',
        ]


class BookDetailSerializer(BookSerializer):
    """Detay ucu: liste alanlari + govde ve alintilar."""

    quotes = BookQuoteSerializer(many=True, read_only=True)

    class Meta(BookSerializer.Meta):
        fields = BookSerializer.Meta.fields + ['body', 'quotes']


class PhotoSerializer(serializers.ModelSerializer):
    """Galeri fotografi.

    Photo modelinde slug YOK, bu yuzden detay ucu de yok; tum kunye
    bilgisi liste ucunda donuyor.
    """

    # Kategori adi duz metin, kategorisiz fotoda null (blog desenindeki gibi).
    category = serializers.SerializerMethodField()

    class Meta:
        model = Photo
        # thumbnail, image_width ve image_height modelde editable=False;
        # DRF bunlari salt okunur alan olarak kuruyor.
        fields = [
            'id', 'title', 'image', 'thumbnail',
            'image_width', 'image_height', 'category', 'location',
            'taken_at', 'camera', 'lens', 'iso',
            'shutter_speed', 'aperture', 'focal_length', 'order',
        ]

    def get_category(self, obj):
        return obj.category.name if obj.category else None
