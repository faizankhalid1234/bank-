from pathlib import Path

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import FileResponse, HttpResponse, HttpResponseRedirect
from django.urls import include, path, re_path

from . import seo_views


def healthz(_request):
    return HttpResponse("ok", content_type="text/plain; charset=utf-8")


def spa_index(request):
    """Serve the React SPA (built to static/spa/)."""
    p = Path(settings.BASE_DIR) / "static" / "spa" / "index.html"
    if not p.exists():
        return HttpResponse(
            "Build the React app: cd frontend && npm install && npm run build",
            status=503,
            content_type="text/plain; charset=utf-8",
        )
    return FileResponse(p.open("rb"), content_type="text/html; charset=utf-8")


def root(request):
    """Production: Railway home → Django admin; dev: same as SPA (see RAILWAY_ROOT_TO_ADMIN)."""
    if getattr(settings, "RAILWAY_ROOT_TO_ADMIN", False):
        return HttpResponseRedirect("/admin/")
    return spa_index(request)


urlpatterns = [
    path("healthz", healthz),
    path("robots.txt", seo_views.robots_txt),
    path("sitemap.xml", seo_views.sitemap_xml),
    path("admin/", admin.site.urls),
    path("api/", include("banking.api_urls")),
    path("", root),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0]
    )

urlpatterns += [re_path(r"^.*$", spa_index)]
