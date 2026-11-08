from __future__ import annotations

from .models import SiteSettings, get_public_social_links


def site_settings(request):
    contact_email = SiteSettings.get_value('contact_email', '').strip()
    return {
        'social_links': get_public_social_links(),
        'contact_email': contact_email,
    }
