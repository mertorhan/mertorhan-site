"""
core/templatetags/experience_extras.py
Deneyim açıklamasını "alt başlık + madde listesi"ne çeviren
ve kimlik çiplerini bölen küçük şablon yardımcıları.
"""

import re

from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe

register = template.Library()

# Madde işaretleri (birini kullanman yeterli)
BULLET_PREFIXES = ("- ", "– ", "— ", "• ", "* ")


def _is_bullet(line):
    return line.lstrip().startswith(BULLET_PREFIXES)


def _strip_bullet(line):
    s = line.strip()
    for prefix in BULLET_PREFIXES:
        if s.startswith(prefix):
            return s[len(prefix):].strip()
    return s


@register.filter
def experience_body(value):
    """Düz metni alt başlık + madde listesi HTML'ine çevirir."""
    if not value:
        return ""

    text = value.replace("\r\n", "\n").replace("\r", "\n")
    blocks = re.split(r"\n\s*\n", text)  # boş satır -> yeni grup

    parts = []
    for block in blocks:
        lines = [ln for ln in block.split("\n") if ln.strip()]
        if not lines:
            continue

        heads = [ln.strip() for ln in lines if not _is_bullet(ln)]
        bullets = [_strip_bullet(ln) for ln in lines if _is_bullet(ln)]

        if bullets:
            for h in heads:
                parts.append('<p class="exp-subhead">%s</p>' % escape(h))
            parts.append('<ul class="exp-bullets">')
            for b in bullets:
                parts.append("<li>%s</li>" % escape(b))
            parts.append("</ul>")
        else:
            for h in heads:
                parts.append('<p class="exp-text">%s</p>' % escape(h))

    return mark_safe("\n".join(parts))


@register.filter
def split_chips(value):
    """'A · B · C' -> ['A', 'B', 'C']"""
    if not value:
        return []
    return [part.strip() for part in value.split("·") if part.strip()]