"""Lightweight SEO endpoints (robots.txt, sitemap.xml)."""

from django.conf import settings
from django.http import HttpResponse


def robots_txt(request):
    base = (getattr(settings, "SITE_CANONICAL_URL", "") or "").strip().rstrip("/")
    if not base:
        base = request.build_absolute_uri("/").split("?")[0].rstrip("/")
    lines = [
        "User-agent: *",
        "Allow: /",
        "",
        f"Sitemap: {base}/sitemap.xml",
    ]
    return HttpResponse(
        "\n".join(lines) + "\n",
        content_type="text/plain; charset=utf-8",
    )


def sitemap_xml(request):
    base = (getattr(settings, "SITE_CANONICAL_URL", "") or "").strip().rstrip("/")
    if not base:
        base = request.build_absolute_uri("/").split("?")[0].rstrip("/")
    loc = f"{base}/"
    body = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        f"<url><loc>{loc}</loc>"
        "<changefreq>weekly</changefreq>"
        "<priority>1.0</priority>"
        "</url></urlset>"
    )
    return HttpResponse(body, content_type="application/xml; charset=utf-8")
