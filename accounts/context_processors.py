from __future__ import annotations

from .models import SITE_SETTINGS_DEFAULTS, SiteSettings, validate_site_url


INSTITUTION_LINKS = {
    'school_site_url': 'Сайт ліцею',
    'parliament_site_url': 'Парламент на сайті ліцею',
    'self_governance_url': 'Самоврядування ліцею',
    'school_contacts_url': 'Контакти ліцею',
}

SOCIAL_LINKS = {
    'instagram_url': 'Instagram',
    'telegram_url': 'Telegram',
    'facebook_url': 'Facebook',
    'tiktok_url': 'TikTok',
    'youtube_url': 'YouTube',
    'discord_url': 'Discord',
}


def site_settings(request):
    keys = (*SITE_SETTINGS_DEFAULTS.keys(), 'contact_email')
    stored = dict(
        SiteSettings.objects.filter(key__in=keys).values_list('key', 'value')
    )
    values = {**SITE_SETTINGS_DEFAULTS, **stored}

    institution_links = [
        {'key': key, 'label': label, 'url': values[key].strip()}
        for key, label in INSTITUTION_LINKS.items()
        if validate_site_url(values.get(key, '').strip())
    ]
    social_links = [
        {'key': key, 'label': label, 'url': values[key].strip()}
        for key, label in SOCIAL_LINKS.items()
        if validate_site_url(values.get(key, '').strip())
    ]

    return {
        'institution_links': institution_links,
        'social_links': social_links,
        'contact_email': values.get('contact_email', '').strip(),
    }
