from __future__ import annotations

from django.core.management.base import BaseCommand

from accounts.models import Commission


class Command(BaseCommand):
    help = 'Seed the default commissions for the parliament.'

    def handle(self, *args, **options):
        defaults = [
            ('Навчання', 'navchannia', 'Навчальна та освітня робота.'),
            ('Порядок', 'poryadok', 'Порядок, дисципліна та життя школи.'),
            ('Дозвілля', 'dozvillia', 'Масові заходи та дозвілля.'),
        ]
        created_count = 0
        for name, slug, description in defaults:
            commission, created = Commission.objects.get_or_create(
                slug=slug,
                defaults={'name': name, 'description': description, 'sort_order': created_count},
            )
            if created:
                created_count += 1
            if commission.name != name:
                commission.name = name
                commission.description = description
                commission.save(update_fields=['name', 'description'])
        self.stdout.write(self.style.SUCCESS('Commissions seeded successfully.'))
