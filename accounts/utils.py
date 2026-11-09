from __future__ import annotations

from django.conf import settings


def normalize_email(value: str | None) -> str:
    return (value or '').strip().lower()


def is_allowed_email(email: str) -> bool:
    value = normalize_email(email)
    if not value or value.count('@') != 1:
        return False
    local, domain = value.split('@', 1)
    if not local or not domain:
        return False
    if domain != settings.ALLOWED_EMAIL_DOMAIN.strip().lower():
        return False
    return True