from django.apps import AppConfig


class AccountsConfig(AppConfig):
    name = 'accounts'

    def ready(self):
        from .models import ensure_default_site_settings, seed_default_commissions
        seed_default_commissions()
        ensure_default_site_settings()
