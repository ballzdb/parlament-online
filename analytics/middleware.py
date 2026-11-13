from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied

from accounts.models import User


class AnalyticsAccessMiddleware:
    protected_paths = frozenset({
        '/analytics/',
        '/analytics/export.csv',
        '/analytics/classes/',
    })

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path in self.protected_paths:
            if not request.user.is_authenticated:
                return redirect_to_login(request.get_full_path())
            if not request.user.has_role(User.Role.MEMBER, User.Role.SECRETARY):
                raise PermissionDenied

        return self.get_response(request)
