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


class PageView(models.Model):
    path = models.CharField(max_length=255, db_index=True)
    visitor_key = models.CharField(max_length=64, db_index=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='page_views',
    )
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [models.Index(fields=['timestamp', 'path'], name='analytics_p_timepat_7a7e3b_idx')]

    def __str__(self) -> str:
        return f'{self.path} @ {self.timestamp:%Y-%m-%d %H:%M}'
