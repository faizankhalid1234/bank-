"""Answer /healthz before Host/session/DB middleware — Railway healthchecks stay 200."""

from django.http import HttpResponse


class RailwayHealthCheckMiddleware:
    """Must be first in MIDDLEWARE so ALLOWED_HOSTS / DB cannot break deploy health probes."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        p = request.path
        if p == "/healthz" or p == "/healthz/":
            return HttpResponse("ok", content_type="text/plain; charset=utf-8")
        return self.get_response(request)
