from __future__ import annotations

from django.core.management.base import BaseCommand

from accounts.models import Commission, User
from ideas.models import Idea


class Command(BaseCommand):
    help = 'Create a small demo dataset.'

    def handle(self, *args, **options):
        self.stdout.write('Creating demo data...')
        commission = Commission.objects.first() or Commission.objects.create(
            name='Навчання', slug='navchannia', description='Demo commission.'
        )
        student, _ = User.objects.get_or_create(
            email='student@example.com',
            defaults={'display_name': 'Студент', 'role': User.Role.STUDENT, 'is_active': True},
        )
        if not student.has_usable_password():
            student.set_password('student123')
            student.save(update_fields=['password'])
        Idea.objects.get_or_create(
            title='Відкрити форум для учнів',
            defaults={
                'body': 'Запропоновано провести онлайн-форум для обговорення навчальних питань.',
                'author': student,
                'commission': commission,
                'status': Idea.Status.SUBMITTED,
            },
        )
        self.stdout.write(self.style.SUCCESS('Demo data ready.'))
