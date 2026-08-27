"""
blog/templatetags/blog_extras.py
Blok metinlerini (paragraf ve alinti) markdown olarak isleyen
sablon yardimcisi.
"""

from django import template
from django.utils.safestring import mark_safe
from markdown_it import MarkdownIt

register = template.Library()

# Tek nesne, modul seviyesinde: bir sayfada 20 blok varsa
# ayristirici 20 kez kurulmasin.
#
# "default" preset -> html secenegi False gelir, yani metindeki ham HTML
# calistirilmaz, kacislanir. Guvenlik varsayilan olarak saglanir.
#
# breaks=True -> bugunku |linebreaks davranisi korunur. Markdown normalde
# tek satir sonunu bosluk sayar; siir/dize alt alta yazilamaz hale gelirdi.
#
# Kapatilan kurallar:
#   heading, lheading -> "## baslik" paragraf icinden baslik uretirdi. Baslik
#                        ayri bir blok tipi; markdown'dan cikan baslik in_toc
#                        bilgisi tasiyamaz, KB-26'yi bozar.
#   image             -> gorsel ayri blok tipi; markdown gorseli kucultme
#                        mantigini (BLOG_IMAGE_LONG_EDGE) komple atlar.
#   code, fence       -> girintili metin yanlislikla kod kutusuna donusmesin.
#   hr, blockquote,
#   table, reference  -> bu turun kapsaminda degil, sessizce devreye girmesinler.
_MD = MarkdownIt("default", {"breaks": True}).disable([
    "heading", "lheading", "image", "code",
    "fence", "hr", "blockquote", "table", "reference",
])


@register.filter
def markdown(value):
    """Blok metnini markdown olarak isler (kalin, italik, liste, baglanti)."""
    if not value:
        return ""

    # mark_safe burada guvenli: MarkdownIt ham HTML uretmiyor, kacisliyor.
    # Django'nun korumasini kapatiyoruz ama kapatilan yerde tehlikeli etiket
    # zaten olusmuyor.
    return mark_safe(_MD.render(value))
