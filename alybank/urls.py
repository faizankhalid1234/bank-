from pathlib import Path

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import FileResponse, HttpResponse
from django.urls import include, path, re_path


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


urlpatterns = [
    path("healthz", healthz),
    path("admin/", admin.site.urls),
    path("api/", include("banking.api_urls")),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0]
    )

urlpatterns += [re_path(r"^.*$", spa_index)]
