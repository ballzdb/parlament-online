from django.apps import AppConfig
from django.db.models import Q
from django.db.models.signals import post_migrate


class AccountsConfig(AppConfig):
    name = 'accounts'

    def ready(self):
        from .models import (
            PRIMARY_ADMIN_EMAIL,
            User,
            ensure_default_site_settings,
            seed_default_commissions,
        )

        def initialise_account_defaults(sender, **kwargs):
            seed_default_commissions()
            ensure_default_site_settings()
            User.objects.exclude(email__iexact=PRIMARY_ADMIN_EMAIL).filter(
                Q(is_staff=True) | Q(is_superuser=True)
            ).update(is_staff=False, is_superuser=False)
            User.objects.filter(email__iexact=PRIMARY_ADMIN_EMAIL).update(
                is_active=True,
                is_staff=True,
                is_superuser=True,
                role=User.Role.SECRETARY,
            )

        post_migrate.connect(
            initialise_account_defaults,
            sender=self,
            dispatch_uid='accounts.initialise_account_defaults',
        )
