from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError

from accounts.models import AuditLog, User


class Command(BaseCommand):
    help = 'Set a user role and log the action.'

    def add_arguments(self, parser):
        parser.add_argument('--email', required=True)
        parser.add_argument('--role', required=True, choices=[choice.value for choice in User.Role])

    def handle(self, *args, **options):
        email = (options['email'] or '').strip().lower()
        role = options['role']
        user = User.objects.filter(email__iexact=email).first()
        if not user:
            raise CommandError(f'Користувача з поштою {email} не знайдено.')

        previous_role = user.role
        user.role = role
        user.additional_roles = []
        user.is_staff = role == User.Role.SECRETARY
        user.save(update_fields=['role', 'additional_roles', 'is_staff'])

        AuditLog.objects.create(
            action='role_changed',
            email=user.email,
            user=user,
            details=f'{previous_role} -> {role}',
        )
        self.stdout.write(self.style.SUCCESS(f'Роль користувача {user.email} змінено: {previous_role} -> {role}'))
