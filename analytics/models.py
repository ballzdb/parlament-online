from __future__ import annotations

from django.conf import settings
from django.db import models


class EventLog(models.Model):
    action = models.CharField(max_length=80)
    related_object = models.CharField(max_length=120, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self) -> str:
        return f'{self.user or "anon"}: {self.action}'


class AnonymousMetric(models.Model):
    class Section(models.TextChoices):
        HOME = 'home', 'Головна'
        IDEAS = 'ideas', 'Ідеї'
        DECISIONS = 'decisions', 'Рішення'
        APPEALS = 'appeals', 'Звернення'
        SUPPORT = 'support', 'Підтримка'
        KANBAN = 'kanban', 'Комісії'
        ANALYTICS = 'analytics', 'Аналітика'
        OTHER = 'other', 'Інше'

    date = models.DateField()
    section = models.CharField(max_length=20, choices=Section.choices)
    page_views = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['date', 'section']
        constraints = [
            models.UniqueConstraint(fields=['date', 'section'], name='unique_anonymous_metric_per_day_section'),
        ]

    def __str__(self) -> str:
        return f'{self.date}: {self.section} ({self.page_views})'
