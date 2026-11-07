from __future__ import annotations

from functools import wraps

from django.core.exceptions import PermissionDenied


def requires_roles(*roles):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            user = request.user
            if not user.is_authenticated:
                raise PermissionDenied
            if roles and not user.has_role(*roles):
                raise PermissionDenied
            return view_func(request, *args, **kwargs)

        return _wrapped_view

    return decorator


class RoleRequiredMixin:
    required_roles = ()

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            raise PermissionDenied
        if self.required_roles and not request.user.has_role(*self.required_roles):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)
