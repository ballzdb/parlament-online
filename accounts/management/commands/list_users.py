from __future__ import annotations

from django.core.management.base import BaseCommand

from accounts.models import User


class Command(BaseCommand):
    help = 'List users without exposing password hashes.'

    def handle(self, *args, **options):
        qs = User.objects.order_by('id')
        header = 'id | email | role | active'
        self.stdout.write(header)
        self.stdout.write('-' * len(header))
        for user in qs:
            self.stdout.write(f'{user.id} | {user.email} | {user.role} | {"yes" if user.is_active else "no"}')
