from __future__ import annotations

from django.core.management.base import BaseCommand

from accounts.views import send_queued_emails


class Command(BaseCommand):
    help = 'Send queued email messages with retry backoff.'

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=25)

    def handle(self, *args, **options):
        sent = send_queued_emails(limit=options['limit'])
        self.stdout.write(self.style.SUCCESS(f'Sent {sent} queued email(s).'))
