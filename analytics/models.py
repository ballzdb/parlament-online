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
