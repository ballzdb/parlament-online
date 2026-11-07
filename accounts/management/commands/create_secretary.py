from __future__ import annotations

from django.core.management.base import BaseCommand

from accounts.models import User


class Command(BaseCommand):
    help = 'Create the initial secretary account.'

    def add_arguments(self, parser):
        parser.add_argument('--email', default='secretary@parlament-online.local')
        parser.add_argument('--password', default='Parlament123!')
        parser.add_argument('--name', default='Секретар')

    def handle(self, *args, **options):
        email = options['email'].strip().lower()
        password = options['password']
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'display_name': options['name'],
                'role': User.Role.SECRETARY,
                'is_active': True,
            },
        )
        if created:
            user.set_password(password)
            user.save(update_fields=['password'])
        self.stdout.write(self.style.SUCCESS(f'Secretary ready: {user.email}'))
