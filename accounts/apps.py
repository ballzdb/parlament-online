from django.apps import AppConfig
from django.db.models.signals import post_migrate


class AccountsConfig(AppConfig):
    name = 'accounts'

    def ready(self):
        from .models import ensure_default_site_settings, seed_default_commissions

        def initialise_account_defaults(sender, **kwargs):
            seed_default_commissions()
            ensure_default_site_settings()

        post_migrate.connect(
            initialise_account_defaults,
            sender=self,
            dispatch_uid='accounts.initialise_account_defaults',
        )
