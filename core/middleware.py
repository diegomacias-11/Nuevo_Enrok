from django.conf import settings
from django.http import HttpResponseRedirect
from django.urls import reverse


class LoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated or self._is_public_path(request):
            return self.get_response(request)

        return HttpResponseRedirect(settings.LOGIN_URL)

    def _is_public_path(self, request):
        resolver = getattr(request, "resolver_match", None)
        url_name = resolver.url_name if resolver else None
        path = request.path
        login_path = settings.LOGIN_URL
        logout_path = reverse("logout")

        return (
            url_name in {"login", "logout"}
            or path == login_path
            or path == logout_path
            or path.startswith(settings.STATIC_URL)
            or path.startswith("/admin/")
        )
