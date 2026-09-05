from rest_framework import serializers

from blog.models import BlogPost, PostSection


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
