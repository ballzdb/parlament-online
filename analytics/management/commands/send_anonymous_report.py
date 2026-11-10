from __future__ import annotations

from datetime import timedelta

from django.core.management.base import BaseCommand, CommandError
from django.core.mail import send_mail
from django.utils import timezone

from analytics.models import AnonymousMetric


REPORT_RECIPIENT = 'ye74@khul.ukr.education'


class Command(BaseCommand):
    help = 'Send yesterday’s anonymous page-view totals to the designated secretary.'

    def handle(self, *args, **options):
        report_date = timezone.localdate() - timedelta(days=1)
        metrics = AnonymousMetric.objects.filter(date=report_date).order_by('section')
        lines = [f'Анонімна статистика за {report_date:%d.%m.%Y}:', '']

        if metrics.exists():
            lines.extend(
                f'{metric.get_section_display()}: {metric.page_views}'
                for metric in metrics
            )
        else:
            lines.append('За цю дату немає переглядів, на які користувачі дали згоду.')

        sent = send_mail(
            subject=f'Парламент.Online — анонімна статистика за {report_date:%d.%m.%Y}',
            message='\n'.join(lines),
            from_email=None,
            recipient_list=[REPORT_RECIPIENT],
            fail_silently=False,
        )
        if sent != 1:
            raise CommandError('Не вдалося надіслати звіт на визначену адресу.')

        self.stdout.write(self.style.SUCCESS(f'Анонімний звіт надіслано: {REPORT_RECIPIENT}'))
