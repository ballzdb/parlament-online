from __future__ import annotations

from getpass import getpass

from django.core.management.base import BaseCommand, CommandError

from accounts.models import User


class Command(BaseCommand):
    help = 'Create the initial secretary account.'

    def add_arguments(self, parser):
        parser.add_argument('--email', default='secretary@parlament-online.local')
        parser.add_argument('--password')
        parser.add_argument('--name', default='Секретар')

    def handle(self, *args, **options):
        email = options['email'].strip().lower()
        existing_user = User.objects.filter(email=email).first()
        if existing_user:
            self.stdout.write(self.style.SUCCESS(f'Secretary ready: {existing_user.email}'))
            return

        password = options['password'] or getpass('New secretary password: ')
        if len(password) < 10:
            raise CommandError('Пароль секретаря має містити щонайменше 10 символів.')

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
