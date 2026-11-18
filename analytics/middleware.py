from __future__ import annotations

import uuid

from django.conf import settings
from django.db import DatabaseError

from .models import PageView


class PageViewMiddleware:
    """Record successful HTML visits without storing IP addresses or user agents."""

    EXCLUDED_PREFIXES = ('/static/', '/media/', '/admin/', '/analytics/')

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if (
            request.method != 'GET'
            or response.status_code >= 400
            or any(request.path.startswith(prefix) for prefix in self.EXCLUDED_PREFIXES)
            or request.path in ('/favicon.ico', '/robots.txt')
            or 'text/html' not in response.get('Content-Type', '')
        ):
            return response

        visitor_key = request.COOKIES.get('site_visitor')
        new_visitor = not visitor_key or len(visitor_key) > 64
        if new_visitor:
            visitor_key = uuid.uuid4().hex

        try:
            PageView.objects.create(
                path=request.path[:255],
                visitor_key=visitor_key,
                user=request.user if getattr(request, 'user', None) and request.user.is_authenticated else None,
            )
        except DatabaseError:
            # Analytics must never make the website unavailable.
            return response

        if new_visitor:
            response.set_cookie(
                'site_visitor',
                visitor_key,
                max_age=60 * 60 * 24 * 365,
                httponly=True,
                secure=not settings.DEBUG,
                samesite='Lax',
            )
        return response
