from django.conf import settings


def bank_branding(request):
    base = (getattr(settings, "SITE_CANONICAL_URL", "") or "").strip().rstrip("/")
    if not base:
        base = request.build_absolute_uri("/").split("?")[0].rstrip("/")
    path = request.get_full_path()
    if "?" in path:
        path = path.split("?")[0]
    canonical_url = base + path if path.startswith("/") else f"{base}/{path}"
    og_image = (getattr(settings, "SEO_OG_IMAGE_URL", "") or "").strip()
    return {
        "BANK_NAME": "AlyBank",
        "BANK_TAGLINE": "Banking that feels effortless",
        "SITE_CANONICAL_BASE": base,
        "canonical_url": canonical_url,
        "SEO_DEFAULT_DESCRIPTION": getattr(settings, "SEO_DEFAULT_DESCRIPTION", ""),
        "SEO_OG_IMAGE_URL": og_image,
    }
