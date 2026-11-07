from __future__ import annotations

from django.db import models


class ModerationEntry(models.Model):
    target_type = models.CharField(max_length=40, default='idea')
    target_id = models.PositiveIntegerField(default=0)
    verdict = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f'{self.target_type}:{self.target_id}'
