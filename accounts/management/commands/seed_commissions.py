from __future__ import annotations

from django.core.management.base import BaseCommand

from accounts.models import seed_default_commissions


class Command(BaseCommand):
    help = 'Seed the default commissions for the parliament.'

    def handle(self, *args, **options):
        seed_default_commissions()
        self.stdout.write(self.style.SUCCESS('Commissions seeded successfully.'))
